import { BadgeCheck, Mail, Shield, TrendingUp, Activity, Brain } from "lucide-react";
import { useAuth } from "../lib/auth";

function getMhiColor(mhi: number | null): string {
  if (mhi === null) return "#7a92a8";
  if (mhi >= 75) return "#3d8a5c";
  if (mhi >= 55) return "#b5822a";
  return "#c04040";
}

export function ProfilePage() {
  const { user } = useAuth();
  const firstName = user?.name?.split(" ")[0] ?? "User";
  const mhi       = user?.latestMhi ?? null;
  const mhiColor  = getMhiColor(mhi);

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div>
        <p className="label-caps">Profile</p>
        <h1 className="mt-1.5 text-[20px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          {firstName}&apos;s workspace
        </h1>
        <p className="mt-1 text-[13px]" style={{ color: "#7a92a8" }}>
          Your identity, well-being signals, and account details — all in one place.
        </p>
      </div>

      {/* Top row */}
      <section className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">

        {/* Identity card */}
        <article className="rounded-2xl p-5" style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
          <div className="flex items-center gap-4">
            {user?.picture ? (
              <img src={user.picture} alt={user.name} className="h-16 w-16 rounded-2xl object-cover" />
            ) : (
              <div
                className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl text-xl font-bold text-white"
                style={{ background: "#4a84d6" }}
              >
                {firstName[0]}
              </div>
            )}
            <div className="min-w-0">
              <h3 className="truncate text-[18px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                {user?.name ?? "User"}
              </h3>
              <p className="mt-0.5 truncate text-[12px]" style={{ color: "#4a6278" }}>{user?.email}</p>
            </div>
          </div>

          <div className="mt-5 space-y-2">
            {[
              { icon: <BadgeCheck className="h-3.5 w-3.5" />, label: "Verified account access",        color: "#4a84d6" },
              { icon: <Shield     className="h-3.5 w-3.5" />, label: "Protected wellness workspace",   color: "#3d8a5c" },
              { icon: <Mail       className="h-3.5 w-3.5" />, label: "History linked to this sign-in", color: "#6a5acd" },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2.5 rounded-xl px-3 py-2.5"
                style={{ background: `${item.color}0a`, border: `1px solid ${item.color}20` }}
              >
                <span style={{ color: item.color }}>{item.icon}</span>
                <span className="text-[12px]" style={{ color: "#7a92a8" }}>{item.label}</span>
              </div>
            ))}
          </div>
        </article>

        {/* Account snapshot */}
        <article className="rounded-2xl p-5" style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
          <p className="label-caps">Account snapshot</p>
          <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Current profile details
          </h3>

          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {/* MHI tile */}
            <div
              className="col-span-2 flex items-center gap-4 rounded-xl p-4"
              style={{ background: `${mhiColor}0a`, border: `1px solid ${mhiColor}22` }}
            >
              <TrendingUp className="h-5 w-5 shrink-0" style={{ color: mhiColor }} />
              <div>
                <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: "#4a6278" }}>Latest MHI</p>
                <p className="mt-1 text-[2rem] font-bold leading-none" style={{ fontFamily: "'Space Grotesk', sans-serif", color: mhiColor }}>
                  {mhi ?? "—"}
                  {mhi !== null && <span className="ml-1 text-[13px] font-normal" style={{ color: "#4a6278" }}>/ 100</span>}
                </p>
              </div>
            </div>

            <StatTile label="PHQ-2"  value={`${user?.phq2 ?? "—"}`}  color="#b5822a" />
            <StatTile label="GAD-2"  value={`${user?.gad2 ?? "—"}`}  color="#6a5acd" />
          </div>

          <div className="mt-3">
            <StatTile label="Contact email" value={user?.email ?? "—"} color="#4a84d6" wide />
          </div>
        </article>
      </section>

      {/* Bottom row */}
      <section className="grid gap-4 xl:grid-cols-2">

        {/* Signals card */}
        <article className="rounded-2xl p-5" style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: "rgba(74,132,214,0.12)", border: "1px solid rgba(74,132,214,0.2)" }}>
              <Activity className="h-4 w-4" style={{ color: "#4a84d6" }} />
            </div>
            <div>
              <p className="label-caps">Profile signals</p>
              <h3 className="text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Workspace characteristics
              </h3>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            {[
              { label: "Tone",      value: "Clinical",      color: "#4a84d6" },
              { label: "Design",    value: "Minimal",       color: "#b5822a" },
              { label: "Privacy",   value: "By default",    color: "#3d8a5c" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-xl p-3 text-center"
                style={{ background: `${item.color}08`, border: `1px solid ${item.color}18` }}
              >
                <p className="text-[10px] uppercase tracking-[0.16em]" style={{ color: "#4a6278" }}>{item.label}</p>
                <p className="mt-1.5 text-[12px] font-semibold" style={{ color: item.color, fontFamily: "'Space Grotesk', sans-serif" }}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </article>

        {/* About card */}
        <article className="rounded-2xl p-5" style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: "rgba(106,90,205,0.12)", border: "1px solid rgba(106,90,205,0.2)" }}>
              <Brain className="h-4 w-4" style={{ color: "#6a5acd" }} />
            </div>
            <div>
              <p className="label-caps">About</p>
              <h3 className="text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Your private well-being space
              </h3>
            </div>
          </div>

          <p className="text-[13px] leading-relaxed" style={{ color: "#7a92a8" }}>
            This workspace keeps your mental health history, assessment scores, and
            conversation records private and linked only to your Google account.
            Nothing is sold or shared. You can export or delete your data at any time.
          </p>

          <div
            className="mt-4 flex items-center gap-2.5 rounded-xl px-3 py-2.5"
            style={{ background: "rgba(61,138,92,0.08)", border: "1px solid rgba(61,138,92,0.2)" }}
          >
            <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: "#3d8a5c" }} />
            <p className="text-[12px] font-medium" style={{ color: "#3d8a5c" }}>Workspace is secure and active</p>
          </div>
        </article>
      </section>
    </div>
  );
}

function StatTile({ label, value, color, wide = false }: {
  label: string; value: string; color: string; wide?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-3 ${wide ? "col-span-2" : ""}`}
      style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.35)" }}
    >
      <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: "#4a6278" }}>{label}</p>
      <p className="mt-1 truncate text-[14px] font-semibold" style={{ fontFamily: "'Space Grotesk', sans-serif", color }}>
        {value}
      </p>
    </div>
  );
}
