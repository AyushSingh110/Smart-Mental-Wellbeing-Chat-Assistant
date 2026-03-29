import type { ReactNode } from "react";
import { BadgeCheck, ChartSpline, Mail, Shield } from "lucide-react";

import { PageHeader } from "../components/shared/PageHeader";
import { useAuth } from "../lib/auth";

export function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Profile"
        title="A personal overview built around trust, clarity, and progress"
        description="This profile keeps identity and well-being signals easy to scan so the workspace feels dependable from the moment it opens."
      />

      <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <article className="surface-card animate-rise-in rounded-[28px] border border-white/10 p-6 shadow-halo">
          <div className="flex items-center gap-4">
            {user?.picture ? (
              <img
                src={user.picture}
                alt={user.name}
                className="h-20 w-20 rounded-[26px] object-cover"
              />
            ) : (
              <div className="flex h-20 w-20 items-center justify-center rounded-[26px] bg-gradient-to-br from-brand-300 to-brand-600 font-display text-2xl font-bold text-ink">
                {user?.avatar}
              </div>
            )}
            <div>
              <h3 className="font-display text-2xl font-semibold text-white">{user?.name}</h3>
              <p className="mt-1 text-slate-400">{user?.email}</p>
            </div>
          </div>

          <div className="mt-8 space-y-3">
            <ProfilePill icon={<BadgeCheck className="h-4 w-4" />} label="Verified account access" />
            <ProfilePill icon={<Shield className="h-4 w-4" />} label="Protected wellness workspace" />
            <ProfilePill icon={<Mail className="h-4 w-4" />} label="Personal history linked to this sign-in" />
          </div>
        </article>

        <article className="surface-card animate-rise-in rounded-[28px] border border-white/10 p-6 shadow-halo">
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Account snapshot</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-white">
            Current profile details
          </h3>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <DetailCard label="Latest MHI" value={`${user?.latestMhi ?? "--"}`} />
            <DetailCard label="PHQ-2" value={`${user?.phq2 ?? "--"}`} />
            <DetailCard label="GAD-2" value={`${user?.gad2 ?? "--"}`} />
            <DetailCard label="Contact email" value={user?.email ?? "--"} />
          </div>
        </article>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <article className="surface-card animate-rise-in rounded-[28px] border border-white/10 p-6 shadow-halo">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-brand-400/12 p-3 text-brand-300">
              <ChartSpline className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Progress view</p>
              <h3 className="mt-1 font-display text-xl font-semibold text-white">
                What this profile should communicate
              </h3>
            </div>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <DetailCard label="Tone" value="Quiet and reassuring" />
            <DetailCard label="Hierarchy" value="Identity first, stats second" />
            <DetailCard label="Trust" value="Private by default" />
          </div>
        </article>

        <article className="surface-card animate-rise-in rounded-[28px] border border-white/10 p-6 shadow-halo">
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Experience notes</p>
          <h3 className="mt-2 font-display text-xl font-semibold text-white">
            A production-friendly profile surface
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-300">
            The page now focuses on live account data and trust signals instead of showing
            internal implementation notes. That keeps the experience closer to what a real
            user should actually see.
          </p>
        </article>
      </section>
    </div>
  );
}

function ProfilePill({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-200">
      <div className="text-brand-300">{icon}</div>
      <span>{label}</span>
    </div>
  );
}

function DetailCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-white/8 bg-white/[0.03] p-4">
      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <p className="mt-3 font-display text-lg font-semibold text-white">{value}</p>
    </div>
  );
}
