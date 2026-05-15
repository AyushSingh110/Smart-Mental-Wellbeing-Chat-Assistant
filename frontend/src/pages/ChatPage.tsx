import { useEffect, useRef, useState } from "react";
import { AlertCircle, AlertTriangle } from "lucide-react";

import { AvatarPanel }      from "../components/chat/AvatarPanel";
import { CBTCard }           from "../components/chat/CBTCard";
import { Composer }          from "../components/chat/Composer";
import { ConversationPanel } from "../components/chat/ConversationPanel";
import { CrisisOverlay }     from "../components/chat/CrisisOverlay";
import { VoiceOrb }          from "../components/chat/VoiceOrb";
import { avatarSpeak, getConversationHistory, sendChatMessage } from "../lib/api";
import { useAuth }           from "../lib/auth";
import type { ConversationEntry } from "../types";

function playAlertTone(type: "crisis" | "velocity" = "crisis") {
  try {
    const ctx  = new AudioContext();
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    if (type === "crisis") {
      osc.frequency.setValueAtTime(220, ctx.currentTime);
      osc.frequency.linearRampToValueAtTime(180, ctx.currentTime + 0.6);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.6);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.6);
    } else {
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      gain.gain.setValueAtTime(0.07, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.25);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.25);
    }

    osc.onended = () => { ctx.close().catch(() => {}); };
  } catch {
    // AudioContext unavailable
  }
}

export function ChatPage() {
  const { token, user }                           = useAuth();
  const [entries, setEntries]                     = useState<ConversationEntry[]>([]);
  const [draft, setDraft]                         = useState("");
  const [status, setStatus]                       = useState("");
  const [isSending, setIsSending]                 = useState(false);
  const [languageCode, setLanguageCode]           = useState(user?.preferredLanguage ?? "en");
  const [crisisTier, setCrisisTier]               = useState<"active" | "passive" | null>(null);
  const [showCrisisOverlay, setShowCrisisOverlay] = useState(false);
  const [mhiDropAlert, setMhiDropAlert]           = useState(false);
  const [velocityAlert, setVelocityAlert]         = useState(false);
  const [activeCBT, setActiveCBT]                 = useState<string | null>(null);
  const [avatarAudioUrl, setAvatarAudioUrl]       = useState<string | null>(null);
  const [whisperConfidence, setWhisperConfidence] = useState<number | undefined>(undefined);
  const [avatarSpeaking, setAvatarSpeaking]       = useState(false);
  const [avatarDuration, setAvatarDuration]       = useState(2000);
  const prevMhiRef                                = useRef<number | null>(null);
  const statusTimer                               = useRef<ReturnType<typeof setTimeout> | null>(null);

  const avatarId = user?.avatarId ?? "therapist";

  useEffect(() => {
    if (!token) return;
    void getConversationHistory(token).then(setEntries);
  }, [token]);

  useEffect(() => {
    if (!status) return;
    if (statusTimer.current) clearTimeout(statusTimer.current);
    statusTimer.current = setTimeout(() => setStatus(""), 4000);
    return () => { if (statusTimer.current) clearTimeout(statusTimer.current); };
  }, [status]);

  async function speakResponse(text: string, tier: string, emotion: string, langCode: string) {
    if (!token) return;
    try {
      const { audioUrl, durationMs } = await avatarSpeak(token, text, langCode, avatarId, emotion, tier);
      setAvatarAudioUrl(audioUrl);
      setAvatarDuration(durationMs);
      setAvatarSpeaking(true);
    } catch {
      // voice is optional, non-fatal
    }
  }

  async function submitMessage(
    text: string,
    langCode: string,
    source: "text" | "voice" = "text",
  ) {
    if (!token || !text.trim() || isSending) return;

    const trimmed   = text.trim();
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    setIsSending(true);
    setStatus(source === "voice" ? "Transcribed — analyzing…" : "Analyzing message…");

    setEntries((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", content: trimmed, timestamp },
    ]);

    try {
      const result = await sendChatMessage(token, trimmed, langCode, source);

      if (result.crisis_tier) setCrisisTier(null);

      if (prevMhiRef.current !== null && prevMhiRef.current - result.mhi > 15) {
        setMhiDropAlert(true);
        setTimeout(() => setMhiDropAlert(false), 6000);
      }
      prevMhiRef.current = result.mhi;

      if (result.crisis_tier === "active" || result.crisis_tier === "passive") {
        setCrisisTier(result.crisis_tier as "active" | "passive");
        setShowCrisisOverlay(true);
        playAlertTone("crisis");
      }

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

      const topEmotion = Object.entries(result.emotion_scores)
        .sort(([, a], [, b]) => b - a)[0]?.[0] ?? "default";
      void speakResponse(result.response, result.crisis_tier, topEmotion, langCode);

    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Chat request failed.");
    } finally {
      setIsSending(false);
    }
  }

  // Called by text Composer
  async function handleSend() {
    const text = draft.trim();
    if (!text || isSending) return;
    setDraft("");
    await submitMessage(text, languageCode, "text");
  }

  // Called by VoiceOrb after Whisper transcription — auto-sends for speech-to-speech
  function handleTranscript(text: string, confidence?: number, detectedLangCode?: string) {
    const effectiveLang = detectedLangCode ?? languageCode;
    setDraft(text);  // show transcript in composer so user can see what was heard
    if (confidence !== undefined) setWhisperConfidence(confidence);
    if (detectedLangCode) setLanguageCode(detectedLangCode);
    void submitMessage(text, effectiveLang, "voice");  // auto-send for speech-to-speech
  }

  const suggestions = [
    "I am feeling overwhelmed today",
    "Help me slow down for a minute",
    "I want to reflect on what triggered me",
  ];

  return (
    <div className="space-y-4">
      {/* Active crisis full-screen overlay */}
      {showCrisisOverlay && crisisTier === "active" && (
        <CrisisOverlay crisisTier="active" onDismiss={() => setShowCrisisOverlay(false)} />
      )}

      {/* Page header */}
      <div>
        <p className="label-caps">Chat</p>
        <h1 className="mt-1.5 text-[20px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          A calm space for reflection and support
        </h1>
        <p className="mt-1 text-[13px]" style={{ color: "#7a92a8" }}>
          Speak or type — the assistant listens in any language and responds with care.
        </p>
      </div>

      {/* Passive crisis banner */}
      {crisisTier === "passive" && (
        <CrisisOverlay crisisTier="passive" onDismiss={() => setCrisisTier(null)} />
      )}

      {/* Velocity alert banner */}
      {velocityAlert && (
        <div
          className="flex items-start gap-3 rounded-xl px-4 py-3"
          style={{ background: "rgba(181,130,42,0.08)", border: "1px solid rgba(181,130,42,0.25)" }}
        >
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" style={{ color: "#b5822a" }} />
          <p className="text-[13px] leading-relaxed" style={{ color: "#b5822a" }}>
            Your distress seems to be building. I&apos;m paying close attention — take your time.
          </p>
        </div>
      )}

      {/* MHI drop alert */}
      {mhiDropAlert && (
        <div
          className="flex items-start gap-3 rounded-xl px-4 py-3"
          style={{ background: "rgba(74,132,214,0.07)", border: "1px solid rgba(74,132,214,0.22)" }}
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" style={{ color: "#4a84d6" }} />
          <p className="text-[13px] leading-relaxed" style={{ color: "#7a92a8" }}>
            I noticed things seem heavier right now. I&apos;m here with you.
          </p>
        </div>
      )}

      {/* Main grid: Avatar (left) | Conversation (right) */}
      <div className="grid gap-4 lg:grid-cols-[2fr_3fr]">
        {/* Left: Avatar + Voice orb */}
        <div className="flex flex-col gap-3">
          <AvatarPanel
            avatarId={avatarId}
            speakAudioUrl={avatarAudioUrl}
            speakDurationMs={avatarDuration}
            isSpeaking={avatarSpeaking}
            isListening={isSending}
            onSpeakEnd={() => setAvatarSpeaking(false)}
            crisisTier={crisisTier}
          />
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

      {/* Active CBT card */}
      {activeCBT && (
        <div
          className="rounded-2xl p-4"
          style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
        >
          <div className="flex items-center justify-between mb-3">
            <p className="text-[12px] font-semibold" style={{ color: "#6a5acd" }}>
              Self-Help Exercise
            </p>
            <button
              type="button"
              onClick={() => setActiveCBT(null)}
              className="text-[11px] transition-colors"
              style={{ color: "#4a6278" }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "#c8d8ea"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "#4a6278"; }}
            >
              Close
            </button>
          </div>
          <CBTCard technique={activeCBT} onOpen={() => {}} />
          <p className="mt-3 text-[11px]" style={{ color: "#4a6278" }}>
            Full interactive CBT exercises are available in the Self-Help Tools tab of the Dashboard.
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
          className="flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-[12px] transition-all duration-300"
          style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(55,75,105,0.3)",
            color: status.toLowerCase().includes("fail") || status.toLowerCase().includes("error")
              ? "#c04040" : "#7a92a8",
          }}
        >
          {isSending && (
            <span className="h-3.5 w-3.5 rounded-full border-2 animate-spinSlow shrink-0"
              style={{ borderColor: "rgba(74,132,214,0.2)", borderTopColor: "#4a84d6" }} />
          )}
          {status}
        </div>
      )}

      <input type="hidden" value={languageCode} onChange={(e) => setLanguageCode(e.target.value)} />
    </div>
  );
}
