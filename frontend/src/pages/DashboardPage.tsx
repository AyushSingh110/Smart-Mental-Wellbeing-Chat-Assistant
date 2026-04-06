import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import {
  Download, HeartHandshake, ShieldCheck, Sparkles, TrendingUp,
  AlertTriangle, Brain,
} from "lucide-react";

import { CBTPanel }         from "../components/cbt/CBTPanel";
import { EmotionPanel }     from "../components/dashboard/EmotionPanel";
import { MetricCard }       from "../components/dashboard/MetricCard";
import { SessionPanel }     from "../components/dashboard/SessionPanel";
import { TrendPanel }       from "../components/dashboard/TrendPanel";
import { PageHeader }       from "../components/shared/PageHeader";
import {
  getCrisisHistory, getDashboardSnapshot, getHealth,
  getMoodJournal, submitAssessment,
} from "../lib/api";
import { useAuth }          from "../lib/auth";
import type { WellnessSnapshot } from "../types";
import { CBT_LABELS }       from "../types";

export function DashboardPage() {
  const { token, refreshUser }                       = useAuth();
  const [snapshot, setSnapshot]                      = useState<WellnessSnapshot | null>(null);
  const [apiHealthy, setApiHealthy]                  = useState(false);
  const [phq2, setPhq2]                              = useState(0);
  const [gad2, setGad2]                              = useState(0);
  const [assessmentStatus, setAssessmentStatus]      = useState("");
  const [activeTab, setActiveTab]                    = useState<"overview" | "cbt" | "crisis">("overview");
  const [crisisEvents, setCrisisEvents]              = useState<Array<{
    timestamp: string; crisis_tier: string; crisis_score: number; message_snippet: string;
  }>>([]);
  const [moodEntries, setMoodEntries]                = useState<Array<{ timestamp: string; mood_rating: number; notes: string }>>([]);
  const prevMhiRef                                   = useRef<number | null>(null);
  const mhiRef                                       = useRef<HTMLSpanElement | null>(null);

  useEffect(() => { void getHealth().then(setApiHealthy); }, []);

  useEffect(() => {
    if (!token) return;
    void getDashboardSnapshot(token).then((data) => {
      setSnapshot(data);
      setPhq2(data.assessment.phq2);
      setGad2(data.assessment.gad2);
    });
    void getCrisisHistory(token).then((d) => setCrisisEvents(d.events));
    void getMoodJournal(token).then((d) => setMoodEntries(d.entries.slice(0, 14)));
  }, [token]);

  // Animate MHI needle when value changes
  useEffect(() => {
    if (!snapshot || !mhiRef.current) return;
    const el = mhiRef.current;
    if (prevMhiRef.current !== null && prevMhiRef.current !== snapshot.latestMhi) {
      el.style.transition = "color 0.8s ease";
      el.style.transform = "scale(1.15)";
      setTimeout(() => { if (el) el.style.transform = "scale(1)"; }, 800);
    }
    prevMhiRef.current = snapshot.latestMhi;
  }, [snapshot?.latestMhi]);

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

  function exportCSV() {
    if (!snapshot) return;
    const rows = [
      ["Timestamp", "Message", "MHI", "Mood"],
      ...snapshot.recentSessions.map((s) => [
        s.time, `"${s.summary.replace(/"/g, '""')}"`, s.mhi, s.mood,
      ]),
    ];
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "wellbeing_sessions.csv";
    a.click();
    URL.revokeObjectURL(url);
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

  const TABS = [
    { id: "overview", label: "Overview" },
    { id: "cbt",      label: "Self-Help Tools" },
    { id: "crisis",   label: "Crisis History" },
  ] as const;

  return (
    <div className="space-y-4">

      {/* PAGE HEADER */}
      <PageHeader
        eyebrow="Dashboard"
        title={`${firstName}, here is your latest well-being snapshot`}
        description="This overview turns history, assessments, and recent sessions into a calm summary."
        actions={
          <div className="flex flex-wrap gap-2">
            <StatusBadge label={apiHealthy ? "Backend reachable" : "Backend offline"} color={apiHealthy ? "#6ce3cf" : "#ff7b70"} />
            <StatusBadge label={`${snapshot.category}`} color="#ffc96b" />
            <button
              type="button"
              onClick={exportCSV}
              className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-medium transition-all hover:opacity-80"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#94a3b8" }}
            >
              <Download className="h-3 w-3" />
              Export CSV
            </button>
          </div>
        }
      />

      {/* TABS */}
      <div
        className="flex gap-1 rounded-[14px] p-1"
        style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className="flex-1 rounded-[10px] py-2 text-[12px] font-medium transition-all duration-200"
            style={{
              background: activeTab === tab.id ? "rgba(108,227,207,0.12)" : "transparent",
              color: activeTab === tab.id ? "#6ce3cf" : "#64748b",
              border: activeTab === tab.id ? "1px solid rgba(108,227,207,0.2)" : "1px solid transparent",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ─────────────────────────────────── */}
      {activeTab === "overview" && (
        <div className="space-y-4 animate-fadeIn">

          {/* METRIC CARDS */}
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Latest MHI"        value={`${snapshot.latestMhi}`}        detail="Most recent composite well-being score"       accent="#45d5cf" />
            <MetricCard label="Weekly check-ins"  value={`${snapshot.checkInsThisWeek}`} detail="Completed conversations this week"             accent="#7be495" />
            <MetricCard label="Streak"            value={`${snapshot.streakDays}d`}       detail="Consistent check-ins build a clearer picture" accent="#ffc96b" />
            <MetricCard label="Voice mode"        value={snapshot.voiceEnabled ? "On" : "Off"} detail="Current preference for voice-based support" accent="#ff7b70" />
          </section>

          {/* TREND + EMOTION */}
          <section className="grid gap-3 xl:grid-cols-[1.35fr_0.65fr]">
            <TrendPanel values={snapshot.weeklyTrend} />
            <EmotionPanel items={snapshot.emotionMix} />
          </section>

          {/* Mood Trend chart (from mood journal) */}
          {moodEntries.length > 0 && (
            <section>
              <MoodTrendChart entries={moodEntries} />
            </section>
          )}

          {/* SESSIONS + ASSESSMENT */}
          <section className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
            <SessionPanel sessions={snapshot.recentSessions} />

            <article
              className="rounded-[20px] p-5"
              style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Assessment</p>
                  <h3 className="mt-1.5 text-[16px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    PHQ-2 &amp; GAD-2 update
                  </h3>
                </div>
                <div className="shrink-0 rounded-full px-3 py-1.5 text-[11px] text-slate-500"
                  style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}>
                  0 – 6 scale
                </div>
              </div>

              <div className="mt-5 space-y-4">
                <ScoreInput label="PHQ-2 total"    helper="Interest and low mood total" value={phq2} onChange={setPhq2} color="#6ce3cf" />
                <ScoreInput label="GAD-2 total"    helper="Nervousness and worry total" value={gad2} onChange={setGad2} color="#ffc96b" />
                <button type="button" onClick={() => void handleAssessmentSubmit()}
                  className="w-full rounded-[12px] py-3 text-[13px] font-semibold text-[#09111f] transition-all hover:opacity-90"
                  style={{ background: "linear-gradient(135deg, #6ce3cf 0%, #2cb8c7 100%)" }}>
                  Save assessment
                </button>
                {assessmentStatus && (
                  <p className="text-center text-[12px]"
                    style={{ color: assessmentStatus.includes("success") || assessmentStatus === "Saved successfully." ? "#7be495" : "#ff7b70" }}>
                    {assessmentStatus}
                  </p>
                )}
              </div>
            </article>
          </section>

          {/* SESSION SUMMARY + GUIDANCE */}
          <section className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">

            <article className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Guidance</p>
              <h3 className="mt-1.5 text-[16px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Support cues for this week
              </h3>
              <div className="mt-4 space-y-3">
                <GuidanceRow icon={<Sparkles className="h-3.5 w-3.5" />}       title="Best next step"        text={guidance}  color="#6ce3cf" />
                <GuidanceRow icon={<HeartHandshake className="h-3.5 w-3.5" />} title="Assessment rhythm"     text={`PHQ-2 is ${snapshot.assessment.phq2} and GAD-2 is ${snapshot.assessment.gad2}. Keeping these updated sharpens the trend picture.`} color="#ffc96b" />
                <GuidanceRow icon={<ShieldCheck className="h-3.5 w-3.5" />}    title="Session comfort"       text="The interface keeps movement light so you can focus on support, not the screen itself." color="#7be495" />
              </div>
            </article>

            <article className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Summary</p>
              <h3 className="mt-1.5 text-[16px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Daily rhythm at a glance
              </h3>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <SummaryTile label="Display name"        value={snapshot.displayName} />
                <SummaryTile label="Check-ins this week" value={`${snapshot.checkInsThisWeek}`} />
                <SummaryTile label="Streak"              value={`${snapshot.streakDays} days`} />
                <SummaryTile label="Languages used"      value={(snapshot.sessionSummary?.languagesUsed ?? ["en"]).join(", ").toUpperCase()} />
              </div>

              {/* Animated MHI indicator */}
              <div className="mt-4 flex items-center gap-4 rounded-[14px] p-4"
                style={{ background: "rgba(108,227,207,0.06)", border: "1px solid rgba(108,227,207,0.12)" }}>
                <TrendingUp className="h-4 w-4 shrink-0 text-[#6ce3cf]" />
                <div>
                  <p className="text-[11px] text-slate-500">Current MHI score</p>
                  <p className="text-[22px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    <span ref={mhiRef} style={{ display: "inline-block", transition: "transform 0.4s ease" }}>
                      {snapshot.latestMhi}
                    </span>
                    <span className="ml-1 text-[13px] font-normal text-slate-500">/ 100</span>
                  </p>
                </div>
              </div>
            </article>
          </section>

          {/* MHI Gauge + CBT + Behavioral signals row */}
          <section className="grid gap-3 xl:grid-cols-3">
            {/* SVG MHI Gauge */}
            <article className="rounded-[20px] p-5 flex flex-col items-center"
              style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500 mb-1 self-start">MHI Gauge</p>
              <h3 className="mb-3 text-[14px] font-semibold text-white self-start" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Well-being Index
              </h3>
              <MHIGauge mhi={snapshot.latestMhi} />
              <p className="mt-2 text-[13px] font-semibold" style={{ color: getMhiBandColor(snapshot.latestMhi) }}>
                {snapshot.category}
              </p>
            </article>

            {/* CBT Engagement */}
            <article className="rounded-[20px] p-5"
              style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
              <div className="flex items-center gap-2 mb-3">
                <Brain className="h-4 w-4 text-[#a78bfa]" />
                <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">CBT Engagement</p>
              </div>
              {snapshot.cbtCounts && Object.keys(snapshot.cbtCounts).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(snapshot.cbtCounts).slice(0, 5).map(([t, count]) => (
                    <div key={t} className="flex items-center justify-between rounded-[10px] px-3 py-2"
                      style={{ background: "rgba(167,139,250,0.06)", border: "1px solid rgba(167,139,250,0.14)" }}>
                      <span className="text-[12px] font-medium text-[#a78bfa]">{CBT_LABELS[t] ?? t}</span>
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 rounded-full" style={{
                          width: Math.min(40 + count * 8, 80),
                          background: "linear-gradient(90deg, #a78bfa, #7c3aed)",
                          opacity: 0.7,
                        }} />
                        <span className="text-[10px] text-slate-500">×{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[13px] text-slate-500 py-6 text-center">
                  No CBT sessions recorded yet.
                </p>
              )}
            </article>

            {/* Crisis Events count card */}
            <article className="rounded-[20px] p-5"
              style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-4 w-4 text-[#ff7b70]" />
                <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Crisis Events</p>
              </div>
              <div className="flex flex-col items-center justify-center py-4">
                <p className="text-[42px] font-bold" style={{ fontFamily: "'Space Grotesk', sans-serif", color: crisisEvents.length === 0 ? "#7be495" : "#ff7b70" }}>
                  {crisisEvents.length}
                </p>
                <p className="text-[12px] text-slate-500 mt-1">
                  {crisisEvents.length === 0 ? "No events recorded" : "events in history"}
                </p>
              </div>
              {crisisEvents.length > 0 && (
                <div className="space-y-1.5 mt-2">
                  {crisisEvents.slice(0, 3).map((ev, i) => {
                    const c = ev.crisis_tier === "active" ? "#ff7b70" : "#ffc96b";
                    return (
                      <div key={i} className="flex items-center gap-2 rounded-[10px] px-3 py-2"
                        style={{ background: `${c}08`, border: `1px solid ${c}20` }}>
                        <div className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: c }} />
                        <span className="text-[11px] capitalize font-medium" style={{ color: c }}>{ev.crisis_tier}</span>
                        <span className="text-[10px] text-slate-600 ml-auto">
                          {new Date(ev.timestamp).toLocaleDateString([], { month: "short", day: "numeric" })}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </article>
          </section>
        </div>
      )}

      {/* ── SELF-HELP TOOLS TAB ──────────────────────────── */}
      {activeTab === "cbt" && (
        <div className="animate-fadeIn">
          <article className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500 mb-1">Self-Help Tools</p>
            <h3 className="mb-5 text-[16px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              CBT Techniques &amp; Exercises
            </h3>
            <CBTPanel />
          </article>
        </div>
      )}

      {/* ── CRISIS HISTORY TAB ───────────────────────────── */}
      {activeTab === "crisis" && (
        <div className="animate-fadeIn">
          <article className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-4 w-4 text-[#ff7b70]" />
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Crisis History</p>
            </div>
            <h3 className="mb-5 text-[16px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Past crisis event timeline
            </h3>

            {crisisEvents.length === 0 ? (
              <div className="py-10 text-center text-slate-500 text-[13px]">
                No crisis events recorded — that is a good sign.
              </div>
            ) : (
              <div className="space-y-3">
                {crisisEvents.map((ev, i) => {
                  const tierColor = ev.crisis_tier === "active" ? "#ff7b70" : ev.crisis_tier === "passive" ? "#ffc96b" : "#94a3b8";
                  return (
                    <div key={i} className="flex items-start gap-3 rounded-[14px] p-4"
                      style={{ background: `${tierColor}08`, border: `1px solid ${tierColor}20` }}>
                      <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full" style={{ background: tierColor }} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[11px] font-semibold capitalize" style={{ color: tierColor }}>
                            {ev.crisis_tier} crisis
                          </span>
                          <span className="text-[10px] text-slate-600">
                            {new Date(ev.timestamp).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                          </span>
                        </div>
                        <p className="mt-1 text-[12px] text-slate-400 leading-relaxed">{ev.message_snippet}</p>
                        <p className="mt-1 text-[10px] text-slate-600">
                          Score: {(ev.crisis_score * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </article>
        </div>
      )}
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────── */

function StatusBadge({ label, color }: { label: string; color: string }) {
  return (
    <div className="rounded-full px-3 py-1.5 text-[11px] font-medium"
      style={{ background: `${color}15`, border: `1px solid ${color}30`, color }}>
      {label}
    </div>
  );
}

function ScoreInput({ label, helper, value, onChange, color }: {
  label: string; helper: string; value: number; onChange: (v: number) => void; color: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div>
          <p className="text-[13px] font-medium text-white">{label}</p>
          <p className="text-[11px] text-slate-500">{helper}</p>
        </div>
        <span className="rounded-full px-2.5 py-1 text-[13px] font-semibold" style={{ background: `${color}15`, color }}>
          {value}
        </span>
      </div>
      <input type="range" min={0} max={6} step={1} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full cursor-pointer" style={{ accentColor: color }} />
    </div>
  );
}

function GuidanceRow({ icon, title, text, color }: { icon: ReactNode; title: string; text: string; color: string }) {
  return (
    <div className="rounded-[14px] p-4" style={{ background: `${color}08`, border: `1px solid ${color}18` }}>
      <div className="flex items-center gap-2.5 text-[13px] font-semibold" style={{ color }}>
        {icon}{title}
      </div>
      <p className="mt-2 text-[12px] leading-relaxed text-slate-500">{text}</p>
    </div>
  );
}

function SummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[12px] p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
      <p className="text-[10px] uppercase tracking-[0.18em] text-slate-600">{label}</p>
      <p className="mt-1.5 text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>{value}</p>
    </div>
  );
}

// ── 7-band MHI color lookup
const _MHI_BANDS: Array<{ min: number; color: string; label: string }> = [
  { min: 88, color: "#7be495", label: "Flourishing" },
  { min: 75, color: "#6ce3cf", label: "Stable" },
  { min: 62, color: "#45d5cf", label: "Mild Stress" },
  { min: 48, color: "#ffc96b", label: "Moderate Distress" },
  { min: 34, color: "#f97316", label: "High Risk" },
  { min: 18, color: "#ef4444", label: "Severe Risk" },
  { min:  0, color: "#ff7b70", label: "Crisis Risk" },
];

function getMhiBandColor(mhi: number): string {
  for (const band of _MHI_BANDS) {
    if (mhi >= band.min) return band.color;
  }
  return "#ff7b70";
}

// ── SVG semicircle MHI Gauge with 7 colored arcs + animated needle
function MHIGauge({ mhi }: { mhi: number }) {
  const cx = 100, cy = 100, r = 80;
  const startAngle = 180;  // left
  const endAngle   = 360;  // right (semicircle going through bottom)
  const totalDeg   = 180;

  // Helper: polar → cartesian
  function polar(deg: number, radius = r) {
    const rad = (deg * Math.PI) / 180;
    return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) };
  }

  // Helper: arc path from deg1 to deg2
  function arcPath(deg1: number, deg2: number, outerR: number, innerR: number): string {
    const o1 = polar(deg1, outerR), o2 = polar(deg2, outerR);
    const i1 = polar(deg1, innerR), i2 = polar(deg2, innerR);
    const large = deg2 - deg1 > 180 ? 1 : 0;
    return [
      `M ${o1.x} ${o1.y}`,
      `A ${outerR} ${outerR} 0 ${large} 1 ${o2.x} ${o2.y}`,
      `L ${i2.x} ${i2.y}`,
      `A ${innerR} ${innerR} 0 ${large} 0 ${i1.x} ${i1.y}`,
      "Z",
    ].join(" ");
  }

  // Band arc slices: 7 bands, each covers totalDeg/7 degrees
  const bandDeg = totalDeg / 7;
  const bands = _MHI_BANDS.map((band, i) => ({
    ...band,
    deg1: startAngle + i * bandDeg,
    deg2: startAngle + (i + 1) * bandDeg,
  }));

  // Needle angle: MHI 0 → 180°, MHI 100 → 360°
  const needleAngle = startAngle + ((mhi / 100) * totalDeg);
  const needleTip   = polar(needleAngle, 65);
  const needleBase1 = polar(needleAngle + 90, 6);
  const needleBase2 = polar(needleAngle - 90, 6);
  const mhiColor    = getMhiBandColor(mhi);

  return (
    <svg viewBox="0 0 200 110" style={{ width: "100%", maxWidth: 200, height: "auto" }}>
      {/* Band arcs */}
      {bands.map((band, i) => (
        <path
          key={i}
          d={arcPath(band.deg1, band.deg2, 82, 62)}
          fill={band.color}
          opacity={0.85}
        />
      ))}

      {/* Track ring */}
      <path
        d={arcPath(startAngle, endAngle, 84, 60)}
        fill="none"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth={1}
      />

      {/* Needle */}
      <polygon
        points={`${needleTip.x},${needleTip.y} ${needleBase1.x},${needleBase1.y} ${needleBase2.x},${needleBase2.y}`}
        fill={mhiColor}
        opacity={0.95}
        style={{ transition: "all 1s ease", filter: `drop-shadow(0 0 4px ${mhiColor}80)` }}
      />

      {/* Center hub */}
      <circle cx={cx} cy={cy} r={7} fill="#1f2e48" stroke={mhiColor} strokeWidth={2} />

      {/* MHI value text */}
      <text x={cx} y={cy - 14} textAnchor="middle" fontSize={22} fontWeight="bold"
        fill="white" fontFamily="Space Grotesk, sans-serif"
        style={{ transition: "all 1s ease" }}>
        {mhi}
      </text>

      {/* Min / Max labels */}
      <text x={startAngle === 180 ? 16 : 16} y={104} fontSize={9} fill="#64748b" textAnchor="middle">0</text>
      <text x={184} y={104} fontSize={9} fill="#64748b" textAnchor="middle">100</text>
    </svg>
  );
}

function MoodTrendChart({ entries }: { entries: Array<{ timestamp: string; mood_rating: number }> }) {
  const sorted = [...entries].reverse();
  const max = 10, min = 1;
  const w = 600, h = 100;
  const padX = 20, padY = 10;
  const points = sorted.map((e, i) => {
    const x = padX + (i / Math.max(sorted.length - 1, 1)) * (w - padX * 2);
    const y = h - padY - ((e.mood_rating - min) / (max - min)) * (h - padY * 2);
    return `${x},${y}`;
  }).join(" ");

  return (
    <article className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Mood Journal</p>
      <h3 className="mt-1.5 text-[16px] font-semibold text-white mb-4" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        Mood trend ({sorted.length} entries)
      </h3>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ minWidth: 260, height: 80 }}>
          <defs>
            <linearGradient id="moodGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ffc96b" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#ffc96b" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          {sorted.length > 1 && (
            <polyline fill="none" stroke="#ffc96b" strokeWidth="2" strokeLinejoin="round" points={points} />
          )}
          {sorted.map((e, i) => {
            const x = padX + (i / Math.max(sorted.length - 1, 1)) * (w - padX * 2);
            const y = h - padY - ((e.mood_rating - min) / (max - min)) * (h - padY * 2);
            return <circle key={i} cx={x} cy={y} r={3} fill="#ffc96b" />;
          })}
        </svg>
      </div>
      <div className="flex justify-between text-[10px] text-slate-600 mt-1">
        <span>Oldest</span><span>Latest</span>
      </div>
    </article>
  );
}
