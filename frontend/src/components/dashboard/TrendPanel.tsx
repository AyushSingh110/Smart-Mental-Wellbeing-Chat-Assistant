type TrendPanelProps = {
  values: number[];
};

export function TrendPanel({ values }: TrendPanelProps) {
  const max     = Math.max(...values, 1);
  const min     = Math.min(...values);
  const average = Math.round(values.reduce((s, v) => s + v, 0) / values.length);
  const isUp    = values[values.length - 1] >= values[0];

  const W = 560, H = 200, pad = 24;

  const pts = values.map((v, i) => ({
    x: pad + (i * (W - pad * 2)) / Math.max(values.length - 1, 1),
    y: H - pad - ((v - min) / Math.max(max - min, 1)) * (H - pad * 2),
    v,
    i,
  }));

  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const area = `${line} L${pts[pts.length - 1].x},${H - pad} L${pts[0].x},${H - pad} Z`;

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
            MHI trend
          </p>
          <h3
            className="mt-1.5 text-[16px] font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Seven-day stability curve
          </h3>
        </div>
        <div
          className="shrink-0 rounded-full px-3 py-1.5 text-[11px] font-medium"
          style={{
            background: isUp ? "rgba(123,228,149,0.1)" : "rgba(255,201,107,0.1)",
            border: isUp ? "1px solid rgba(123,228,149,0.2)" : "1px solid rgba(255,201,107,0.2)",
            color: isUp ? "#7be495" : "#ffc96b",
          }}
        >
          {values[values.length - 1]} · {isUp ? "↑ Upward" : "↓ Mixed"}
        </div>
      </div>

      {/* Chart */}
      <div
        className="mt-5 overflow-hidden rounded-[14px] p-3"
        style={{ background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.04)" }}
      >
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="h-48 w-full"
          role="img"
          aria-label="Mental health index trend"
        >
          <defs>
            <linearGradient id="area-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="rgba(108,227,207,0.35)" />
              <stop offset="100%" stopColor="rgba(108,227,207,0.01)" />
            </linearGradient>
            <linearGradient id="line-grad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%"   stopColor="#7be495" />
              <stop offset="50%"  stopColor="#6ce3cf" />
              <stop offset="100%" stopColor="#45d5cf" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map((r) => (
            <line
              key={r}
              x1={pad} y1={pad + r * (H - pad * 2)}
              x2={W - pad} y2={pad + r * (H - pad * 2)}
              stroke="rgba(148,163,184,0.08)"
              strokeDasharray="4 6"
            />
          ))}

          <path d={area} fill="url(#area-fill)" />
          <path
            d={line}
            fill="none"
            stroke="url(#line-grad)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Points */}
          {pts.map((p) => (
            <g key={p.i}>
              <circle cx={p.x} cy={p.y} r="4" fill="#09111f" stroke="#6ce3cf" strokeWidth="2" />
              <text
                x={p.x} y={H - 6}
                fill="rgba(148,163,184,0.5)"
                fontSize="11"
                textAnchor="middle"
              >
                D{p.i + 1}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        {[
          { label: "Average", value: `${average}` },
          { label: "Range",   value: `${min}–${max}` },
          { label: "Direction", value: isUp ? "Upward" : "Mixed" },
        ].map((s) => (
          <div
            key={s.label}
            className="rounded-[12px] px-3 py-3"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}
          >
            <p className="text-[10px] uppercase tracking-[0.18em] text-slate-600">{s.label}</p>
            <p
              className="mt-1 text-[15px] font-semibold text-white"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              {s.value}
            </p>
          </div>
        ))}
      </div>
    </article>
  );
}