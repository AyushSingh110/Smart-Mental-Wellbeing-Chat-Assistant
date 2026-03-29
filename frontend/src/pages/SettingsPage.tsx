import { useState } from "react";
import { Bell, Mic2, ShieldHalf, WandSparkles, ChevronRight, Check } from "lucide-react";
import { PageHeader } from "../components/shared/PageHeader";

type ToggleState = Record<string, boolean>;

const SETTINGS_GROUPS = [
  {
    id:          "privacy",
    title:       "Privacy and access",
    icon:        ShieldHalf,
    description: "Session retention, export controls, and account-linked authentication rules.",
    status:      "Protected",
    statusColor: "#7be495",
    toggle: {
      label:   "Retain session history",
      default: true,
    },
  },
  {
    id:          "voice",
    title:       "Voice assistant",
    icon:        Mic2,
    description: "Speech preferences, preferred language, voice playback, and audio device behavior.",
    status:      "Ready",
    statusColor: "#6ce3cf",
    toggle: {
      label:   "Enable voice input",
      default: true,
    },
  },
  {
    id:          "notifications",
    title:       "Notifications",
    icon:        Bell,
    description: "Gentle reminders for check-ins, progress summaries, and report readiness.",
    status:      "Calm",
    statusColor: "#ffc96b",
    toggle: {
      label:   "Enable check-in reminders",
      default: false,
    },
  },
  {
    id:          "ai",
    title:       "AI behaviour",
    icon:        WandSparkles,
    description: "Tone preferences, follow-up depth, and future personalization controls.",
    status:      "Thoughtful",
    statusColor: "#a78bfa",
    toggle: {
      label:   "Adaptive tone responses",
      default: true,
    },
  },
] as const;

export function SettingsPage() {
  const [toggles, setToggles] = useState<ToggleState>(
    Object.fromEntries(SETTINGS_GROUPS.map((g) => [g.id, g.toggle.default])),
  );

  function flip(id: string) {
    setToggles((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Settings"
        title="Preferences and controls"
        description="Grouped by need, kept simple — so adjusting your workspace never adds stress."
      />

      {/* Settings cards */}
      <section className="grid gap-3 lg:grid-cols-2">
        {SETTINGS_GROUPS.map((group) => {
          const Icon    = group.icon;
          const isOn    = toggles[group.id];

          return (
            <article
              key={group.id}
              className="rounded-[20px] p-5 transition-all duration-200"
              style={{
                background: "rgba(255,255,255,0.028)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              {/* Header row */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px]"
                    style={{ background: `${group.statusColor}12` }}
                  >
                    <Icon className="h-4 w-4" style={{ color: group.statusColor }} />
                  </div>
                  <div>
                    <h3
                      className="text-[15px] font-semibold text-white"
                      style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                    >
                      {group.title}
                    </h3>
                    <span
                      className="text-[11px] font-medium"
                      style={{ color: group.statusColor }}
                    >
                      {group.status}
                    </span>
                  </div>
                </div>

                {/* Status dot */}
                <div
                  className="mt-1 h-2 w-2 shrink-0 rounded-full"
                  style={{
                    background: isOn ? group.statusColor : "rgba(255,255,255,0.1)",
                    boxShadow: isOn ? `0 0 6px ${group.statusColor}` : "none",
                    transition: "all 0.3s",
                  }}
                />
              </div>

              {/* Description */}
              <p className="mt-3 text-[12px] leading-relaxed text-slate-500">
                {group.description}
              </p>

              {/* Toggle row */}
              <div
                className="mt-4 flex items-center justify-between rounded-[12px] px-3 py-3"
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <span className="text-[12px] text-slate-400">{group.toggle.label}</span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={isOn}
                  onClick={() => flip(group.id)}
                  className="relative h-5 w-9 rounded-full transition-all duration-300 focus:outline-none"
                  style={{
                    background: isOn ? group.statusColor : "rgba(255,255,255,0.1)",
                  }}
                >
                  <span
                    className="absolute top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-white transition-all duration-300"
                    style={{ left: isOn ? "calc(100% - 18px)" : "2px" }}
                  >
                    {isOn && <Check className="h-2.5 w-2.5 text-[#09111f]" strokeWidth={3} />}
                  </span>
                </button>
              </div>
            </article>
          );
        })}
      </section>

      {/* Principles section */}
      <section
        className="rounded-[20px] p-5"
        style={{
          background: "rgba(255,255,255,0.022)",
          border: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
          Design principles
        </p>
        <h3
          className="mt-1.5 text-[16px] font-semibold text-white"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          How this settings page is built
        </h3>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            {
              title: "Less cognitive load",
              text:  "Fewer moving parts and simpler labels make the page easier to process.",
              color: "#6ce3cf",
            },
            {
              title: "Honest states",
              text:  "Controls show real state and avoid fake toggles that don't persist yet.",
              color: "#ffc96b",
            },
            {
              title: "Ready to extend",
              text:  "Structure is ready for future wiring without forcing backend changes now.",
              color: "#a78bfa",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-[14px] p-4"
              style={{
                background: `${item.color}06`,
                border: `1px solid ${item.color}14`,
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <ChevronRight className="h-3.5 w-3.5" style={{ color: item.color }} />
                <p
                  className="text-[13px] font-semibold"
                  style={{ fontFamily: "'Space Grotesk', sans-serif", color: item.color }}
                >
                  {item.title}
                </p>
              </div>
              <p className="text-[12px] leading-relaxed text-slate-500">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Danger zone */}
      <section
        className="rounded-[20px] p-5"
        style={{
          background: "rgba(255,123,112,0.04)",
          border: "1px solid rgba(255,123,112,0.12)",
        }}
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#ff7b70]/60">
          Account actions
        </p>
        <h3
          className="mt-1.5 text-[15px] font-semibold text-white"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          Data and account
        </h3>
        <p className="mt-2 text-[12px] leading-relaxed text-slate-500">
          Export your full history or permanently delete your account and all associated data.
          These actions cannot be undone.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-[10px] px-4 py-2 text-[12px] font-medium text-slate-400 transition-all hover:text-white"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            Export my data
          </button>
          <button
            type="button"
            className="rounded-[10px] px-4 py-2 text-[12px] font-medium text-[#ff7b70]/80 transition-all hover:text-[#ff7b70]"
            style={{ background: "rgba(255,123,112,0.06)", border: "1px solid rgba(255,123,112,0.16)" }}
          >
            Delete account
          </button>
        </div>
      </section>
    </div>
  );
}