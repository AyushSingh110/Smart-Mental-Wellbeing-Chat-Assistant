type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  accent: string;
};

export function MetricCard({ label, value, detail, accent }: MetricCardProps) {
  return (
    <article
      className="rounded-2xl p-5 transition-all duration-150"
      style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.border = `1px solid ${accent}40`;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.border = "1px solid rgba(55,75,105,0.5)";
      }}
    >
      {/* Accent dot */}
      <div className="h-2 w-2 rounded-full" style={{ background: accent }} />

      <p className="mt-4 label-caps">{label}</p>
      <p className="mt-2 text-[2.2rem] font-bold leading-none tracking-tight text-white"
        style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        {value}
      </p>
      <p className="mt-3 text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>{detail}</p>
    </article>
  );
}
