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
  value, disabled = false, suggestions = [], onChange, onSuggestionPick, onSubmit,
}: ComposerProps) {
  const charCount = value.trim().length;
  const canSend   = !disabled && charCount > 0;

  return (
    <section
      className="rounded-2xl p-4"
      style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
    >
      {/* Suggestion chips */}
      {suggestions.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onSuggestionPick?.(s)}
              disabled={disabled}
              className="rounded-full px-3 py-1.5 text-[12px] font-medium transition-all duration-150 disabled:opacity-40"
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(55,75,105,0.4)", color: "#7a92a8" }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(74,132,214,0.1)";
                (e.currentTarget as HTMLElement).style.borderColor = "rgba(74,132,214,0.3)";
                (e.currentTarget as HTMLElement).style.color = "#4a84d6";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
                (e.currentTarget as HTMLElement).style.borderColor = "rgba(55,75,105,0.4)";
                (e.currentTarget as HTMLElement).style.color = "#7a92a8";
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div
        className="flex items-end gap-3 rounded-xl p-3 transition-all duration-150"
        style={{
          background: "#0c1220",
          border: `1px solid ${value ? "rgba(74,132,214,0.35)" : "rgba(55,75,105,0.4)"}`,
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
          className="flex-1 resize-none bg-transparent text-[13px] leading-relaxed outline-none disabled:opacity-50"
          style={{ color: "#c8d8ea" }}
        />

        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSend}
          aria-label="Send message"
          className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all duration-150 active:scale-95 disabled:cursor-not-allowed disabled:opacity-30"
          style={{ background: canSend ? "#4a84d6" : "rgba(255,255,255,0.05)" }}
          onMouseEnter={(e) => { if (canSend) (e.currentTarget as HTMLElement).style.background = "#3168b8"; }}
          onMouseLeave={(e) => { if (canSend) (e.currentTarget as HTMLElement).style.background = "#4a84d6"; }}
        >
          <Send className="h-4 w-4" style={{ color: canSend ? "#ffffff" : "#4a6278" }} strokeWidth={2} />
        </button>
      </div>

      {/* Footer hint */}
      <div className="mt-2.5 flex items-center justify-between">
        <p className="text-[11px]" style={{ color: "#4a6278" }}>
          {disabled ? "Waiting for response…" : "Ctrl+Enter to send"}
        </p>
        <p className="text-[11px]" style={{ color: charCount > 400 ? "#b5822a" : "#4a6278" }}>
          {charCount} chars
        </p>
      </div>
    </section>
  );
}
