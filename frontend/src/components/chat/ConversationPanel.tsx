import clsx from "clsx";

import type { ConversationEntry } from "../../types";

type ConversationPanelProps = {
  entries: ConversationEntry[];
};

export function ConversationPanel({ entries }: ConversationPanelProps) {
  return (
    <section className="surface-card animate-rise-in rounded-[30px] border border-white/10 p-6 shadow-halo">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Conversation flow</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-white">
            Response timeline
          </h3>
        </div>
        <div className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300">
          {entries.length} messages
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="mt-6 rounded-[28px] border border-dashed border-white/10 bg-white/[0.02] p-8 text-center">
          <p className="font-display text-xl font-semibold text-white">No messages yet</p>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            Start with a short check-in, a question, or a reflection from today.
          </p>
        </div>
      ) : (
        <div className="mt-6 max-h-[560px] space-y-4 overflow-y-auto pr-1">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className={clsx(
                "max-w-4xl rounded-[24px] border px-5 py-4",
                entry.role === "assistant"
                  ? "border-brand-300/16 bg-brand-300/8"
                  : "ml-auto border-white/8 bg-white/[0.03]",
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-display text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">
                  {entry.role}
                </span>
                <span className="text-xs text-slate-500">{entry.timestamp}</span>
              </div>
              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-200">
                {entry.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
