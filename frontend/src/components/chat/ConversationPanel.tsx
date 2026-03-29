import { useEffect, useRef } from "react";
import clsx from "clsx";
import type { ConversationEntry } from "../../types";

type ConversationPanelProps = {
  entries: ConversationEntry[];
};

export function ConversationPanel({ entries }: ConversationPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

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

      {/* Messages */}
      <div className="mt-4 flex-1 overflow-y-auto space-y-3 pr-1"
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
            <MessageBubble key={entry.id} entry={entry} />
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </article>
  );
}

function MessageBubble({ entry }: { entry: ConversationEntry }) {
  const isAssistant = entry.role === "assistant";

  return (
    <div className={clsx("flex", isAssistant ? "justify-start" : "justify-end")}>
      <div
        className={clsx(
          "max-w-[85%] rounded-[16px] px-4 py-3",
          isAssistant ? "rounded-tl-[4px]" : "rounded-tr-[4px]",
        )}
        style={
          isAssistant
            ? {
                background: "rgba(108,227,207,0.07)",
                border: "1px solid rgba(108,227,207,0.14)",
              }
            : {
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.09)",
              }
        }
      >
        {/* Role label */}
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
      </div>
    </div>
  );
}