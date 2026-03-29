import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { HeartHandshake, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";

import { EmotionPanel }  from "../components/dashboard/EmotionPanel";
import { MetricCard }    from "../components/dashboard/MetricCard";
import { SessionPanel }  from "../components/dashboard/SessionPanel";
import { TrendPanel }    from "../components/dashboard/TrendPanel";
import { PageHeader }    from "../components/shared/PageHeader";
import { getDashboardSnapshot, getHealth, submitAssessment } from "../lib/api";
import { useAuth }       from "../lib/auth";
import type { WellnessSnapshot } from "../types";

export function DashboardPage() {
  const { token, refreshUser } = useAuth();
  const [snapshot, setSnapshot]               = useState<WellnessSnapshot | null>(null);
  const [apiHealthy, setApiHealthy]           = useState(false);
  const [phq2, setPhq2]                       = useState(0);
  const [gad2, setGad2]                       = useState(0);
  const [assessmentStatus, setAssessmentStatus] = useState("");

  useEffect(() => { void getHealth().then(setApiHealthy); }, []);

  useEffect(() => {
    if (!token) return;
    void getDashboardSnapshot(token).then((data) => {
      setSnapshot(data);
      setPhq2(data.assessment.phq2);
      setGad2(data.assessment.gad2);
    });
  }, [token]);

  async function handleAssessmentSubmit() {
    if (!token) return;
    setAssessmentStatus("Saving…");
    try {
      await submitAssessment(token, phq2, gad2);
      const refreshed = await getDashboardSnapshot(token);
      setSnapshot(refreshed);
      await refreshUser();
      setAssessmentStatus("Saved successfully.");
    } catch (err) {
      setAssessmentStatus(err instanceof Error ? err.message : "Could not save.");
    }
  }

  if (!snapshot) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-[#6ce3cf]" />
          <span className="text-sm">Loading dashboard…</span>
        </div>
      </div>
    );
  }

  const firstName = snapshot.displayName.split(" ")[0];

  const guidance =
    snapshot.latestMhi >= 75
      ? "The current pattern looks steady. Keep the rhythm gentle and consistent."
      : snapshot.latestMhi >= 55
        ? "There is enough stability to build on. A short check-in today can help keep momentum."
        : "The recent picture looks more delicate. Low-pressure support and shorter sessions may feel better.";

  return (
    <div className="space-y-4">

      {/* ── PAGE HEADER ─────────────────────────────────── */}
      <PageHeader
        eyebrow="Dashboard"
        title={`${firstName}, here is your latest well-being snapshot`}
        description="This overview turns history, assessments, and recent sessions into a calm summary that is easier to revisit regularly."
        actions={
          <div className="flex flex-wrap gap-2">
            <StatusBadge
              label={apiHealthy ? "Backend reachable" : "Backend offline"}
              color={apiHealthy ? "#6ce3cf" : "#ff7b70"}
            />
            <StatusBadge
              label={`${snapshot.category}`}
              color="#ffc96b"
            />
          </div>
        }
      />

      {/* ── METRIC CARDS ────────────────────────────────── */}
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Latest MHI"
          value={`${snapshot.latestMhi}`}
          detail="Most recent composite well-being score"
          accent="#45d5cf"
        />
        <MetricCard
          label="Weekly check-ins"
          value={`${snapshot.checkInsThisWeek}`}
          detail="Completed conversations this week"
          accent="#7be495"
        />
        <MetricCard
          label="Streak"
          value={`${snapshot.streakDays}d`}
          detail="Consistent check-ins build a clearer picture"
          accent="#ffc96b"
        />
        <MetricCard
          label="Voice mode"
          value={snapshot.voiceEnabled ? "On" : "Off"}
          detail="Current preference for voice-based support"
          accent="#ff7b70"
        />
      </section>

      {/* ── TREND + EMOTION ─────────────────────────────── */}
      <section className="grid gap-3 xl:grid-cols-[1.35fr_0.65fr]">
        <TrendPanel values={snapshot.weeklyTrend} />
        <EmotionPanel items={snapshot.emotionMix} />
      </section>

      {/* ── SESSIONS + ASSESSMENT ───────────────────────── */}
      <section className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
        <SessionPanel sessions={snapshot.recentSessions} />

        {/* Assessment card */}
        <article
          className="rounded-[20px] p-5"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                Assessment
              </p>
              <h3
                className="mt-1.5 text-[16px] font-semibold text-white"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              >
                PHQ-2 &amp; GAD-2 update
              </h3>
            </div>
            <div
              className="shrink-0 rounded-full px-3 py-1.5 text-[11px] text-slate-500"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              0 – 6 scale
            </div>
          </div>

          <div className="mt-5 space-y-4">
            <ScoreInput
              label="PHQ-2 total"
              helper="Interest and low mood total"
              value={phq2}
              onChange={setPhq2}
              color="#6ce3cf"
            />
            <ScoreInput
              label="GAD-2 total"
              helper="Nervousness and worry total"
              value={gad2}
              onChange={setGad2}
              color="#ffc96b"
            />

            <button
              type="button"
              onClick={() => void handleAssessmentSubmit()}
              className="w-full rounded-[12px] py-3 text-[13px] font-semibold text-[#09111f] transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
              style={{
                background: "linear-gradient(135deg, #6ce3cf 0%, #2cb8c7 100%)",
              }}
            >
              Save assessment
            </button>

            {assessmentStatus && (
              <p
                className="text-center text-[12px]"
                style={{ color: assessmentStatus.includes("success") || assessmentStatus === "Saved successfully." ? "#7be495" : "#ff7b70" }}
              >
                {assessmentStatus}
              </p>
            )}
          </div>
        </article>
      </section>

      {/* ── GUIDANCE + SUMMARY ──────────────────────────── */}
      <section className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">

        {/* Guidance */}
        <article
          className="rounded-[20px] p-5"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
            Guidance
          </p>
          <h3
            className="mt-1.5 text-[16px] font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Support cues for this week
          </h3>
          <div className="mt-4 space-y-3">
            <GuidanceRow
              icon={<Sparkles className="h-3.5 w-3.5" />}
              title="Best next step"
              text={guidance}
              color="#6ce3cf"
            />
            <GuidanceRow
              icon={<HeartHandshake className="h-3.5 w-3.5" />}
              title="Assessment rhythm"
              text={`PHQ-2 is ${snapshot.assessment.phq2} and GAD-2 is ${snapshot.assessment.gad2}. Keeping these updated sharpens the trend picture.`}
              color="#ffc96b"
            />
            <GuidanceRow
              icon={<ShieldCheck className="h-3.5 w-3.5" />}
              title="Session comfort"
              text="The interface keeps movement light so you can focus on support, not the screen itself."
              color="#7be495"
            />
          </div>
        </article>

        {/* Summary */}
        <article
          className="rounded-[20px] p-5"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
            Summary
          </p>
          <h3
            className="mt-1.5 text-[16px] font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Daily rhythm at a glance
          </h3>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <SummaryTile label="Display name"       value={snapshot.displayName} />
            <SummaryTile label="Check-ins this week" value={`${snapshot.checkInsThisWeek}`} />
            <SummaryTile label="Streak"             value={`${snapshot.streakDays} days`} />
            <SummaryTile
              label="Voice"
              value={snapshot.voiceEnabled ? "Enabled" : "Disabled"}
            />
          </div>

          {/* MHI ring indicator */}
          <div
            className="mt-4 flex items-center gap-4 rounded-[14px] p-4"
            style={{ background: "rgba(108,227,207,0.06)", border: "1px solid rgba(108,227,207,0.12)" }}
          >
            <TrendingUp className="h-4 w-4 shrink-0 text-[#6ce3cf]" />
            <div>
              <p className="text-[11px] text-slate-500">Current MHI score</p>
              <p
                className="text-[22px] font-bold text-white"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              >
                {snapshot.latestMhi}
                <span className="ml-1 text-[13px] font-normal text-slate-500">/ 100</span>
              </p>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────────── */

function StatusBadge({ label, color }: { label: string; color: string }) {
  return (
    <div
      className="rounded-full px-3 py-1.5 text-[11px] font-medium"
      style={{
        background: `${color}15`,
        border: `1px solid ${color}30`,
        color,
      }}
    >
      {label}
    </div>
  );
}

function ScoreInput({
  label, helper, value, onChange, color,
}: {
  label: string; helper: string; value: number;
  onChange: (v: number) => void; color: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div>
          <p className="text-[13px] font-medium text-white">{label}</p>
          <p className="text-[11px] text-slate-500">{helper}</p>
        </div>
        <span
          className="rounded-full px-2.5 py-1 text-[13px] font-semibold"
          style={{ background: `${color}15`, color }}
        >
          {value}
        </span>
      </div>
      <input
        type="range" min={0} max={6} step={1} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full cursor-pointer"
        style={{ accentColor: color }}
      />
    </div>
  );
}

function GuidanceRow({
  icon, title, text, color,
}: {
  icon: ReactNode; title: string; text: string; color: string;
}) {
  return (
    <div
      className="rounded-[14px] p-4"
      style={{ background: `${color}08`, border: `1px solid ${color}18` }}
    >
      <div className="flex items-center gap-2.5 text-[13px] font-semibold" style={{ color }}>
        {icon}
        {title}
      </div>
      <p className="mt-2 text-[12px] leading-relaxed text-slate-500">{text}</p>
    </div>
  );
}

function SummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="rounded-[12px] p-3"
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <p className="text-[10px] uppercase tracking-[0.18em] text-slate-600">{label}</p>
      <p
        className="mt-1.5 text-[14px] font-semibold text-white"
        style={{ fontFamily: "'Space Grotesk', sans-serif" }}
      >
        {value}
      </p>
    </div>
  );
}