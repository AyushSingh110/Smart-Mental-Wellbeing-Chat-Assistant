type TrendPanelProps = {
  values: number[];
};

export function TrendPanel({ values }: TrendPanelProps) {
  const max     = Math.max(...values, 1);
  const min     = Math.min(...values);
  const average = Math.round(values.reduce((s, v) => s + v, 0) / values.length);
  const isUp    = values[values.length - 1] >= values[0];

  const W = 560, H = 180, pad = 24;

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
      className="flex flex-col rounded-2xl p-5"
      style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="label-caps">MHI trend</p>
          <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Seven-day stability curve
          </h3>
        </div>
        <div
          className="shrink-0 rounded-full px-3 py-1.5 text-[11px] font-semibold"
          style={{
            background: isUp ? "rgba(61,138,92,0.1)" : "rgba(181,130,42,0.1)",
            border:     isUp ? "1px solid rgba(61,138,92,0.25)" : "1px solid rgba(181,130,42,0.25)",
            color:      isUp ? "#3d8a5c" : "#b5822a",
          }}
        >
          {values[values.length - 1]} · {isUp ? "↑ Upward" : "↓ Mixed"}
        </div>
      </div>

      {/* Chart */}
      <div
        className="mt-4 overflow-hidden rounded-xl p-3"
        style={{ background: "#0c1220", border: "1px solid rgba(55,75,105,0.35)" }}
      >
        <svg viewBox={`0 0 ${W} ${H}`} className="h-44 w-full" role="img" aria-label="MHI trend">
          <defs>
            <linearGradient id="area-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="rgba(74,132,214,0.22)" />
              <stop offset="100%" stopColor="rgba(74,132,214,0.01)" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map((r) => (
            <line
              key={r}
              x1={pad} y1={pad + r * (H - pad * 2)}
              x2={W - pad} y2={pad + r * (H - pad * 2)}
              stroke="rgba(55,75,105,0.4)"
              strokeDasharray="4 6"
            />
          ))}

          <path d={area} fill="url(#area-fill)" />
          <path d={line} fill="none" stroke="#4a84d6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

          {pts.map((p) => (
            <g key={p.i}>
              <circle cx={p.x} cy={p.y} r="4" fill="#172032" stroke="#4a84d6" strokeWidth="2" />
              <text x={p.x} y={H - 6} fill="rgba(74,98,120,0.8)" fontSize="10" textAnchor="middle">
                D{p.i + 1}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-3 gap-2.5">
        {[
          { label: "Average",   value: `${average}` },
          { label: "Range",     value: `${min}–${max}` },
          { label: "Direction", value: isUp ? "Upward" : "Mixed" },
        ].map((s) => (
          <div
            key={s.label}
            className="rounded-xl px-3 py-2.5"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.35)" }}
          >
            <p className="label-caps">{s.label}</p>
            <p className="mt-1 text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              {s.value}
            </p>
          </div>
        ))}
      </div>
    </article>
  );
}
