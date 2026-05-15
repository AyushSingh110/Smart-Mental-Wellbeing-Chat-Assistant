import { ArrowRight } from "lucide-react";
import { CBT_TECHNIQUES } from "../../types";

type CBTCardProps = {
  technique: string;
  onOpen: (technique: string) => void;
};

export function CBTCard({ technique, onOpen }: CBTCardProps) {
  const info = CBT_TECHNIQUES.find((t) => t.id === technique);
  if (!info) return null;

  return (
    <button
      type="button"
      onClick={() => onOpen(technique)}
      className="mt-2 flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-all duration-150 active:scale-[0.98]"
      style={{
        background: "rgba(106,90,205,0.08)",
        border: "1px solid rgba(106,90,205,0.22)",
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(106,90,205,0.12)"; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(106,90,205,0.08)"; }}
    >
      <span className="text-[1.3rem]" role="img" aria-label={info.label}>
        {info.icon}
      </span>
      <div className="flex-1">
        <p className="text-[12px] font-semibold" style={{ color: "#6a5acd" }}>
          Try: {info.label}
        </p>
        <p className="text-[11px]" style={{ color: "#4a6278" }}>{info.description}</p>
      </div>
      <ArrowRight className="h-3.5 w-3.5 shrink-0" style={{ color: "#6a5acd", opacity: 0.6 }} />
    </button>
  );
}
