type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  accent: string;
};

export function MetricCard({ label, value, detail, accent }: MetricCardProps) {
  return (
    <article
      className="group relative overflow-hidden rounded-[20px] p-5 transition-all duration-300 hover:-translate-y-0.5"
      style={{
        background: "rgba(255,255,255,0.028)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.border = `1px solid ${accent}30`;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.border = "1px solid rgba(255,255,255,0.07)";
      }}
    >
      {/* Accent glow top-right */}
      <div
        className="pointer-events-none absolute -right-4 -top-4 h-20 w-20 rounded-full opacity-20 transition-opacity duration-300 group-hover:opacity-40"
        style={{ background: `radial-gradient(circle, ${accent}, transparent 70%)`, filter: "blur(16px)" }}
      />

      {/* Accent dot */}
      <div
        className="h-2 w-2 rounded-full"
        style={{ background: accent, boxShadow: `0 0 8px ${accent}` }}
      />

      <p className="mt-4 text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </p>
      <p
        className="mt-2 text-[2.4rem] font-bold leading-none tracking-tight text-white"
        style={{ fontFamily: "'Space Grotesk', sans-serif" }}
      >
        {value}
      </p>
      <p className="mt-3 text-[12px] leading-relaxed text-slate-500">{detail}</p>
    </article>
  );
}