import { useEffect, useRef, useState } from "react";
import { Check, ChevronLeft, ChevronRight } from "lucide-react";
import { CBT_TECHNIQUES } from "../../types";
import { recordCBTSession, saveMoodEntry } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type CBTPanelProps = {
  initialTechnique?: string | null;
};

// ── Breathing Exercise (4-7-8) ────────────────────────────────────────────────
function BreathingExercise({ onComplete }: { onComplete: () => void }) {
  const PHASES = [
    { label: "Inhale",  duration: 4, color: "#6ce3cf" },
    { label: "Hold",    duration: 7, color: "#ffc96b" },
    { label: "Exhale",  duration: 8, color: "#a78bfa" },
  ];
  const [phaseIdx, setPhaseIdx] = useState(0);
  const [tick, setTick]        = useState(0);
  const [running, setRunning]  = useState(false);
  const [cycles, setCycles]    = useState(0);

  useEffect(() => {
    if (!running) return;
    const phase = PHASES[phaseIdx];
    if (tick >= phase.duration) {
      const next = (phaseIdx + 1) % PHASES.length;
      setPhaseIdx(next);
      setTick(0);
      if (next === 0) setCycles((c) => c + 1);
      return;
    }
    const id = setTimeout(() => setTick((t) => t + 1), 1000);
    return () => clearTimeout(id);
  }, [running, phaseIdx, tick]);

  const phase = PHASES[phaseIdx];
  const progress = tick / phase.duration;
  const r = 56;
  const circ = 2 * Math.PI * r;

  return (
    <div className="flex flex-col items-center gap-5 py-4">
      <h4 className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        4-7-8 Breathing
      </h4>
      <p className="text-[12px] text-slate-500 text-center max-w-xs">
        Inhale for 4 counts, hold for 7, exhale for 8. Complete 4 cycles.
      </p>

      {/* SVG circle timer */}
      <div className="relative flex items-center justify-center">
        <svg width={140} height={140} className="-rotate-90">
          <circle cx={70} cy={70} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={8} />
          <circle
            cx={70} cy={70} r={r}
            fill="none"
            stroke={phase.color}
            strokeWidth={8}
            strokeDasharray={circ}
            strokeDashoffset={circ * (1 - progress)}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.9s linear, stroke 0.3s" }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-[22px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            {phase.duration - tick}
          </span>
          <span className="text-[11px] font-semibold" style={{ color: phase.color }}>{phase.label}</span>
        </div>
      </div>

      <p className="text-[11px] text-slate-600">Cycle {cycles + 1} of 4</p>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => setRunning((r) => !r)}
          className="rounded-[12px] px-6 py-2.5 text-[13px] font-semibold transition-all"
          style={{ background: "rgba(108,227,207,0.12)", color: "#6ce3cf", border: "1px solid rgba(108,227,207,0.25)" }}
        >
          {running ? "Pause" : "Start"}
        </button>
        {cycles >= 4 && (
          <button type="button" onClick={onComplete}
            className="rounded-[12px] px-6 py-2.5 text-[13px] font-semibold text-[#09111f]"
            style={{ background: "linear-gradient(135deg, #6ce3cf, #2cb8c7)" }}
          >
            Done
          </button>
        )}
      </div>
    </div>
  );
}

// ── Grounding 5-4-3-2-1 ──────────────────────────────────────────────────────
const GROUNDING_STEPS = [
  { count: 5, sense: "things you can SEE",    prompt: "Look around. Name 5 things visible to you right now." },
  { count: 4, sense: "things you can TOUCH",  prompt: "Feel your surroundings. Name 4 things you can physically touch." },
  { count: 3, sense: "things you can HEAR",   prompt: "Listen carefully. Name 3 sounds you can hear." },
  { count: 2, sense: "things you can SMELL",  prompt: "Notice any scents. Name 2 things you can smell." },
  { count: 1, sense: "thing you can TASTE",   prompt: "Name 1 taste in your mouth." },
];

function GroundingExercise({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const current = GROUNDING_STEPS[step];

  return (
    <div className="flex flex-col gap-4 py-2">
      <h4 className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        5-4-3-2-1 Grounding
      </h4>

      {/* Step progress dots */}
      <div className="flex gap-2 justify-center">
        {GROUNDING_STEPS.map((s, i) => (
          <div key={i} className="h-2 w-2 rounded-full transition-all"
            style={{ background: i <= step ? "#6ce3cf" : "rgba(255,255,255,0.1)" }} />
        ))}
      </div>

      <div className="rounded-[16px] p-5" style={{ background: "rgba(108,227,207,0.06)", border: "1px solid rgba(108,227,207,0.15)" }}>
        <div className="flex items-center gap-3 mb-3">
          <span className="text-[2rem] font-bold text-[#6ce3cf]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            {current.count}
          </span>
          <div>
            <p className="text-[13px] font-semibold text-white">{current.sense}</p>
            <p className="text-[11px] text-slate-400">{current.prompt}</p>
          </div>
        </div>
      </div>

      <div className="flex justify-between">
        <button type="button" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}
          className="flex items-center gap-1.5 rounded-[10px] px-4 py-2 text-[12px] disabled:opacity-30"
          style={{ background: "rgba(255,255,255,0.05)", color: "#94a3b8" }}>
          <ChevronLeft className="h-3.5 w-3.5" /> Back
        </button>
        {step < GROUNDING_STEPS.length - 1 ? (
          <button type="button" onClick={() => setStep((s) => s + 1)}
            className="flex items-center gap-1.5 rounded-[10px] px-4 py-2 text-[12px] font-semibold"
            style={{ background: "rgba(108,227,207,0.12)", color: "#6ce3cf" }}>
            Next <ChevronRight className="h-3.5 w-3.5" />
          </button>
        ) : (
          <button type="button" onClick={onComplete}
            className="flex items-center gap-1.5 rounded-[10px] px-4 py-2 text-[12px] font-semibold text-[#09111f]"
            style={{ background: "linear-gradient(135deg, #6ce3cf, #2cb8c7)" }}>
            <Check className="h-3.5 w-3.5" /> Complete
          </button>
        )}
      </div>
    </div>
  );
}

// ── Thought Record ────────────────────────────────────────────────────────────
function ThoughtRecord({ onComplete }: { onComplete: (notes: string) => void }) {
  const [situation, setSituation]   = useState("");
  const [autoThought, setAutoThought] = useState("");
  const [emotion, setEmotion]       = useState("");
  const [evidenceFor, setEvidenceFor] = useState("");
  const [evidenceAgainst, setEvidenceAgainst] = useState("");
  const [balanced, setBalanced]     = useState("");

  const allFilled = situation && autoThought && emotion && balanced;
  const notes = `Situation: ${situation}\nAuto-thought: ${autoThought}\nEmotion: ${emotion}\nEvidence for: ${evidenceFor}\nEvidence against: ${evidenceAgainst}\nBalanced thought: ${balanced}`;

  return (
    <div className="space-y-3 py-2">
      <h4 className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        Thought Record
      </h4>
      {[
        { label: "Situation", value: situation, set: setSituation, placeholder: "What happened?" },
        { label: "Automatic thought", value: autoThought, set: setAutoThought, placeholder: "What ran through your mind?" },
        { label: "Emotion & intensity (e.g. Anxious 7/10)", value: emotion, set: setEmotion, placeholder: "e.g. Sad 6/10" },
        { label: "Evidence FOR the thought", value: evidenceFor, set: setEvidenceFor, placeholder: "Facts that support it" },
        { label: "Evidence AGAINST the thought", value: evidenceAgainst, set: setEvidenceAgainst, placeholder: "Facts that challenge it" },
        { label: "Balanced thought", value: balanced, set: setBalanced, placeholder: "A more balanced way to see this…" },
      ].map(({ label, value, set, placeholder }) => (
        <div key={label}>
          <p className="mb-1 text-[11px] font-semibold text-slate-400">{label}</p>
          <textarea
            value={value}
            onChange={(e) => set(e.target.value)}
            placeholder={placeholder}
            rows={2}
            className="w-full resize-none rounded-[12px] px-3 py-2.5 text-[12px] text-slate-200 placeholder-slate-600 outline-none"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
          />
        </div>
      ))}
      <button type="button" disabled={!allFilled} onClick={() => onComplete(notes)}
        className="w-full rounded-[12px] py-2.5 text-[13px] font-semibold text-[#09111f] disabled:opacity-40"
        style={{ background: "linear-gradient(135deg, #6ce3cf, #2cb8c7)" }}>
        Save thought record
      </button>
    </div>
  );
}

// ── Mood Journal ──────────────────────────────────────────────────────────────
function MoodJournalWidget({ onComplete }: { onComplete: (rating: number, notes: string) => void }) {
  const [rating, setRating] = useState(5);
  const [notes, setNotes]   = useState("");

  const color = rating >= 7 ? "#7be495" : rating >= 4 ? "#ffc96b" : "#ff7b70";

  return (
    <div className="space-y-4 py-2">
      <h4 className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        Mood Journal
      </h4>
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-[12px] text-slate-400">How are you feeling? (1 = very low, 10 = great)</p>
          <span className="text-[20px] font-bold" style={{ color, fontFamily: "'Space Grotesk', sans-serif" }}>{rating}</span>
        </div>
        <input type="range" min={1} max={10} step={1} value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
          className="w-full cursor-pointer" style={{ accentColor: color }} />
        <div className="flex justify-between text-[10px] text-slate-600 mt-1">
          <span>Very low</span><span>Great</span>
        </div>
      </div>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Optional: anything on your mind today?"
        rows={3}
        className="w-full resize-none rounded-[12px] px-3 py-2.5 text-[12px] text-slate-200 placeholder-slate-600 outline-none"
        style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
      />
      <button type="button" onClick={() => onComplete(rating, notes)}
        className="w-full rounded-[12px] py-2.5 text-[13px] font-semibold text-[#09111f]"
        style={{ background: "linear-gradient(135deg, #6ce3cf, #2cb8c7)" }}>
        Save entry
      </button>
    </div>
  );
}

// ── Cognitive Restructuring ───────────────────────────────────────────────────
const REFRAME_STEPS = [
  { q: "What is the negative thought?", placeholder: "Write the thought exactly as it feels…" },
  { q: "What thinking pattern might this be?", placeholder: "e.g. All-or-nothing, catastrophising, mind-reading…" },
  { q: "What would you say to a friend with this thought?", placeholder: "Imagine advising someone you care about…" },
  { q: "What is a more helpful, realistic alternative?", placeholder: "A kinder, more balanced version of the thought…" },
];

function CognitiveRestructuring({ onComplete }: { onComplete: (notes: string) => void }) {
  const [step, setStep]         = useState(0);
  const [answers, setAnswers]   = useState<string[]>(["", "", "", ""]);

  function setAnswer(val: string) {
    setAnswers((prev) => prev.map((a, i) => (i === step ? val : a)));
  }

  const current = REFRAME_STEPS[step];
  const notes = REFRAME_STEPS.map((s, i) => `${s.q}\n${answers[i]}`).join("\n\n");

  return (
    <div className="space-y-4 py-2">
      <h4 className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        Cognitive Restructuring
      </h4>

      <div className="flex gap-1.5 justify-center">
        {REFRAME_STEPS.map((_, i) => (
          <div key={i} className="h-1.5 rounded-full transition-all"
            style={{ width: i === step ? 24 : 8, background: i <= step ? "#6ce3cf" : "rgba(255,255,255,0.1)" }} />
        ))}
      </div>

      <div className="rounded-[16px] p-4" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
        <p className="text-[12px] font-semibold text-[#6ce3cf] mb-2">Step {step + 1} of {REFRAME_STEPS.length}</p>
        <p className="text-[13px] text-white mb-3">{current.q}</p>
        <textarea
          value={answers[step]}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder={current.placeholder}
          rows={3}
          className="w-full resize-none rounded-[10px] px-3 py-2.5 text-[12px] text-slate-200 placeholder-slate-600 outline-none"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
        />
      </div>

      <div className="flex justify-between">
        <button type="button" disabled={step === 0} onClick={() => setStep((s) => s - 1)}
          className="flex items-center gap-1.5 rounded-[10px] px-4 py-2 text-[12px] disabled:opacity-30"
          style={{ background: "rgba(255,255,255,0.05)", color: "#94a3b8" }}>
          <ChevronLeft className="h-3.5 w-3.5" /> Back
        </button>
        {step < REFRAME_STEPS.length - 1 ? (
          <button type="button" disabled={!answers[step].trim()} onClick={() => setStep((s) => s + 1)}
            className="flex items-center gap-1.5 rounded-[10px] px-4 py-2 text-[12px] font-semibold disabled:opacity-40"
            style={{ background: "rgba(108,227,207,0.12)", color: "#6ce3cf" }}>
            Next <ChevronRight className="h-3.5 w-3.5" />
          </button>
        ) : (
          <button type="button" disabled={!answers[step].trim()} onClick={() => onComplete(notes)}
            className="flex items-center gap-1.5 rounded-[10px] px-4 py-2 text-[12px] font-semibold disabled:opacity-40 text-[#09111f]"
            style={{ background: "linear-gradient(135deg, #6ce3cf, #2cb8c7)" }}>
            <Check className="h-3.5 w-3.5" /> Complete
          </button>
        )}
      </div>
    </div>
  );
}

// ── Main CBT Panel ────────────────────────────────────────────────────────────
export function CBTPanel({ initialTechnique }: CBTPanelProps) {
  const { token } = useAuth();
  const [active, setActive]     = useState<string | null>(initialTechnique ?? null);
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [saved, setSaved]       = useState(false);

  async function handleComplete(technique: string, notes = "") {
    setCompleted((prev) => new Set(prev).add(technique));
    setSaved(false);
    if (!token) return;
    try {
      await recordCBTSession(token, technique, notes, true);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { /* non-fatal */ }
    setActive(null);
  }

  async function handleMoodComplete(rating: number, notes: string) {
    if (!token) return;
    try {
      await saveMoodEntry(token, rating, notes);
    } catch { /* non-fatal */ }
    await handleComplete("mood_journal", notes);
  }

  return (
    <div className="space-y-4">
      {/* Technique selector */}
      {!active && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {CBT_TECHNIQUES.map((t) => {
              const done = completed.has(t.id);
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setActive(t.id)}
                  className="flex items-start gap-3 rounded-[16px] p-4 text-left transition-all hover:opacity-90"
                  style={{
                    background: done ? "rgba(123,228,149,0.07)" : "rgba(255,255,255,0.03)",
                    border: done ? "1px solid rgba(123,228,149,0.2)" : "1px solid rgba(255,255,255,0.07)",
                  }}
                >
                  <span className="text-[1.6rem]" role="img" aria-label={t.label}>{t.icon}</span>
                  <div>
                    <p className="text-[13px] font-semibold text-white flex items-center gap-1.5">
                      {t.label}
                      {done && <Check className="h-3 w-3 text-[#7be495]" />}
                    </p>
                    <p className="text-[11px] text-slate-500">{t.description}</p>
                  </div>
                </button>
              );
            })}
          </div>
          {saved && (
            <p className="text-center text-[12px] text-[#7be495]">Session saved successfully.</p>
          )}
        </>
      )}

      {/* Active exercise */}
      {active === "breathing" && (
        <div className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <button type="button" onClick={() => setActive(null)} className="mb-3 text-[11px] text-slate-500 hover:text-white">
            ← Back to techniques
          </button>
          <BreathingExercise onComplete={() => void handleComplete("breathing")} />
        </div>
      )}

      {active === "grounding" && (
        <div className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <button type="button" onClick={() => setActive(null)} className="mb-3 text-[11px] text-slate-500 hover:text-white">
            ← Back to techniques
          </button>
          <GroundingExercise onComplete={() => void handleComplete("grounding")} />
        </div>
      )}

      {active === "thought_record" && (
        <div className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <button type="button" onClick={() => setActive(null)} className="mb-3 text-[11px] text-slate-500 hover:text-white">
            ← Back to techniques
          </button>
          <ThoughtRecord onComplete={(notes) => void handleComplete("thought_record", notes)} />
        </div>
      )}

      {active === "mood_journal" && (
        <div className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <button type="button" onClick={() => setActive(null)} className="mb-3 text-[11px] text-slate-500 hover:text-white">
            ← Back to techniques
          </button>
          <MoodJournalWidget onComplete={(r, n) => void handleMoodComplete(r, n)} />
        </div>
      )}

      {active === "cognitive_restructuring" && (
        <div className="rounded-[20px] p-5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <button type="button" onClick={() => setActive(null)} className="mb-3 text-[11px] text-slate-500 hover:text-white">
            ← Back to techniques
          </button>
          <CognitiveRestructuring onComplete={(notes) => void handleComplete("cognitive_restructuring", notes)} />
        </div>
      )}
    </div>
  );
}
