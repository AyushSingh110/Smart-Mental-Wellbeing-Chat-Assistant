import { Bell, Mic2, ShieldHalf, WandSparkles } from "lucide-react";

import { PageHeader } from "../components/shared/PageHeader";

const settingsGroups = [
  {
    title: "Privacy and access",
    icon: <ShieldHalf className="h-5 w-5" />,
    description:
      "Session retention, export controls, and account-linked authentication rules.",
    status: "Protected",
    helper: "Core privacy expectations are clearly framed for the user.",
  },
  {
    title: "Voice assistant",
    icon: <Mic2 className="h-5 w-5" />,
    description:
      "Speech preferences, preferred language, voice playback, and audio device behavior.",
    status: "Ready",
    helper: "Reserved space for future voice preferences without noisy controls today.",
  },
  {
    title: "Notifications",
    icon: <Bell className="h-5 w-5" />,
    description:
      "Gentle reminders for check-ins, progress summaries, and report readiness.",
    status: "Calm",
    helper: "Reminder language should stay supportive and low-pressure.",
  },
  {
    title: "AI behavior",
    icon: <WandSparkles className="h-5 w-5" />,
    description:
      "Tone preferences, follow-up depth, and future personalization controls.",
    status: "Thoughtful",
    helper: "Tone and follow-up depth can evolve without changing the current backend.",
  },
];

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Settings"
        title="A dedicated settings surface that feels intentional and uncluttered"
        description="Preferences are grouped by user need, with a calmer structure that avoids overwhelming people who may already be under stress."
      />

      <section className="grid gap-4 lg:grid-cols-2">
        {settingsGroups.map((group) => (
          <article
            key={group.title}
            className="surface-card animate-rise-in rounded-[28px] border border-white/10 p-6 shadow-halo"
          >
            <div className="inline-flex rounded-2xl bg-brand-400/12 p-3 text-brand-300">{group.icon}</div>
            <div className="mt-4 flex items-center justify-between gap-4">
              <h3 className="font-display text-xl font-semibold text-white">{group.title}</h3>
              <span className="rounded-full border border-white/10 px-3 py-1 text-sm text-slate-300">
                {group.status}
              </span>
            </div>
            <p className="mt-3 text-sm leading-7 text-slate-400">{group.description}</p>
            <div className="mt-6 rounded-[22px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
              {group.helper}
            </div>
          </article>
        ))}
      </section>

      <section className="surface-card animate-rise-in rounded-[28px] border border-white/10 p-6 shadow-halo">
        <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Design direction</p>
        <h3 className="mt-2 font-display text-xl font-semibold text-white">
          Principles behind this settings layout
        </h3>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <PrincipleCard
            title="Less cognitive load"
            description="Fewer moving parts and simpler labels make the page easier to process."
          />
          <PrincipleCard
            title="Honest states"
            description="The UI avoids fake controls that imply persistence where none exists yet."
          />
          <PrincipleCard
            title="Ready to extend"
            description="Visual structure is ready for future wiring without forcing backend changes now."
          />
        </div>
      </section>
    </div>
  );
}

function PrincipleCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <article className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
      <h4 className="font-display text-lg font-semibold text-white">{title}</h4>
      <p className="mt-2 text-sm leading-7 text-slate-400">{description}</p>
    </article>
  );
}
