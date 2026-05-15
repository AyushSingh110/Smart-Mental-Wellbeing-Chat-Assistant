import type { WellnessSnapshot } from "../../types";

type SessionPanelProps = {
  sessions: WellnessSnapshot["recentSessions"];
};

const MOOD_COLORS: Record<string, string> = {
  // Backend canonical emotion labels
  neutral:  "#7a92a8",
  stress:   "#b5822a",
  anxiety:  "#b5822a",
  sadness:  "#6a5acd",
  anger:    "#c04040",
  fear:     "#c04040",
  // Legacy / display labels (lowercase)
  calm:     "#4a84d6",
  happy:    "#3d8a5c",
  anxious:  "#b5822a",
  sad:      "#6a5acd",
};

function moodColor(mood: string): string {
  return MOOD_COLORS[mood.toLowerCase()] ?? "#7a92a8";
}

export function SessionPanel({ sessions }: SessionPanelProps) {
  return (
    <article
      className="flex flex-col rounded-2xl p-5"
      style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="label-caps">Recent sessions</p>
          <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Conversation snapshots
          </h3>
        </div>
        <div
          className="rounded-full px-3 py-1.5 text-[11px] font-medium"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(55,75,105,0.35)", color: "#4a6278" }}
        >
          {sessions.length} in view
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {sessions.length === 0 ? (
          <div className="py-8 text-center text-[13px]" style={{ color: "#4a6278" }}>
            No sessions yet — start a chat to see snapshots here.
          </div>
        ) : (
          sessions.map((s) => {
            const color = moodColor(s.mood);
            return (
              <div
                key={s.id}
                className="rounded-xl p-3.5 transition-all duration-150"
                style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.35)" }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.background = "rgba(74,132,214,0.06)";
                  (e.currentTarget as HTMLElement).style.border = "1px solid rgba(74,132,214,0.2)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.02)";
                  (e.currentTarget as HTMLElement).style.border = "1px solid rgba(55,75,105,0.35)";
                }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />
                    <p className="text-[12px] leading-relaxed line-clamp-2" style={{ color: "#c8d8ea" }}>
                      {s.summary}
                    </p>
                  </div>
                  <div
                    className="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold"
                    style={{ background: `${color}14`, color }}
                  >
                    {s.mhi}
                  </div>
                </div>

                <div className="mt-2 flex items-center gap-2.5 pl-4">
                  <span
                    className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                    style={{ background: `${color}12`, border: `1px solid ${color}28`, color }}
                  >
                    {s.mood}
                  </span>
                  <span className="text-[10px]" style={{ color: "#4a6278" }}>
                    {new Date(s.time).toLocaleDateString("en-IN", {
                      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </article>
  );
}
