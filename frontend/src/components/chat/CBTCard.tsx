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
      className="mt-2 flex w-full items-center gap-3 rounded-[14px] px-4 py-3 text-left transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
      style={{
        background: "rgba(108,227,207,0.07)",
        border: "1px solid rgba(108,227,207,0.2)",
      }}
    >
      <span className="text-[1.4rem]" role="img" aria-label={info.label}>
        {info.icon}
      </span>
      <div className="flex-1">
        <p className="text-[12px] font-semibold text-[#6ce3cf]">
          Try: {info.label}
        </p>
        <p className="text-[11px] text-slate-500">{info.description}</p>
      </div>
      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-[#6ce3cf]/60" />
    </button>
  );
}
