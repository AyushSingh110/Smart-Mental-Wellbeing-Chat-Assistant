import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle, Brain, Download, HeartHandshake,
  ShieldCheck, Sparkles, TrendingUp,
} from "lucide-react";

import { CBTPanel }     from "../components/cbt/CBTPanel";
import { EmotionPanel } from "../components/dashboard/EmotionPanel";
import { MetricCard }   from "../components/dashboard/MetricCard";
import { SessionPanel } from "../components/dashboard/SessionPanel";
import { TrendPanel }   from "../components/dashboard/TrendPanel";
import {
  getCrisisHistory, getDashboardSnapshot, getHealth, getMoodJournal, submitAssessment,
} from "../lib/api";
import { useAuth }      from "../lib/auth";
import type { WellnessSnapshot } from "../types";
import { CBT_LABELS }   from "../types";

// ── MHI band colour map (muted clinical palette)
const MHI_BANDS: Array<{ min: number; color: string; label: string }> = [
  { min: 88, color: "#3d8a5c", label: "Flourishing"       },
  { min: 75, color: "#4a84d6", label: "Stable"            },
  { min: 62, color: "#6a7fb8", label: "Mild Stress"       },
  { min: 48, color: "#b5822a", label: "Moderate Distress" },
  { min: 34, color: "#b06030", label: "High Risk"         },
  { min: 18, color: "#c04040", label: "Severe Risk"       },
  { min:  0, color: "#943030", label: "Crisis Risk"       },
];

function getMhiColor(mhi: number): string {
  for (const band of MHI_BANDS) {
    if (mhi >= band.min) return band.color;
  }
  return "#943030";
}

export function DashboardPage() {
  const { token, refreshUser }                   = useAuth();
  const [snapshot, setSnapshot]                  = useState<WellnessSnapshot | null>(null);
  const [apiHealthy, setApiHealthy]              = useState(false);
  const [phq2, setPhq2]                          = useState(0);
  const [gad2, setGad2]                          = useState(0);
  const [assessmentStatus, setAssessmentStatus]  = useState("");
  const [activeTab, setActiveTab]                = useState<"overview" | "cbt" | "crisis">("overview");
  const [crisisEvents, setCrisisEvents]          = useState<Array<{
    timestamp: string; crisis_tier: string; crisis_score: number; message_snippet: string;
  }>>([]);
  const [moodEntries, setMoodEntries] = useState<Array<{ timestamp: string; mood_rating: number; notes: string }>>([]);
  const prevMhiRef = useRef<number | null>(null);
  const mhiRef     = useRef<HTMLSpanElement | null>(null);

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

  useEffect(() => {
    if (!snapshot || !mhiRef.current) return;
    const el = mhiRef.current;
    if (prevMhiRef.current !== null && prevMhiRef.current !== snapshot.latestMhi) {
      el.style.transition = "transform 0.6s ease";
      el.style.transform  = "scale(1.12)";
      setTimeout(() => { if (el) el.style.transform = "scale(1)"; }, 600);
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
    const csv  = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = "wellbeing_sessions.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!snapshot) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex items-center gap-3" style={{ color: "#4a6278" }}>
          <span className="h-4 w-4 rounded-full border-2 animate-spinSlow"
            style={{ borderColor: "rgba(74,132,214,0.2)", borderTopColor: "#4a84d6" }} />
          <span className="text-[13px]">Loading dashboard…</span>
        </div>
      </div>
    );
  }

  const firstName = snapshot.displayName.split(" ")[0];
  const mhiColor  = getMhiColor(snapshot.latestMhi);

  const guidance =
    snapshot.latestMhi >= 75
      ? "The current pattern looks steady. Keep the rhythm gentle and consistent."
      : snapshot.latestMhi >= 55
        ? "There is enough stability to build on. A short check-in today can help keep momentum."
        : "The recent picture looks more delicate. Low-pressure support and shorter sessions may feel better.";

  const TABS = [
    { id: "overview", label: "Overview"        },
    { id: "cbt",      label: "Self-Help Tools" },
    { id: "crisis",   label: "Crisis History"  },
  ] as const;

  return (
    <div className="space-y-5">

      {/* Page header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="label-caps">Dashboard</p>
          <h1 className="mt-1.5 text-[22px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            {firstName}, here is your latest well-being snapshot
          </h1>
          <p className="mt-1 text-[13px]" style={{ color: "#7a92a8" }}>
            History, assessments, and recent sessions — in one place.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill
            label={apiHealthy ? "Backend online" : "Backend offline"}
            color={apiHealthy ? "#3d8a5c" : "#c04040"}
          />
          <StatusPill label={snapshot.category} color="#b5822a" />
          <button
            type="button"
            onClick={exportCSV}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium transition-all"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(55,75,105,0.4)",
              color: "#7a92a8",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "#c8d8ea"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "#7a92a8"; }}
          >
            <Download className="h-3 w-3" /> Export CSV
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div
        className="flex gap-1 rounded-xl p-1"
        style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.4)" }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className="flex-1 rounded-lg py-2 text-[12px] font-semibold transition-all duration-150"
            style={{
              background: activeTab === tab.id ? "#4a84d6" : "transparent",
              color:      activeTab === tab.id ? "#ffffff" : "#4a6278",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ─────────────────────────────────── */}
      {activeTab === "overview" && (
        <div className="space-y-4 animate-fadeIn">

          {/* Metric cards */}
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Latest MHI"       value={`${snapshot.latestMhi}`}        detail="Most recent composite well-being score"       accent="#4a84d6" />
            <MetricCard label="Weekly check-ins" value={`${snapshot.checkInsThisWeek}`} detail="Completed conversations this week"             accent="#3d8a5c" />
            <MetricCard label="Streak"           value={`${snapshot.streakDays}d`}       detail="Consistent check-ins build a clearer picture" accent="#b5822a" />
            <MetricCard label="Voice mode"       value={snapshot.voiceEnabled ? "On" : "Off"} detail="Current voice-based support preference"  accent="#6a5acd" />
          </section>

          {/* Trend + Emotion */}
          <section className="grid gap-3 xl:grid-cols-[1.4fr_0.6fr]">
            <TrendPanel values={snapshot.weeklyTrend} />
            <EmotionPanel items={snapshot.emotionMix} />
          </section>

          {/* Mood trend chart */}
          {moodEntries.length > 0 && (
            <section>
              <MoodTrendChart entries={moodEntries} />
            </section>
          )}

          {/* Sessions + Assessment */}
          <section className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
            <SessionPanel sessions={snapshot.recentSessions} />

            <Card>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="label-caps">Assessment</p>
                  <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    PHQ-2 &amp; GAD-2 update
                  </h3>
                </div>
                <div
                  className="shrink-0 rounded-lg px-2.5 py-1 text-[11px] font-medium"
                  style={{ background: "rgba(74,132,214,0.1)", color: "#4a84d6", border: "1px solid rgba(74,132,214,0.2)" }}
                >
                  0 – 6 scale
                </div>
              </div>

              <div className="mt-5 space-y-4">
                <ScoreInput label="PHQ-2 total" helper="Interest and low mood" value={phq2} onChange={setPhq2} color="#4a84d6" />
                <ScoreInput label="GAD-2 total" helper="Nervousness and worry" value={gad2} onChange={setGad2} color="#b5822a" />
                <button
                  type="button"
                  onClick={() => void handleAssessmentSubmit()}
                  className="w-full rounded-xl py-2.5 text-[13px] font-semibold text-white transition-all"
                  style={{ background: "#4a84d6" }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#3168b8"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "#4a84d6"; }}
                >
                  Save assessment
                </button>
                {assessmentStatus && (
                  <p className="text-center text-[12px]" style={{
                    color: assessmentStatus.includes("success") || assessmentStatus === "Saved successfully."
                      ? "#3d8a5c" : "#c04040",
                  }}>
                    {assessmentStatus}
                  </p>
                )}
              </div>
            </Card>
          </section>

          {/* Guidance + Summary */}
          <section className="grid gap-3 xl:grid-cols-2">
            <Card>
              <p className="label-caps">Guidance</p>
              <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Support cues for this week
              </h3>
              <div className="mt-4 space-y-2.5">
                <GuidanceRow icon={<Sparkles className="h-3.5 w-3.5" />}       title="Best next step"    text={guidance}                                                                                                                         color="#4a84d6" />
                <GuidanceRow icon={<HeartHandshake className="h-3.5 w-3.5" />} title="Assessment rhythm" text={`PHQ-2 is ${snapshot.assessment.phq2} and GAD-2 is ${snapshot.assessment.gad2}. Keeping these updated sharpens the trend.`}    color="#b5822a" />
                <GuidanceRow icon={<ShieldCheck className="h-3.5 w-3.5" />}    title="Session comfort"   text="The interface keeps movement light so you can focus on support, not the screen itself."                                          color="#3d8a5c" />
              </div>
            </Card>

            <Card>
              <p className="label-caps">Summary</p>
              <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Daily rhythm at a glance
              </h3>
              <div className="mt-4 grid grid-cols-2 gap-2.5">
                <SummaryTile label="Display name"        value={snapshot.displayName} />
                <SummaryTile label="Check-ins this week" value={`${snapshot.checkInsThisWeek}`} />
                <SummaryTile label="Streak"              value={`${snapshot.streakDays} days`} />
                <SummaryTile label="Languages"           value={(snapshot.sessionSummary?.languagesUsed ?? ["en"]).join(", ").toUpperCase()} />
              </div>

              <div
                className="mt-3 flex items-center gap-4 rounded-xl p-4"
                style={{ background: "rgba(74,132,214,0.07)", border: "1px solid rgba(74,132,214,0.18)" }}
              >
                <TrendingUp className="h-4 w-4 shrink-0" style={{ color: mhiColor }} />
                <div>
                  <p className="text-[11px]" style={{ color: "#4a6278" }}>Current MHI score</p>
                  <p className="text-[22px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    <span ref={mhiRef} style={{ display: "inline-block", transition: "transform 0.4s ease" }}>
                      {snapshot.latestMhi}
                    </span>
                    <span className="ml-1 text-[13px] font-normal" style={{ color: "#4a6278" }}>/ 100</span>
                  </p>
                </div>
              </div>
            </Card>
          </section>

          {/* MHI Gauge + CBT Engagement + Crisis Events */}
          <section className="grid gap-3 xl:grid-cols-3">
            <Card className="flex flex-col items-center">
              <p className="label-caps self-start">MHI Gauge</p>
              <h3 className="mt-1.5 self-start text-[14px] font-semibold text-white mb-3" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Well-being Index
              </h3>
              <MHIGauge mhi={snapshot.latestMhi} />
              <p className="mt-2 text-[13px] font-semibold" style={{ color: mhiColor }}>
                {snapshot.category}
              </p>
            </Card>

            <Card>
              <div className="flex items-center gap-2 mb-3">
                <Brain className="h-4 w-4" style={{ color: "#6a5acd" }} />
                <p className="label-caps">CBT Engagement</p>
              </div>
              {snapshot.cbtCounts && Object.keys(snapshot.cbtCounts).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(snapshot.cbtCounts).slice(0, 5).map(([t, count]) => (
                    <div
                      key={t}
                      className="flex items-center justify-between rounded-lg px-3 py-2"
                      style={{ background: "rgba(106,90,205,0.07)", border: "1px solid rgba(106,90,205,0.16)" }}
                    >
                      <span className="text-[12px] font-medium" style={{ color: "#6a5acd" }}>{CBT_LABELS[t] ?? t}</span>
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 rounded-full" style={{ width: Math.min(40 + count * 8, 80), background: "#6a5acd", opacity: 0.6 }} />
                        <span className="text-[10px]" style={{ color: "#4a6278" }}>×{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="py-6 text-center text-[13px]" style={{ color: "#4a6278" }}>No CBT sessions recorded yet.</p>
              )}
            </Card>

            <Card>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-4 w-4" style={{ color: "#c04040" }} />
                <p className="label-caps">Crisis Events</p>
              </div>
              <div className="flex flex-col items-center justify-center py-3">
                <p className="text-[40px] font-bold" style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  color: crisisEvents.length === 0 ? "#3d8a5c" : "#c04040",
                }}>
                  {crisisEvents.length}
                </p>
                <p className="text-[12px]" style={{ color: "#4a6278" }}>
                  {crisisEvents.length === 0 ? "No events recorded" : "events in history"}
                </p>
              </div>
              {crisisEvents.length > 0 && (
                <div className="space-y-1.5 mt-2">
                  {crisisEvents.slice(0, 3).map((ev, i) => {
                    const c = ev.crisis_tier === "active" ? "#c04040" : "#b5822a";
                    return (
                      <div key={i} className="flex items-center gap-2 rounded-lg px-3 py-2"
                        style={{ background: `${c}10`, border: `1px solid ${c}25` }}>
                        <div className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: c }} />
                        <span className="text-[11px] capitalize font-medium" style={{ color: c }}>{ev.crisis_tier}</span>
                        <span className="text-[10px] ml-auto" style={{ color: "#4a6278" }}>
                          {new Date(ev.timestamp).toLocaleDateString([], { month: "short", day: "numeric" })}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </section>
        </div>
      )}

      {/* ── SELF-HELP TOOLS TAB ──────────────────────────── */}
      {activeTab === "cbt" && (
        <div className="animate-fadeIn">
          <Card>
            <p className="label-caps mb-1">Self-Help Tools</p>
            <h3 className="mb-5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              CBT Techniques &amp; Exercises
            </h3>
            <CBTPanel />
          </Card>
        </div>
      )}

      {/* ── CRISIS HISTORY TAB ───────────────────────────── */}
      {activeTab === "crisis" && (
        <div className="animate-fadeIn">
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-4 w-4" style={{ color: "#c04040" }} />
              <p className="label-caps">Crisis History</p>
            </div>
            <h3 className="mb-5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Past crisis event timeline
            </h3>

            {crisisEvents.length === 0 ? (
              <div className="py-10 text-center text-[13px]" style={{ color: "#4a6278" }}>
                No crisis events recorded — that is a good sign.
              </div>
            ) : (
              <div className="space-y-3">
                {crisisEvents.map((ev, i) => {
                  const tierColor = ev.crisis_tier === "active" ? "#c04040"
                    : ev.crisis_tier === "passive" ? "#b5822a" : "#7a92a8";
                  return (
                    <div key={i} className="flex items-start gap-3 rounded-xl p-4"
                      style={{ background: `${tierColor}08`, border: `1px solid ${tierColor}22` }}>
                      <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full" style={{ background: tierColor }} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[11px] font-semibold capitalize" style={{ color: tierColor }}>
                            {ev.crisis_tier} crisis
                          </span>
                          <span className="text-[10px]" style={{ color: "#4a6278" }}>
                            {new Date(ev.timestamp).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                          </span>
                        </div>
                        <p className="mt-1 text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>
                          {ev.message_snippet}
                        </p>
                        <p className="mt-1 text-[10px]" style={{ color: "#4a6278" }}>
                          Score: {(ev.crisis_score * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────── */

function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <article className={`rounded-2xl p-5 ${className}`}
      style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
      {children}
    </article>
  );
}

function StatusPill({ label, color }: { label: string; color: string }) {
  return (
    <div className="rounded-full px-3 py-1.5 text-[11px] font-semibold"
      style={{ background: `${color}12`, border: `1px solid ${color}28`, color }}>
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
          <p className="text-[11px]" style={{ color: "#4a6278" }}>{helper}</p>
        </div>
        <span className="rounded-lg px-2.5 py-1 text-[13px] font-bold"
          style={{ background: `${color}14`, color }}>
          {value}
        </span>
      </div>
      <input type="range" min={0} max={6} step={1} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full cursor-pointer"
        style={{ accentColor: color }} />
    </div>
  );
}

function GuidanceRow({ icon, title, text, color }: { icon: ReactNode; title: string; text: string; color: string }) {
  return (
    <div className="rounded-xl p-3.5" style={{ background: `${color}08`, border: `1px solid ${color}1a` }}>
      <div className="flex items-center gap-2 text-[12px] font-semibold" style={{ color }}>
        {icon}{title}
      </div>
      <p className="mt-1.5 text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>{text}</p>
    </div>
  );
}

function SummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.35)" }}>
      <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: "#4a6278" }}>{label}</p>
      <p className="mt-1 truncate text-[13px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>{value}</p>
    </div>
  );
}

/* ── SVG MHI Gauge ───────────────────────────────────── */
function MHIGauge({ mhi }: { mhi: number }) {
  const cx = 100, cy = 100, r = 80;
  const startAngle = 180, totalDeg = 180;

  function polar(deg: number, radius = r) {
    const rad = (deg * Math.PI) / 180;
    return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) };
  }

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

  const bandDeg = totalDeg / MHI_BANDS.length;
  const bands = MHI_BANDS.map((band, i) => ({
    ...band,
    deg1: startAngle + i * bandDeg,
    deg2: startAngle + (i + 1) * bandDeg,
  }));

  const needleAngle = startAngle + ((mhi / 100) * totalDeg);
  const needleTip   = polar(needleAngle, 65);
  const needleBase1 = polar(needleAngle + 90, 6);
  const needleBase2 = polar(needleAngle - 90, 6);
  const mhiColor    = getMhiColor(mhi);

  return (
    <svg viewBox="0 0 200 110" style={{ width: "100%", maxWidth: 200, height: "auto" }}>
      {bands.map((band, i) => (
        <path key={i} d={arcPath(band.deg1, band.deg2, 82, 62)} fill={band.color} opacity={0.75} />
      ))}
      <path d={arcPath(startAngle, startAngle + totalDeg, 84, 60)} fill="none"
        stroke="rgba(55,75,105,0.5)" strokeWidth={1} />
      <polygon
        points={`${needleTip.x},${needleTip.y} ${needleBase1.x},${needleBase1.y} ${needleBase2.x},${needleBase2.y}`}
        fill={mhiColor}
        opacity={0.9}
        style={{ transition: "all 1s ease" }}
      />
      <circle cx={cx} cy={cy} r={7} fill="#172032" stroke={mhiColor} strokeWidth={2} />
      <text x={cx} y={cy - 14} textAnchor="middle" fontSize={20} fontWeight="bold"
        fill="#e0eaf6" fontFamily="Space Grotesk, sans-serif" style={{ transition: "all 1s ease" }}>
        {mhi}
      </text>
      <text x={18} y={104} fontSize={9} fill="#4a6278" textAnchor="middle">0</text>
      <text x={182} y={104} fontSize={9} fill="#4a6278" textAnchor="middle">100</text>
    </svg>
  );
}

function MoodTrendChart({ entries }: { entries: Array<{ timestamp: string; mood_rating: number }> }) {
  const sorted = [...entries].reverse();
  const max = 10, min = 1;
  const w = 600, h = 100, padX = 20, padY = 10;
  const points = sorted.map((e, i) => {
    const x = padX + (i / Math.max(sorted.length - 1, 1)) * (w - padX * 2);
    const y = h - padY - ((e.mood_rating - min) / (max - min)) * (h - padY * 2);
    return `${x},${y}`;
  }).join(" ");

  return (
    <article className="rounded-2xl p-5" style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
      <p className="label-caps">Mood Journal</p>
      <h3 className="mt-1.5 text-[15px] font-semibold text-white mb-4" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        Mood trend ({sorted.length} entries)
      </h3>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ minWidth: 260, height: 80 }}>
          {sorted.length > 1 && (
            <polyline fill="none" stroke="#b5822a" strokeWidth="2" strokeLinejoin="round" points={points} />
          )}
          {sorted.map((e, i) => {
            const x = padX + (i / Math.max(sorted.length - 1, 1)) * (w - padX * 2);
            const y = h - padY - ((e.mood_rating - min) / (max - min)) * (h - padY * 2);
            return <circle key={i} cx={x} cy={y} r={3} fill="#b5822a" />;
          })}
        </svg>
      </div>
      <div className="mt-1 flex justify-between text-[10px]" style={{ color: "#4a6278" }}>
        <span>Oldest</span><span>Latest</span>
      </div>
    </article>
  );
}
