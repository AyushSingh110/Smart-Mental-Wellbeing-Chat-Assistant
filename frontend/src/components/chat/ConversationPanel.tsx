import { useEffect, useRef } from "react";
import clsx from "clsx";
import { MessageSquare } from "lucide-react";
import type { ConversationEntry } from "../../types";
import { CBTCard } from "./CBTCard";

type ConversationPanelProps = {
  entries: ConversationEntry[];
  onOpenCBT?: (technique: string) => void;
  languageCode?: string;
  whisperConfidence?: number;
};

const LANG_NAMES: Record<string, string> = {
  hi: "Hindi", bn: "Bengali", ta: "Tamil",   te: "Telugu",    mr: "Marathi",
  gu: "Gujarati", pa: "Punjabi", kn: "Kannada", ml: "Malayalam", ur: "Urdu",
  or: "Odia", as: "Assamese", ne: "Nepali",  sa: "Sanskrit",  en: "English",
};

const INDIAN_LANGS = new Set(["hi","bn","ta","te","mr","gu","pa","kn","ml","ur","or","as","ne","sa"]);

function getMhiColor(mhi: number): string {
  if (mhi >= 75) return "#3d8a5c";
  if (mhi >= 55) return "#b5822a";
  return "#c04040";
}

export function ConversationPanel({
  entries, onOpenCBT, languageCode, whisperConfidence,
}: ConversationPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  const langLabel = languageCode ? LANG_NAMES[languageCode] ?? languageCode.toUpperCase() : null;
  const isIndian  = languageCode ? INDIAN_LANGS.has(languageCode) : false;

  return (
    <article
      className="flex flex-col rounded-2xl"
      style={{
        background: "#172032",
        border: "1px solid rgba(55,75,105,0.5)",
        minHeight: "420px",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between gap-3 px-5 py-4 shrink-0"
        style={{ borderBottom: "1px solid rgba(55,75,105,0.4)" }}
      >
        <div className="flex items-center gap-2.5">
          <MessageSquare className="h-4 w-4" style={{ color: "#4a6278" }} />
          <div>
            <p className="text-[13px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Conversation
            </p>
            <p className="text-[10px]" style={{ color: "#4a6278" }}>Response timeline</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {langLabel && (
            <div
              className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold"
              style={{ background: "rgba(74,132,214,0.1)", border: "1px solid rgba(74,132,214,0.2)", color: "#4a84d6" }}
            >
              <span>{isIndian ? "🇮🇳" : "🇬🇧"}</span>
              {langLabel}
              {whisperConfidence !== undefined && (
                <span style={{ color: whisperConfidence >= 0.75 ? "#3d8a5c" : "#b5822a", marginLeft: 2 }}>
                  {Math.round(whisperConfidence * 100)}%
                </span>
              )}
            </div>
          )}
          <div
            className="rounded-full px-2.5 py-1 text-[10px] font-medium"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(55,75,105,0.35)", color: "#4a6278" }}
          >
            {entries.length} msgs
          </div>
        </div>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-5 space-y-3"
        style={{ maxHeight: "420px", scrollbarWidth: "thin", scrollbarColor: "rgba(55,75,105,0.5) transparent" }}
      >
        {entries.length === 0 ? (
          <div
            className="flex flex-col items-center justify-center py-14 text-center rounded-xl"
            style={{ border: "1px dashed rgba(55,75,105,0.4)" }}
          >
            <div
              className="mb-3 flex h-10 w-10 items-center justify-center rounded-full"
              style={{ background: "rgba(74,132,214,0.1)" }}
            >
              <MessageSquare className="h-5 w-5" style={{ color: "#4a84d6" }} />
            </div>
            <p className="text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              No messages yet
            </p>
            <p className="mt-1.5 text-[12px] max-w-[200px]" style={{ color: "#4a6278" }}>
              Start with a short check-in or reflection from today.
            </p>
          </div>
        ) : (
          entries.map((entry) => (
            <div key={entry.id}>
              <MessageBubble entry={entry} />
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
  const mhiColor    = getMhiColor(entry.mhi ?? 100);

  return (
    <div className={clsx("flex flex-col", isAssistant ? "items-start" : "items-end")}>
      <div
        className={clsx(
          "max-w-[85%] rounded-2xl px-4 py-3",
          isAssistant ? "rounded-tl-[6px]" : "rounded-tr-[6px]",
        )}
        style={
          isAssistant
            ? { background: "#1d2940", border: "1px solid rgba(74,132,214,0.2)" }
            : { background: "#4a84d6", border: "1px solid rgba(74,132,214,0.4)" }
        }
      >
        {/* Role + timestamp */}
        <div className="flex items-center justify-between gap-4 mb-2">
          <span
            className="text-[10px] font-bold uppercase tracking-[0.16em]"
            style={{ color: isAssistant ? "#4a84d6" : "rgba(255,255,255,0.7)" }}
          >
            {isAssistant ? "Assistant" : "You"}
          </span>
          <span className="text-[10px]" style={{ color: isAssistant ? "#4a6278" : "rgba(255,255,255,0.5)" }}>
            {entry.timestamp}
          </span>
        </div>

        <p
          className="text-[13px] leading-relaxed whitespace-pre-line"
          style={{ color: isAssistant ? "#c8d8ea" : "#ffffff" }}
        >
          {entry.content}
        </p>

        {/* MHI + category metadata */}
        {isAssistant && entry.mhi !== undefined && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{ background: `${mhiColor}18`, color: mhiColor, border: `1px solid ${mhiColor}30` }}
            >
              MHI {entry.mhi}
            </span>
            {entry.category && (
              <span
                className="rounded-full px-2 py-0.5 text-[10px]"
                style={{ background: "rgba(255,255,255,0.04)", color: "#4a6278", border: "1px solid rgba(55,75,105,0.3)" }}
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
