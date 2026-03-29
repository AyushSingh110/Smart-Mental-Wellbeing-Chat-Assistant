import { useEffect, useState } from "react";

import { Composer } from "../components/chat/Composer";
import { ConversationPanel } from "../components/chat/ConversationPanel";
import { VoiceOrb } from "../components/chat/VoiceOrb";
import { PageHeader } from "../components/shared/PageHeader";
import { getConversationHistory, sendChatMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { ConversationEntry } from "../types";

export function ChatPage() {
  const { token } = useAuth();
  const [entries, setEntries] = useState<ConversationEntry[]>([]);
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState("");
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    if (!token) return;
    void getConversationHistory(token).then(setEntries);
  }, [token]);

  const suggestions = [
    "I am feeling overwhelmed today",
    "Help me slow down for a minute",
    "I want to reflect on what triggered me",
  ];

  async function handleSend() {
    if (!token || !draft.trim()) return;

    const text = draft.trim();
    const timestamp = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    setIsSending(true);
    setStatus("Analyzing message...");
    setEntries((current) => [
      ...current,
      {
        id: `local-user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp,
      },
    ]);
    setDraft("");

    try {
      const result = await sendChatMessage(token, text);
      setEntries((current) => [
        ...current,
        {
          id: `local-assistant-${Date.now()}`,
          role: "assistant",
          content: `${result.response}\n\nMHI ${result.mhi} - ${result.category} - intent: ${result.intent}`,
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
      setStatus("Response generated successfully.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Chat request failed.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Chat"
        title="A calm conversation space for reflection, check-ins, and gentle support"
        description="The layout keeps attention on the exchange itself, with quiet visual framing and enough structure to make returning feel easy."
      />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <VoiceOrb />
        <ConversationPanel entries={entries} />
      </div>

      <Composer
        value={draft}
        disabled={isSending}
        suggestions={suggestions}
        onChange={setDraft}
        onSuggestionPick={setDraft}
        onSubmit={() => void handleSend()}
      />

      {status ? (
        <div className="surface-card animate-rise-in rounded-[24px] border border-white/10 px-4 py-3 text-sm text-slate-300 shadow-halo">
          {status}
        </div>
      ) : null}
    </div>
  );
}
