import { BadgeCheck, Mail, Shield, TrendingUp, Activity, Brain } from "lucide-react";
import { PageHeader } from "../components/shared/PageHeader";
import { useAuth } from "../lib/auth";

export function ProfilePage() {
  const { user } = useAuth();
  const firstName = user?.name?.split(" ")[0] ?? "User";

  const mhi    = user?.latestMhi ?? null;
  const mhiColor =
    mhi === null ? "#94a3b8"
    : mhi >= 75  ? "#7be495"
    : mhi >= 55  ? "#ffc96b"
    :              "#ff7b70";

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Profile"
        title={`${firstName}'s workspace`}
        description="Your identity, well-being signals, and account details — all in one private place."
      />

      {/* ── TOP ROW: Identity + Stats ── */}
      <section className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">

        {/* Identity card */}
        <article
          className="rounded-[20px] p-5"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          {/* Avatar */}
          <div className="flex items-center gap-4">
            {user?.picture ? (
              <img
                src={user.picture}
                alt={user.name}
                className="h-16 w-16 rounded-[16px] object-cover"
              />
            ) : (
              <div
                className="flex h-16 w-16 shrink-0 items-center justify-center rounded-[16px] text-xl font-bold text-[#09111f]"
                style={{ background: "linear-gradient(135deg, #6ce3cf, #1b9db6)" }}
              >
                {firstName[0]}
              </div>
            )}
            <div className="min-w-0">
              <h3
                className="truncate text-[18px] font-bold text-white"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              >
                {user?.name ?? "User"}
              </h3>
              <p className="mt-0.5 truncate text-[12px] text-slate-500">{user?.email}</p>
            </div>
          </div>

          {/* Trust pills */}
          <div className="mt-5 space-y-2">
            {[
              { icon: <BadgeCheck className="h-3.5 w-3.5" />, label: "Verified account access",        color: "#6ce3cf" },
              { icon: <Shield     className="h-3.5 w-3.5" />, label: "Protected wellness workspace",   color: "#7be495" },
              { icon: <Mail       className="h-3.5 w-3.5" />, label: "History linked to this sign-in", color: "#a78bfa" },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2.5 rounded-[10px] px-3 py-2.5"
                style={{
                  background: `${item.color}08`,
                  border: `1px solid ${item.color}18`,
                }}
              >
                <span style={{ color: item.color }}>{item.icon}</span>
                <span className="text-[12px] text-slate-400">{item.label}</span>
              </div>
            ))}
          </div>
        </article>

        {/* Account snapshot */}
        <article
          className="rounded-[20px] p-5"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
            Account snapshot
          </p>
          <h3
            className="mt-1.5 text-[16px] font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Current profile details
          </h3>

          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {/* MHI — special treatment */}
            <div
              className="col-span-2 flex items-center gap-4 rounded-[14px] p-4 sm:col-span-2"
              style={{
                background: `${mhiColor}08`,
                border: `1px solid ${mhiColor}20`,
              }}
            >
              <TrendingUp className="h-5 w-5 shrink-0" style={{ color: mhiColor }} />
              <div>
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Latest MHI</p>
                <p
                  className="mt-1 text-[2rem] font-bold leading-none"
                  style={{ fontFamily: "'Space Grotesk', sans-serif", color: mhiColor }}
                >
                  {mhi ?? "—"}
                  {mhi !== null && (
                    <span className="ml-1 text-[13px] font-normal text-slate-500">/ 100</span>
                  )}
                </p>
              </div>
            </div>

            <StatTile label="PHQ-2"  value={`${user?.phq2 ?? "—"}`}  color="#ffc96b" />
            <StatTile label="GAD-2"  value={`${user?.gad2 ?? "—"}`}  color="#a78bfa" />
          </div>

          <div className="mt-3">
            <StatTile label="Contact email" value={user?.email ?? "—"} color="#6ce3cf" wide />
          </div>
        </article>
      </section>

      {/* ── BOTTOM ROW: Signals + Notes ── */}
      <section className="grid gap-4 xl:grid-cols-2">

        {/* Well-being signals */}
        <article
          className="rounded-[20px] p-5"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-[10px]"
              style={{ background: "rgba(108,227,207,0.1)" }}
            >
              <Activity className="h-4 w-4 text-[#6ce3cf]" />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                Profile signals
              </p>
              <h3
                className="text-[15px] font-semibold text-white"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              >
                What this workspace communicates
              </h3>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-3">
            {[
              { label: "Tone",      value: "Quiet",        color: "#6ce3cf" },
              { label: "Hierarchy", value: "Identity first", color: "#ffc96b" },
              { label: "Privacy",   value: "By default",    color: "#7be495" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-[12px] p-3 text-center"
                style={{
                  background: `${item.color}06`,
                  border: `1px solid ${item.color}15`,
                }}
              >
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-600">{item.label}</p>
                <p
                  className="mt-1.5 text-[13px] font-semibold"
                  style={{ color: item.color, fontFamily: "'Space Grotesk', sans-serif" }}
                >
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </article>

        {/* About this workspace */}
        <article
          className="rounded-[20px] p-5"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-[10px]"
              style={{ background: "rgba(167,139,250,0.1)" }}
            >
              <Brain className="h-4 w-4 text-[#a78bfa]" />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                About
              </p>
              <h3
                className="text-[15px] font-semibold text-white"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              >
                Your private well-being space
              </h3>
            </div>
          </div>

          <p className="mt-4 text-[13px] leading-relaxed text-slate-500">
            This workspace keeps your mental health history, assessment scores, and
            conversation records private and linked only to your Google account.
            Nothing is sold or shared. You can export or delete your data at any time.
          </p>

          <div
            className="mt-4 flex items-center gap-2.5 rounded-[12px] px-3 py-2.5"
            style={{ background: "rgba(123,228,149,0.06)", border: "1px solid rgba(123,228,149,0.14)" }}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#7be495]" style={{ boxShadow: "0 0 6px #7be495" }} />
            <p className="text-[12px] text-[#7be495]/80">Workspace is secure and active</p>
          </div>
        </article>
      </section>
    </div>
  );
}

function StatTile({
  label, value, color, wide = false,
}: {
  label: string; value: string; color: string; wide?: boolean;
}) {
  return (
    <div
      className={`rounded-[12px] p-3 ${wide ? "col-span-2" : ""}`}
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <p className="text-[10px] uppercase tracking-[0.18em] text-slate-600">{label}</p>
      <p
        className="mt-1.5 truncate text-[15px] font-semibold"
        style={{ fontFamily: "'Space Grotesk', sans-serif", color }}
      >
        {value}
      </p>
    </div>
  );
}