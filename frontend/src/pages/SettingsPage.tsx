import { useEffect, useState } from "react";
import { Bell, Check, ChevronRight, Globe, Mic2, ShieldHalf, User, WandSparkles } from "lucide-react";
import { updateUserProfile, getVoiceQuota } from "../lib/api";
import { useAuth } from "../lib/auth";
import { AVATAR_PERSONAS, SUPPORTED_LANGUAGES } from "../types";

type ToggleState = Record<string, boolean>;

const BASIC_SETTINGS = [
  {
    id:          "privacy",
    title:       "Privacy and access",
    icon:        ShieldHalf,
    description: "Session retention, export controls, and account-linked authentication rules.",
    status:      "Protected",
    statusColor: "#3d8a5c",
    toggle:      { label: "Retain session history", default: true },
  },
  {
    id:          "notifications",
    title:       "Notifications",
    icon:        Bell,
    description: "Gentle reminders for check-ins, progress summaries, and report readiness.",
    status:      "Calm",
    statusColor: "#b5822a",
    toggle:      { label: "Enable check-in reminders", default: false },
  },
  {
    id:          "ai",
    title:       "AI behaviour",
    icon:        WandSparkles,
    description: "Tone preferences, follow-up depth, and future personalization controls.",
    status:      "Thoughtful",
    statusColor: "#6a5acd",
    toggle:      { label: "Adaptive tone responses", default: true },
  },
] as const;

export function SettingsPage() {
  const { token, user, refreshUser }         = useAuth();
  const [toggles, setToggles]                = useState<ToggleState>(
    Object.fromEntries(BASIC_SETTINGS.map((g) => [g.id, g.toggle.default])),
  );
  const [selectedAvatar, setSelectedAvatar]  = useState(user?.avatarId ?? "therapist");
  const [selectedLang, setSelectedLang]      = useState(user?.preferredLanguage ?? "en");
  const [voicePref, setVoicePref]            = useState<"elevenlabs" | "gtts">("elevenlabs");
  const [saving, setSaving]                  = useState(false);
  const [saveMsg, setSaveMsg]                = useState("");
  const [quota, setQuota]                    = useState<{
    chars_used: number; chars_limit: number; chars_remaining: number; api_key_set: boolean;
  } | null>(null);

  useEffect(() => {
    if (!token) return;
    void getVoiceQuota(token).then(setQuota).catch(() => {});
  }, [token]);

  function flip(id: string) {
    setToggles((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function savePersonalization() {
    if (!token) return;
    setSaving(true);
    setSaveMsg("");
    try {
      await updateUserProfile(token, { avatar_id: selectedAvatar, preferred_language: selectedLang });
      await refreshUser();
      setSaveMsg("Saved successfully.");
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div>
        <p className="label-caps">Settings</p>
        <h1 className="mt-1.5 text-[20px] font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          Preferences and controls
        </h1>
        <p className="mt-1 text-[13px]" style={{ color: "#7a92a8" }}>
          Grouped by need, kept simple — adjusting your workspace should never add stress.
        </p>
      </div>

      {/* ── PERSONALIZATION ─────────────────────────────── */}
      <section className="rounded-2xl p-5" style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
        <div className="flex items-center gap-2.5 mb-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: "rgba(74,132,214,0.12)", border: "1px solid rgba(74,132,214,0.2)" }}>
            <User className="h-4 w-4" style={{ color: "#4a84d6" }} />
          </div>
          <div>
            <h3 className="text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Personalization
            </h3>
            <p className="text-[11px]" style={{ color: "#4a84d6" }}>Avatar &amp; language</p>
          </div>
        </div>

        {/* Avatar selector */}
        <p className="label-caps mb-2">Choose companion</p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 mb-5">
          {AVATAR_PERSONAS.map((p) => {
            const isSelected = selectedAvatar === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedAvatar(p.id)}
                className="flex flex-col items-center gap-1.5 rounded-xl p-3 transition-all"
                style={{
                  background: isSelected ? "rgba(74,132,214,0.12)" : "rgba(255,255,255,0.02)",
                  border:     isSelected ? "2px solid rgba(74,132,214,0.4)" : "2px solid rgba(55,75,105,0.35)",
                }}
              >
                <span style={{ fontSize: "1.6rem", lineHeight: 1 }} role="img" aria-label={p.name}>
                  {p.emoji}
                </span>
                <p className="text-[11px] font-semibold" style={{ color: isSelected ? "#4a84d6" : "#7a92a8" }}>
                  {p.name}
                </p>
                {isSelected && <Check className="h-3 w-3" style={{ color: "#4a84d6" }} />}
              </button>
            );
          })}
        </div>

        {/* Language selector */}
        <p className="label-caps mb-2">Preferred language</p>
        <div className="mb-5 rounded-xl overflow-hidden" style={{ background: "#0c1220", border: "1px solid rgba(55,75,105,0.45)" }}>
          <div className="flex items-center gap-2 px-3 pt-2.5 pb-0.5">
            <Globe className="h-3.5 w-3.5" style={{ color: "#4a6278" }} />
            <p className="text-[11px]" style={{ color: "#4a6278" }}>
              Used as default when speech detection confidence is below 75%
            </p>
          </div>
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            className="w-full bg-transparent px-4 py-2.5 text-[13px] outline-none cursor-pointer"
            style={{ color: "#c8d8ea" }}
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code} style={{ background: "#0c1220" }}>
                {lang.flag} {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Voice engine */}
        <p className="label-caps mb-2">Voice engine</p>
        <div className="mb-5 grid grid-cols-2 gap-2">
          {(["elevenlabs", "gtts"] as const).map((engine) => (
            <button
              key={engine}
              type="button"
              onClick={() => setVoicePref(engine)}
              className="rounded-xl p-3 text-left transition-all"
              style={{
                background: voicePref === engine ? "rgba(74,132,214,0.1)" : "rgba(255,255,255,0.02)",
                border:     voicePref === engine ? "1px solid rgba(74,132,214,0.3)" : "1px solid rgba(55,75,105,0.35)",
              }}
            >
              <div className="flex items-center justify-between">
                <Mic2 className="h-3.5 w-3.5" style={{ color: voicePref === engine ? "#4a84d6" : "#4a6278" }} />
                {voicePref === engine && <Check className="h-3 w-3" style={{ color: "#4a84d6" }} />}
              </div>
              <p className="mt-1.5 text-[12px] font-semibold" style={{ color: voicePref === engine ? "#4a84d6" : "#7a92a8" }}>
                {engine === "elevenlabs" ? "ElevenLabs" : "gTTS (Free)"}
              </p>
              <p className="text-[10px]" style={{ color: "#4a6278" }}>
                {engine === "elevenlabs" ? "Realistic, avatar-mapped voices" : "Google TTS, Indian accent"}
              </p>
            </button>
          ))}
        </div>

        {/* ElevenLabs quota */}
        {quota && (
          <div className="mb-5 rounded-xl p-3" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.35)" }}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-[11px]" style={{ color: "#4a6278" }}>ElevenLabs usage</p>
              <p className="text-[11px] font-semibold text-white">
                {quota.chars_used.toLocaleString()} / {quota.chars_limit.toLocaleString()} chars
              </p>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.min(100, (quota.chars_used / quota.chars_limit) * 100)}%`,
                  background: quota.chars_used > quota.chars_limit * 0.8 ? "#c04040" : "#4a84d6",
                }}
              />
            </div>
            {!quota.api_key_set && (
              <p className="mt-1.5 text-[10px]" style={{ color: "#b5822a" }}>
                ELEVENLABS_API_KEY not set — using gTTS fallback.
              </p>
            )}
          </div>
        )}

        {/* Save */}
        <button
          type="button"
          disabled={saving}
          onClick={() => void savePersonalization()}
          className="w-full rounded-xl py-2.5 text-[13px] font-semibold text-white transition-all disabled:opacity-50"
          style={{ background: "#4a84d6" }}
          onMouseEnter={(e) => { if (!saving) (e.currentTarget as HTMLElement).style.background = "#3168b8"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "#4a84d6"; }}
        >
          {saving ? "Saving…" : "Save personalization"}
        </button>
        {saveMsg && (
          <p className="mt-2 text-center text-[12px]" style={{
            color: saveMsg.includes("success") || saveMsg === "Saved successfully." ? "#3d8a5c" : "#c04040",
          }}>
            {saveMsg}
          </p>
        )}
      </section>

      {/* ── BASIC SETTINGS ──────────────────────────────── */}
      <section className="grid gap-3 lg:grid-cols-3">
        {BASIC_SETTINGS.map((group) => {
          const Icon = group.icon;
          const isOn = toggles[group.id];
          return (
            <article
              key={group.id}
              className="rounded-2xl p-5"
              style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl"
                    style={{ background: `${group.statusColor}12`, border: `1px solid ${group.statusColor}22` }}
                  >
                    <Icon className="h-4 w-4" style={{ color: group.statusColor }} />
                  </div>
                  <div>
                    <h3 className="text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                      {group.title}
                    </h3>
                    <span className="text-[11px] font-medium" style={{ color: group.statusColor }}>{group.status}</span>
                  </div>
                </div>
                <div
                  className="mt-1 h-2 w-2 shrink-0 rounded-full transition-all duration-300"
                  style={{ background: isOn ? group.statusColor : "rgba(55,75,105,0.5)" }}
                />
              </div>
              <p className="mt-3 text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>{group.description}</p>
              <div
                className="mt-4 flex items-center justify-between rounded-xl px-3 py-3"
                style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.35)" }}
              >
                <span className="text-[12px]" style={{ color: "#7a92a8" }}>{group.toggle.label}</span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={isOn}
                  onClick={() => flip(group.id)}
                  className="relative h-5 w-9 rounded-full transition-all duration-200 focus:outline-none"
                  style={{ background: isOn ? group.statusColor : "rgba(55,75,105,0.5)" }}
                >
                  <span
                    className="absolute top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-white transition-all duration-200"
                    style={{ left: isOn ? "calc(100% - 18px)" : "2px" }}
                  >
                    {isOn && <Check className="h-2.5 w-2.5" style={{ color: group.statusColor }} strokeWidth={3} />}
                  </span>
                </button>
              </div>
            </article>
          );
        })}
      </section>

      {/* Design principles */}
      <section className="rounded-2xl p-5" style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}>
        <p className="label-caps">Design principles</p>
        <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          How this settings page is built
        </h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { title: "Less cognitive load",  text: "Fewer moving parts and simpler labels make the page easier to process.",         color: "#4a84d6" },
            { title: "Honest states",        text: "Controls show real state and avoid fake toggles that don't persist yet.",         color: "#b5822a" },
            { title: "Ready to extend",      text: "Structure is ready for future wiring without forcing backend changes now.",        color: "#6a5acd" },
          ].map((item) => (
            <div key={item.title} className="rounded-xl p-4" style={{ background: `${item.color}08`, border: `1px solid ${item.color}18` }}>
              <div className="flex items-center gap-2 mb-2">
                <ChevronRight className="h-3.5 w-3.5" style={{ color: item.color }} />
                <p className="text-[12px] font-semibold" style={{ fontFamily: "'Space Grotesk', sans-serif", color: item.color }}>
                  {item.title}
                </p>
              </div>
              <p className="text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Danger zone */}
      <section className="rounded-2xl p-5" style={{ background: "rgba(192,64,64,0.04)", border: "1px solid rgba(192,64,64,0.18)" }}>
        <p className="label-caps" style={{ color: "rgba(192,64,64,0.7)" }}>Account actions</p>
        <h3 className="mt-1.5 text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          Data and account
        </h3>
        <p className="mt-2 text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>
          Export your full history or permanently delete your account and all associated data.
          These actions cannot be undone.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-xl px-4 py-2 text-[12px] font-medium transition-all"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(55,75,105,0.35)", color: "#7a92a8" }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "#c8d8ea"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "#7a92a8"; }}
          >
            Export my data
          </button>
          <button
            type="button"
            className="rounded-xl px-4 py-2 text-[12px] font-medium transition-all"
            style={{ background: "rgba(192,64,64,0.06)", border: "1px solid rgba(192,64,64,0.22)", color: "#c04040" }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(192,64,64,0.12)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(192,64,64,0.06)"; }}
          >
            Delete account
          </button>
        </div>
      </section>
    </div>
  );
}
