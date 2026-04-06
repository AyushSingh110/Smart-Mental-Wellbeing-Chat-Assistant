import { useEffect, useRef } from "react";
import clsx from "clsx";
import type { ConversationEntry } from "../../types";
import { CBTCard } from "./CBTCard";

type ConversationPanelProps = {
  entries: ConversationEntry[];
  onOpenCBT?: (technique: string) => void;
  languageCode?: string;
  whisperConfidence?: number;  // 0-1, from STT result
};

const LANG_NAMES: Record<string, string> = {
  hi: "Hindi", bn: "Bengali", ta: "Tamil", te: "Telugu", mr: "Marathi",
  gu: "Gujarati", pa: "Punjabi", kn: "Kannada", ml: "Malayalam", ur: "Urdu",
  or: "Odia", as: "Assamese", ne: "Nepali", sa: "Sanskrit", en: "English",
};

const INDIAN_LANGS = new Set(["hi","bn","ta","te","mr","gu","pa","kn","ml","ur","or","as","ne","sa"]);

export function ConversationPanel({
  entries,
  onOpenCBT,
  languageCode,
  whisperConfidence,
}: ConversationPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  const langLabel = languageCode ? LANG_NAMES[languageCode] ?? languageCode.toUpperCase() : null;
  const isIndian = languageCode ? INDIAN_LANGS.has(languageCode) : false;

  return (
    <article
      className="flex flex-col rounded-[20px] p-5"
      style={{
        background: "rgba(255,255,255,0.028)",
        border: "1px solid rgba(255,255,255,0.07)",
        minHeight: "420px",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3 shrink-0">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
            Conversation
          </p>
          <h3
            className="mt-1.5 text-[16px] font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Response timeline
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {/* Language detection badge */}
          {langLabel && (
            <div
              className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium"
              style={{
                background: "rgba(108,227,207,0.08)",
                border: "1px solid rgba(108,227,207,0.18)",
                color: "#6ce3cf",
              }}
            >
              <span>{isIndian ? "\u{1F1EE}\u{1F1F3}" : "\u{1F1EC}\u{1F1E7}"}</span>
              {langLabel}
              {whisperConfidence !== undefined && (
                <span style={{ color: whisperConfidence >= 0.75 ? "#7be495" : "#ffc96b", marginLeft: 2 }}>
                  {Math.round(whisperConfidence * 100)}%
                </span>
              )}
            </div>
          )}
          <div
            className="shrink-0 rounded-full px-3 py-1.5 text-[11px] text-slate-500"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            {entries.length} messages
          </div>
        </div>
      </div>

      {/* Messages */}
      <div
        className="mt-4 flex-1 overflow-y-auto space-y-3 pr-1"
        style={{ maxHeight: "400px", scrollbarWidth: "thin", scrollbarColor: "rgba(255,255,255,0.06) transparent" }}
      >
        {entries.length === 0 ? (
          <div
            className="flex flex-col items-center justify-center py-12 text-center"
            style={{
              border: "1px dashed rgba(255,255,255,0.08)",
              borderRadius: "14px",
              background: "rgba(255,255,255,0.01)",
            }}
          >
            <div
              className="mb-3 flex h-10 w-10 items-center justify-center rounded-full"
              style={{ background: "rgba(108,227,207,0.08)" }}
            >
              <span className="text-[18px]">💬</span>
            </div>
            <p
              className="text-[14px] font-semibold text-white"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              No messages yet
            </p>
            <p className="mt-1.5 text-[12px] text-slate-600 max-w-[200px]">
              Start with a short check-in or reflection from today.
            </p>
          </div>
        ) : (
          entries.map((entry) => (
            <div key={entry.id}>
              <MessageBubble entry={entry} />
              {/* CBT suggestion card below assistant message */}
              {entry.role === "assistant" && entry.cbtTechniqueSuggested && onOpenCBT && (
                <CBTCard technique={entry.cbtTechniqueSuggested} onOpen={onOpenCBT} />
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </article>
  );
}

function MessageBubble({ entry }: { entry: ConversationEntry }) {
  const isAssistant = entry.role === "assistant";

  const mhiColor =
    (entry.mhi ?? 100) >= 75 ? "#7be495"
    : (entry.mhi ?? 100) >= 55 ? "#ffc96b"
    : "#ff7b70";

  return (
    <div className={clsx("flex flex-col", isAssistant ? "items-start" : "items-end")}>
      <div
        className={clsx(
          "max-w-[85%] rounded-[16px] px-4 py-3",
          isAssistant ? "rounded-tl-[4px]" : "rounded-tr-[4px]",
        )}
        style={
          isAssistant
            ? { background: "rgba(108,227,207,0.07)", border: "1px solid rgba(108,227,207,0.14)" }
            : { background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.09)" }
        }
      >
        {/* Role label + timestamp */}
        <div className="flex items-center justify-between gap-4 mb-2">
          <span
            className="text-[10px] font-semibold uppercase tracking-[0.18em]"
            style={{ color: isAssistant ? "#6ce3cf" : "#94a3b8" }}
          >
            {isAssistant ? "Assistant" : "You"}
          </span>
          <span className="text-[10px] text-slate-600">{entry.timestamp}</span>
        </div>

        {/* Content */}
        <p className="text-[13px] leading-relaxed text-slate-200 whitespace-pre-line">
          {entry.content}
        </p>

        {/* MHI + category metadata for assistant messages */}
        {isAssistant && entry.mhi !== undefined && (
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{ background: `${mhiColor}15`, color: mhiColor, border: `1px solid ${mhiColor}30` }}
            >
              MHI {entry.mhi}
            </span>
            {entry.category && (
              <span
                className="rounded-full px-2 py-0.5 text-[10px]"
                style={{ background: "rgba(255,255,255,0.04)", color: "#64748b", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                {entry.category}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
