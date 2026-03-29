import type { WellnessSnapshot } from "../../types";

type SessionPanelProps = {
  sessions: WellnessSnapshot["recentSessions"];
};

const MOOD_COLORS: Record<string, string> = {
  calm:      "#6ce3cf",
  happy:     "#7be495",
  anxious:   "#ffc96b",
  sad:       "#a78bfa",
  frustrated:"#ff7b70",
  neutral:   "#94a3b8",
};

function moodColor(mood: string) {
  const key = mood.toLowerCase();
  return MOOD_COLORS[key] ?? "#94a3b8";
}

export function SessionPanel({ sessions }: SessionPanelProps) {
  return (
    <article
      className="flex flex-col rounded-[20px] p-5"
      style={{
        background: "rgba(255,255,255,0.028)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
            Recent sessions
          </p>
          <h3
            className="mt-1.5 text-[16px] font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Conversation snapshots
          </h3>
        </div>
        <div
          className="rounded-full px-3 py-1.5 text-[11px] text-slate-400"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          {sessions.length} in view
        </div>
      </div>

      {/* Sessions */}
      <div className="mt-5 space-y-2">
        {sessions.length === 0 ? (
          <div className="py-8 text-center text-[13px] text-slate-600">
            No sessions yet — start a chat to see snapshots here.
          </div>
        ) : (
          sessions.map((s) => {
            const color = moodColor(s.mood);
            return (
              <div
                key={s.id}
                className="group rounded-[14px] p-4 transition-all duration-200"
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.05)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
                  (e.currentTarget as HTMLElement).style.border = `1px solid ${color}25`;
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.02)";
                  (e.currentTarget as HTMLElement).style.border = "1px solid rgba(255,255,255,0.05)";
                }}
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Left — mood dot + summary */}
                  <div className="flex items-start gap-3">
                    <div
                      className="mt-1 h-2 w-2 shrink-0 rounded-full"
                      style={{ background: color, boxShadow: `0 0 6px ${color}` }}
                    />
                    <p className="text-[13px] leading-relaxed text-slate-300 line-clamp-2">
                      {s.summary}
                    </p>
                  </div>

                  {/* Right — MHI badge */}
                  <div
                    className="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold"
                    style={{ background: `${color}15`, color }}
                  >
                    {s.mhi}
                  </div>
                </div>

                <div className="mt-2.5 flex items-center gap-3 pl-5">
                  <span
                    className="rounded-full px-2.5 py-0.5 text-[10px] font-medium"
                    style={{
                      background: `${color}12`,
                      border: `1px solid ${color}25`,
                      color,
                    }}
                  >
                    {s.mood}
                  </span>
                  <span className="text-[11px] text-slate-600">
                    {new Date(s.time).toLocaleDateString("en-IN", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
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