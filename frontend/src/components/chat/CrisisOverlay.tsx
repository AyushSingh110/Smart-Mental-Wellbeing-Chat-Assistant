import { useEffect, useRef, useState } from "react";
import { Phone, ShieldAlert, X } from "lucide-react";

type CrisisOverlayProps = {
  crisisTier: "active" | "passive" | null;
  onDismiss: () => void;
};

const HELPLINES = [
  { name: "Kiran Mental Health Helpline", number: "1800-599-0019", free: true  },
  { name: "iCall (TISS)",                 number: "9152987821",    free: false },
  { name: "AASRA",                         number: "9820466627",    free: false },
  { name: "Vandrevala Foundation",         number: "1860-2662-345", free: true  },
];

export function CrisisOverlay({ crisisTier, onDismiss }: CrisisOverlayProps) {
  const [canDismiss, setCanDismiss] = useState(crisisTier !== "active");
  const [countdown, setCountdown]   = useState(crisisTier === "active" ? 10 : 0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (crisisTier !== "active") {
      setCanDismiss(true);
      return;
    }
    setCanDismiss(false);
    setCountdown(10);

    intervalRef.current = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          setCanDismiss(true);
          return 0;
        }
        return c - 1;
      });
    }, 1000);

    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [crisisTier]);

  if (!crisisTier) return null;

  const isActive = crisisTier === "active";

  // Passive: persistent inline banner
  if (!isActive) {
    return (
      <div
        className="flex items-start gap-3 rounded-xl px-4 py-3"
        style={{ background: "rgba(192,64,64,0.07)", border: "1px solid rgba(192,64,64,0.25)" }}
      >
        <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" style={{ color: "#c04040" }} />
        <div className="flex-1">
          <p className="text-[13px] font-semibold" style={{ color: "#c04040" }}>
            Support resources are available
          </p>
          <p className="mt-1 text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>
            You don&apos;t have to face this alone. Free helplines are available 24/7:
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {HELPLINES.slice(0, 2).map((h) => (
              <div
                key={h.number}
                className="flex items-center gap-1.5 rounded-full px-3 py-1"
                style={{ background: "rgba(192,64,64,0.08)", border: "1px solid rgba(192,64,64,0.2)" }}
              >
                <Phone className="h-3 w-3" style={{ color: "#c04040" }} />
                <span className="text-[11px] font-medium" style={{ color: "#c04040" }}>
                  {h.name}: {h.number}{h.free && " (Free)"}
                </span>
              </div>
            ))}
          </div>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 mt-0.5 rounded-lg p-1.5 transition-colors"
          style={{ color: "#4a6278" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "#c8d8ea"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "#4a6278"; }}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }

  // Active: full-screen overlay
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(12,18,32,0.96)" }}
    >
      <div
        className="w-full max-w-[500px] rounded-2xl p-8"
        style={{ background: "#172032", border: "1px solid rgba(192,64,64,0.4)" }}
      >
        {/* Icon */}
        <div
          className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full"
          style={{ background: "rgba(192,64,64,0.12)", border: "1px solid rgba(192,64,64,0.3)" }}
        >
          <ShieldAlert className="h-7 w-7" style={{ color: "#c04040" }} />
        </div>

        <h2 className="text-center text-[20px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          You are not alone
        </h2>
        <p className="mt-3 text-center text-[13px] leading-relaxed" style={{ color: "#7a92a8" }}>
          It sounds like you may be going through something very difficult right now.
          Please reach out to one of these free, confidential support lines —
          trained counsellors are available right now.
        </p>

        <div className="mt-6 space-y-2">
          {HELPLINES.map((h) => (
            <div
              key={h.number}
              className="flex items-center justify-between rounded-xl px-4 py-3"
              style={{ background: "rgba(192,64,64,0.06)", border: "1px solid rgba(192,64,64,0.18)" }}
            >
              <div>
                <p className="text-[13px] font-medium text-white">{h.name}</p>
                {h.free && <p className="text-[10px]" style={{ color: "#3d8a5c" }}>Free call</p>}
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-3.5 w-3.5" style={{ color: "#c04040" }} />
                <span className="text-[14px] font-bold" style={{ color: "#c04040" }}>{h.number}</span>
              </div>
            </div>
          ))}
        </div>

        <button
          type="button"
          disabled={!canDismiss}
          onClick={onDismiss}
          className="mt-6 w-full rounded-xl py-3 text-[13px] font-semibold transition-all duration-200 disabled:opacity-40"
          style={{
            background: canDismiss ? "rgba(255,255,255,0.07)" : "rgba(255,255,255,0.03)",
            border: "1px solid rgba(55,75,105,0.4)",
            color: canDismiss ? "#c8d8ea" : "#4a6278",
          }}
        >
          {canDismiss ? (
            <span className="flex items-center justify-center gap-2">
              <X className="h-4 w-4" />
              I understand, close this
            </span>
          ) : (
            `Please read the resources above (${countdown}s)`
          )}
        </button>
      </div>
    </div>
  );
}
