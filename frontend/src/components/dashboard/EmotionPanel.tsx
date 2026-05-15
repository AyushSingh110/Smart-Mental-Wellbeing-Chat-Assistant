type EmotionPanelProps = {
  items: Array<{ label: string; value: number }>;
};

// Muted clinical colours for emotion bars
const EMOTION_COLORS = ["#4a84d6", "#3d8a5c", "#b5822a", "#6a5acd", "#c04040"];

export function EmotionPanel({ items }: EmotionPanelProps) {
  const strongest = items.reduce((cur, item) => item.value > cur.value ? item : cur);

  return (
    <article
      className="flex flex-col rounded-2xl p-5"
      style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="label-caps">Emotional pattern</p>
          <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Signals worth noticing
          </h3>
        </div>
        <div
          className="shrink-0 rounded-full px-3 py-1.5 text-[11px] font-semibold"
          style={{ background: "rgba(74,132,214,0.1)", border: "1px solid rgba(74,132,214,0.22)", color: "#4a84d6" }}
        >
          {strongest.label}
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {items.map((item, index) => {
          const color = EMOTION_COLORS[index % EMOTION_COLORS.length];
          return (
            <div key={item.label}>
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-[12px]" style={{ color: "#7a92a8" }}>{item.label}</span>
                <span className="text-[12px] font-semibold text-white">{item.value}%</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full" style={{ background: "rgba(55,75,105,0.4)" }}>
                <div
                  className="h-1.5 rounded-full transition-all duration-700"
                  style={{ width: `${item.value}%`, background: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}
