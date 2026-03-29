type EmotionPanelProps = {
  items: Array<{ label: string; value: number }>;
};

const ACCENT_COLORS = [
  "#6ce3cf",
  "#7be495",
  "#ffc96b",
  "#ff7b70",
  "#a78bfa",
];

export function EmotionPanel({ items }: EmotionPanelProps) {
  const strongest = items.reduce((cur, item) =>
    item.value > cur.value ? item : cur,
  );

  return (
    <article
      className="flex flex-col rounded-[20px] p-5"
      style={{
        background: "rgba(255,255,255,0.028)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
            Emotional pattern
          </p>
          <h3
            className="mt-1.5 text-[16px] font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Signals worth noticing
          </h3>
        </div>
        <div
          className="shrink-0 rounded-full px-3 py-1.5 text-[11px] font-medium"
          style={{
            background: "rgba(108,227,207,0.1)",
            border: "1px solid rgba(108,227,207,0.18)",
            color: "#6ce3cf",
          }}
        >
          {strongest.label}
        </div>
      </div>

      {/* Bars */}
      <div className="mt-5 space-y-3">
        {items.map((item, index) => {
          const color = ACCENT_COLORS[index % ACCENT_COLORS.length];
          return (
            <div key={item.label}>
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-[12px] text-slate-400">{item.label}</span>
                <span className="text-[12px] font-medium text-slate-300">{item.value}%</span>
              </div>
              <div
                className="h-2 w-full overflow-hidden rounded-full"
                style={{ background: "rgba(255,255,255,0.05)" }}
              >
                <div
                  className="h-2 rounded-full transition-all duration-700"
                  style={{
                    width: `${item.value}%`,
                    background: color,
                    boxShadow: `0 0 8px ${color}50`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}