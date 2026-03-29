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
  return (
    <section className="surface-card animate-rise-in rounded-[30px] border border-white/10 p-6 shadow-halo">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Message</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-white">
            Share what is on your mind
          </h3>
        </div>
        <p className="text-sm text-slate-400">Press Ctrl+Enter or use the button to send.</p>
      </div>
      <div className="mt-5 rounded-[26px] border border-white/8 bg-white/[0.02] p-4">
        <textarea
          rows={4}
          disabled={disabled}
          className="w-full resize-none bg-transparent text-sm leading-7 text-slate-200 outline-none disabled:text-slate-500"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
              event.preventDefault();
              onSubmit();
            }
          }}
          placeholder="Tell the assistant how you are feeling..."
        />
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSuggestionPick?.(suggestion)}
            className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-200 transition hover:border-brand-300/20 hover:bg-brand-300/10 hover:text-brand-100"
          >
            {suggestion}
          </button>
        ))}
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
          className="ml-auto rounded-2xl bg-gradient-to-r from-brand-600 to-brand-400 px-5 py-3 text-sm font-semibold text-ink transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Send message
        </button>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
        <span>Use clear language. You do not need to structure anything perfectly.</span>
        <span>{value.trim().length} chars</span>
      </div>
    </section>
  );
}
