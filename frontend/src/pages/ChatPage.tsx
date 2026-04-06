import { useEffect, useRef, useState } from "react";

import { AvatarPanel }        from "../components/chat/AvatarPanel";
import { CBTCard }             from "../components/chat/CBTCard";
import { Composer }            from "../components/chat/Composer";
import { ConversationPanel }   from "../components/chat/ConversationPanel";
import { CrisisOverlay }       from "../components/chat/CrisisOverlay";
import { VoiceOrb }            from "../components/chat/VoiceOrb";
import { PageHeader }          from "../components/shared/PageHeader";
import { avatarSpeak, getConversationHistory, sendChatMessage } from "../lib/api";
import { useAuth }             from "../lib/auth";
import type { ConversationEntry } from "../types";

// ── Web Audio API: play alert tone via OscillatorNode (no network request)
function playAlertTone(type: "crisis" | "velocity" = "crisis") {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    if (type === "crisis") {
      // 220 Hz → 180 Hz descending tone, 0.6s — signals urgency
      osc.frequency.setValueAtTime(220, ctx.currentTime);
      osc.frequency.linearRampToValueAtTime(180, ctx.currentTime + 0.6);
      gain.gain.setValueAtTime(0.18, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.6);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.6);
    } else {
      // Velocity pre-alert: 440 Hz soft blip, 0.25s
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.25);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.25);
    }

    osc.onended = () => { ctx.close().catch(() => {}); };
  } catch {
    // AudioContext unavailable — silent fallback
  }
}

export function ChatPage() {
  const { token, user }                             = useAuth();
  const [entries, setEntries]                       = useState<ConversationEntry[]>([]);
  const [draft, setDraft]                           = useState("");
  const [status, setStatus]                         = useState("");
  const [isSending, setIsSending]                   = useState(false);
  const [languageCode, setLanguageCode]             = useState(user?.preferredLanguage ?? "en");
  const [crisisTier, setCrisisTier]                 = useState<"active" | "passive" | null>(null);
  const [showCrisisOverlay, setShowCrisisOverlay]   = useState(false);
  const [mhiDropAlert, setMhiDropAlert]             = useState(false);
  const [velocityAlert, setVelocityAlert]           = useState(false);
  const [activeCBT, setActiveCBT]                   = useState<string | null>(null);
  const [avatarAudioUrl, setAvatarAudioUrl]         = useState<string | null>(null);
  const [whisperConfidence, setWhisperConfidence]   = useState<number | undefined>(undefined);
  const [avatarSpeaking, setAvatarSpeaking]         = useState(false);
  const [avatarDuration, setAvatarDuration]         = useState(2000);
  const prevMhiRef                                  = useRef<number | null>(null);
  const statusTimer                                 = useRef<ReturnType<typeof setTimeout> | null>(null);

  const avatarId = user?.avatarId ?? "therapist";

  useEffect(() => {
    if (!token) return;
    void getConversationHistory(token).then(setEntries);
  }, [token]);

  // Auto-clear status after 4 s
  useEffect(() => {
    if (!status) return;
    if (statusTimer.current) clearTimeout(statusTimer.current);
    statusTimer.current = setTimeout(() => setStatus(""), 4000);
    return () => { if (statusTimer.current) clearTimeout(statusTimer.current); };
  }, [status]);

  // VoiceOrb → appends transcript to draft + records confidence + updates active language
  function handleTranscript(text: string, confidence?: number, detectedLangCode?: string) {
    setDraft((prev) => {
      const trimmed = prev.trimEnd();
      return trimmed ? `${trimmed} ${text}` : text;
    });
    if (confidence !== undefined) setWhisperConfidence(confidence);
    if (detectedLangCode) setLanguageCode(detectedLangCode);
  }

  // Speak assistant response via avatar
  async function speakResponse(text: string, tier: string, emotion: string) {
    if (!token) return;
    try {
      const { audioUrl, durationMs } = await avatarSpeak(
        token, text, languageCode, avatarId, emotion, tier,
      );
      setAvatarAudioUrl(audioUrl);
      setAvatarDuration(durationMs);
      setAvatarSpeaking(true);
    } catch {
      // Non-fatal — voice is optional
    }
  }

  const suggestions = [
    "I am feeling overwhelmed today",
    "Help me slow down for a minute",
    "I want to reflect on what triggered me",
  ];

  async function handleSend() {
    if (!token || !draft.trim() || isSending) return;

    const text      = draft.trim();
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    setIsSending(true);
    setStatus("Analyzing message…");
    setDraft("");

    setEntries((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", content: text, timestamp },
    ]);

    try {
      const result = await sendChatMessage(token, text, languageCode);

      // Update language from response (server may override)
      if (result.crisis_tier) setCrisisTier(null); // reset before check

      // MHI drop alert: if drops > 15 points
      if (prevMhiRef.current !== null && prevMhiRef.current - result.mhi > 15) {
        setMhiDropAlert(true);
        setTimeout(() => setMhiDropAlert(false), 6000);
      }
      prevMhiRef.current = result.mhi;

      // Crisis overlay + alert tone
      if (result.crisis_tier === "active" || result.crisis_tier === "passive") {
        setCrisisTier(result.crisis_tier as "active" | "passive");
        setShowCrisisOverlay(true);
        playAlertTone("crisis");
      }

      // Velocity pre-alert: escalating distress across turns
      if (result.pre_voice_alert && result.crisis_tier === "none") {
        setVelocityAlert(true);
        setTimeout(() => setVelocityAlert(false), 5000);
        playAlertTone("velocity");
      }

      const assistantEntry: ConversationEntry = {
        id:                    `assistant-${Date.now()}`,
        role:                  "assistant",
        content:               result.response,
        timestamp,
        mhi:                   result.mhi,
        category:              result.category,
        crisisTier:            result.crisis_tier,
        cbtTechniqueSuggested: result.cbt_technique_suggested ?? undefined,
      };

      setEntries((prev) => [...prev, assistantEntry]);
      setStatus("Response received.");

      // Trigger avatar speech
      const topEmotion = Object.entries(result.emotion_scores)
        .sort(([, a], [, b]) => b - a)[0]?.[0] ?? "default";
      void speakResponse(result.response, result.crisis_tier, topEmotion);

    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Chat request failed.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Crisis full-screen overlay */}
      {showCrisisOverlay && crisisTier === "active" && (
        <CrisisOverlay
          crisisTier="active"
          onDismiss={() => setShowCrisisOverlay(false)}
        />
      )}

      <PageHeader
        eyebrow="Chat"
        title="A calm conversation space for reflection and gentle support"
        description="Speak or type — the assistant listens in any language and responds with care."
      />

      {/* Passive crisis persistent banner */}
      {crisisTier === "passive" && (
        <CrisisOverlay crisisTier="passive" onDismiss={() => setCrisisTier(null)} />
      )}

      {/* Velocity pre-alert: escalating distress */}
      {velocityAlert && (
        <div
          className="rounded-[14px] px-4 py-3 text-[13px] text-center"
          style={{
            background: "rgba(255,123,112,0.06)",
            border: "1px solid rgba(255,123,112,0.18)",
            color: "#ff7b70",
            animation: "fadeIn 0.3s ease forwards",
          }}
        >
          Your distress seems to be building. I'm paying close attention — take your time.
        </div>
      )}

      {/* MHI drop in-chat alert */}
      {mhiDropAlert && (
        <div
          className="rounded-[14px] px-4 py-3 text-[13px] text-center animate-pulse"
          style={{
            background: "rgba(255,201,107,0.07)",
            border: "1px solid rgba(255,201,107,0.2)",
            color: "#ffc96b",
          }}
        >
          I noticed things seem heavier right now. I&apos;m here with you.
        </div>
      )}

      {/* Main grid: Avatar (40%) | Conversation (60%) */}
      <div className="grid gap-4 lg:grid-cols-[2fr_3fr]">
        {/* Left: Avatar panel */}
        <div className="flex flex-col gap-4">
          <AvatarPanel
            avatarId={avatarId}
            speakAudioUrl={avatarAudioUrl}
            speakDurationMs={avatarDuration}
            isSpeaking={avatarSpeaking}
            isListening={isSending}
            onSpeakEnd={() => setAvatarSpeaking(false)}
            crisisTier={crisisTier}
          />
          {/* Voice orb below avatar on desktop */}
          <VoiceOrb
            token={token}
            onTranscript={handleTranscript}
            disabled={isSending}
            preferredLanguage={languageCode}
          />
        </div>

        {/* Right: Conversation */}
        <ConversationPanel
          entries={entries}
          onOpenCBT={setActiveCBT}
          languageCode={languageCode}
          whisperConfidence={whisperConfidence}
        />
      </div>

      {/* Active CBT panel card */}
      {activeCBT && (
        <div
          className="rounded-[20px] p-4"
          style={{
            background: "rgba(108,227,207,0.05)",
            border: "1px solid rgba(108,227,207,0.15)",
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <p className="text-[13px] font-semibold text-[#6ce3cf]">
              Self-Help Exercise
            </p>
            <button
              type="button"
              onClick={() => setActiveCBT(null)}
              className="text-[11px] text-slate-500 hover:text-white transition-colors"
            >
              Close
            </button>
          </div>
          <CBTCard technique={activeCBT} onOpen={() => {}} />
          <p className="mt-3 text-[12px] text-slate-500">
            Full interactive CBT exercises are available in the Self-Help Tools tab.
          </p>
        </div>
      )}

      {/* Composer */}
      <Composer
        value={draft}
        disabled={isSending}
        suggestions={suggestions}
        onChange={setDraft}
        onSuggestionPick={setDraft}
        onSubmit={() => void handleSend()}
      />

      {/* Status bar */}
      {status && (
        <div
          className="rounded-[12px] px-4 py-3 text-[13px] text-center transition-all duration-300"
          style={{
            background: isSending ? "rgba(108,227,207,0.06)" : "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.06)",
            color: status.toLowerCase().includes("fail") || status.toLowerCase().includes("error")
              ? "#ff7b70"
              : "#94a3b8",
          }}
        >
          {isSending && (
            <span className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-[#6ce3cf]/20 border-t-[#6ce3cf]" />
          )}
          {status}
        </div>
      )}

      {/* Hidden language state setter — used by VoiceOrb when server returns a language */}
      <input type="hidden" value={languageCode} onChange={(e) => setLanguageCode(e.target.value)} />
    </div>
  );
}
