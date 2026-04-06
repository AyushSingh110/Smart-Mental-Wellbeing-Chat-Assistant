import { useEffect, useRef, useState } from "react";
import { Phone, ShieldAlert, X } from "lucide-react";

type CrisisOverlayProps = {
  crisisTier: "active" | "passive" | null;
  onDismiss: () => void;
};

const HELPLINES = [
  { name: "Kiran Mental Health Helpline", number: "1800-599-0019", free: true },
  { name: "iCall (TISS)", number: "9152987821", free: false },
  { name: "AASRA", number: "9820466627", free: false },
  { name: "Vandrevala Foundation", number: "1860-2662-345", free: true },
];

export function CrisisOverlay({ crisisTier, onDismiss }: CrisisOverlayProps) {
  const [canDismiss, setCanDismiss] = useState(crisisTier !== "active");
  const [countdown, setCountdown] = useState(crisisTier === "active" ? 10 : 0);
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

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [crisisTier]);

  if (!crisisTier) return null;

  const isActive = crisisTier === "active";

  // Passive crisis: persistent banner (not full-screen)
  if (!isActive) {
    return (
      <div
        className="mx-0 flex items-start gap-3 rounded-[14px] p-4"
        style={{
          background: "rgba(255,123,112,0.08)",
          border: "1px solid rgba(255,123,112,0.25)",
        }}
      >
        <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-[#ff7b70]" />
        <div className="flex-1">
          <p className="text-[13px] font-semibold text-[#ff7b70]">
            Support resources are available
          </p>
          <p className="mt-1 text-[12px] text-slate-400">
            You don't have to face this alone. Free helplines are available 24/7:
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {HELPLINES.slice(0, 2).map((h) => (
              <div
                key={h.number}
                className="flex items-center gap-1.5 rounded-full px-3 py-1"
                style={{ background: "rgba(255,123,112,0.1)", border: "1px solid rgba(255,123,112,0.2)" }}
              >
                <Phone className="h-3 w-3 text-[#ff7b70]" />
                <span className="text-[11px] font-medium text-[#ff7b70]">
                  {h.name}: {h.number}
                  {h.free && " (Free)"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Active crisis: full-screen overlay
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(9,17,31,0.95)", backdropFilter: "blur(8px)" }}
    >
      <div
        className="w-full max-w-[520px] rounded-[28px] p-8"
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,123,112,0.35)",
          boxShadow: "0 0 80px rgba(255,123,112,0.12)",
        }}
      >
        {/* Icon */}
        <div
          className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full"
          style={{ background: "rgba(255,123,112,0.12)", border: "1px solid rgba(255,123,112,0.3)" }}
        >
          <ShieldAlert className="h-7 w-7 text-[#ff7b70]" />
        </div>

        <h2
          className="text-center text-[22px] font-bold text-white leading-tight"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          You are not alone
        </h2>
        <p className="mt-3 text-center text-[14px] leading-relaxed text-slate-400">
          It sounds like you may be going through something very difficult right now.
          Please reach out to one of these free, confidential support lines — trained
          counsellors are available right now.
        </p>

        {/* Helplines */}
        <div className="mt-6 space-y-2.5">
          {HELPLINES.map((h) => (
            <div
              key={h.number}
              className="flex items-center justify-between rounded-[14px] px-4 py-3"
              style={{
                background: "rgba(255,123,112,0.07)",
                border: "1px solid rgba(255,123,112,0.15)",
              }}
            >
              <div>
                <p className="text-[13px] font-medium text-white">{h.name}</p>
                {h.free && (
                  <p className="text-[10px] text-[#7be495]">Free call</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-3.5 w-3.5 text-[#ff7b70]" />
                <span className="text-[14px] font-semibold text-[#ff7b70]">{h.number}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Dismiss button */}
        <button
          type="button"
          disabled={!canDismiss}
          onClick={onDismiss}
          className="mt-6 w-full rounded-[12px] py-3 text-[13px] font-semibold transition-all duration-200 disabled:opacity-40"
          style={{
            background: canDismiss ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.1)",
            color: canDismiss ? "#fff" : "#64748b",
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
