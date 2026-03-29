import { useEffect, useRef, useState } from "react";

import { Composer }          from "../components/chat/Composer";
import { ConversationPanel } from "../components/chat/ConversationPanel";
import { VoiceOrb }          from "../components/chat/VoiceOrb";
import { PageHeader }        from "../components/shared/PageHeader";
import { getConversationHistory, sendChatMessage } from "../lib/api";
import { useAuth }           from "../lib/auth";
import type { ConversationEntry } from "../types";

export function ChatPage() {
  const { token }                                   = useAuth();
  const [entries, setEntries]                       = useState<ConversationEntry[]>([]);
  const [draft, setDraft]                           = useState("");
  const [status, setStatus]                         = useState("");
  const [isSending, setIsSending]                   = useState(false);
  const statusTimer                                 = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!token) return;
    void getConversationHistory(token).then(setEntries);
  }, [token]);

  // Auto-clear status after 4 seconds
  useEffect(() => {
    if (!status) return;
    if (statusTimer.current) clearTimeout(statusTimer.current);
    statusTimer.current = setTimeout(() => setStatus(""), 4000);
    return () => {
      if (statusTimer.current) clearTimeout(statusTimer.current);
    };
  }, [status]);

  // VoiceOrb → appends transcript to draft
  function handleTranscript(text: string) {
    setDraft((prev) => {
      const trimmed = prev.trimEnd();
      return trimmed ? `${trimmed} ${text}` : text;
    });
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
      const result = await sendChatMessage(token, text);
      setEntries((prev) => [
        ...prev,
        {
          id:        `assistant-${Date.now()}`,
          role:      "assistant",
          content:   `${result.response}\n\nMHI ${result.mhi} · ${result.category} · intent: ${result.intent}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
      setStatus("Response received.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Chat request failed.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Chat"
        title="A calm conversation space for reflection and gentle support"
        description="Speak or type — the assistant listens in any language and responds with care."
      />

      {/* Main grid */}
      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        {/* VoiceOrb — left */}
        <VoiceOrb
          onTranscript={handleTranscript}
          disabled={isSending}
        />

        {/* Conversation — right */}
        <ConversationPanel entries={entries} />
      </div>

      {/* Composer — full width */}
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
            <span
              className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-[#6ce3cf]/20 border-t-[#6ce3cf]"
            />
          )}
          {status}
        </div>
      )}
    </div>
  );
}