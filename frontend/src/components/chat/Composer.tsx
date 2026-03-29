import { Send } from "lucide-react";

type ComposerProps = {
  value: string;
  disabled?: boolean;
  suggestions?: string[];
  onChange: (value: string) => void;
  onSuggestionPick?: (value: string) => void;
  onSubmit: () => void;
};

export function Composer({
  value,
  disabled = false,
  suggestions = [],
  onChange,
  onSuggestionPick,
  onSubmit,
}: ComposerProps) {
  const charCount = value.trim().length;
  const canSend   = !disabled && charCount > 0;

  return (
    <section
      className="rounded-[20px] p-5"
      style={{
        background: "rgba(255,255,255,0.028)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onSuggestionPick?.(s)}
              disabled={disabled}
              className="rounded-full px-3 py-1.5 text-[12px] text-slate-400 transition-all duration-200 hover:text-white disabled:opacity-40"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(108,227,207,0.07)";
                (e.currentTarget as HTMLElement).style.border     = "1px solid rgba(108,227,207,0.18)";
                (e.currentTarget as HTMLElement).style.color      = "#6ce3cf";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
                (e.currentTarget as HTMLElement).style.border     = "1px solid rgba(255,255,255,0.07)";
                (e.currentTarget as HTMLElement).style.color      = "";
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div
        className="flex items-end gap-3 rounded-[16px] p-3 transition-all duration-200"
        style={{
          background: "rgba(255,255,255,0.03)",
          border: `1px solid ${value ? "rgba(108,227,207,0.2)" : "rgba(255,255,255,0.06)"}`,
        }}
      >
        <textarea
          rows={3}
          disabled={disabled}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
              e.preventDefault();
              if (canSend) onSubmit();
            }
          }}
          placeholder="Tell the assistant how you are feeling…"
          className="flex-1 resize-none bg-transparent text-[14px] leading-relaxed text-slate-200 outline-none placeholder:text-slate-600 disabled:opacity-50"
        />

        {/* Send button */}
        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSend}
          aria-label="Send message"
          className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] transition-all duration-200 active:scale-95 disabled:cursor-not-allowed disabled:opacity-30"
          style={{
            background: canSend
              ? "linear-gradient(135deg, #6ce3cf 0%, #2cb8c7 100%)"
              : "rgba(255,255,255,0.05)",
          }}
        >
          <Send
            className="h-4 w-4"
            style={{ color: canSend ? "#09111f" : "#475569" }}
            strokeWidth={2}
          />
        </button>
      </div>

      {/* Footer */}
      <div className="mt-3 flex items-center justify-between">
        <p className="text-[11px] text-slate-600">
          {disabled ? "Waiting for response…" : "Ctrl+Enter to send · Speak clearly and naturally"}
        </p>
        <p
          className="text-[11px]"
          style={{ color: charCount > 400 ? "#ffc96b" : "#475569" }}
        >
          {charCount} chars
        </p>
      </div>
    </section>
  );
}