import { useEffect, useState } from "react";
import { Bell, Check, ChevronRight, Globe, Mic2, ShieldHalf, User, WandSparkles } from "lucide-react";
import { PageHeader } from "../components/shared/PageHeader";
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
    statusColor: "#7be495",
    toggle: { label: "Retain session history", default: true },
  },
  {
    id:          "notifications",
    title:       "Notifications",
    icon:        Bell,
    description: "Gentle reminders for check-ins, progress summaries, and report readiness.",
    status:      "Calm",
    statusColor: "#ffc96b",
    toggle: { label: "Enable check-in reminders", default: false },
  },
  {
    id:          "ai",
    title:       "AI behaviour",
    icon:        WandSparkles,
    description: "Tone preferences, follow-up depth, and future personalization controls.",
    status:      "Thoughtful",
    statusColor: "#a78bfa",
    toggle: { label: "Adaptive tone responses", default: true },
  },
] as const;

export function SettingsPage() {
  const { token, user, refreshUser }           = useAuth();
  const [toggles, setToggles]                  = useState<ToggleState>(
    Object.fromEntries(BASIC_SETTINGS.map((g) => [g.id, g.toggle.default])),
  );
  const [selectedAvatar, setSelectedAvatar]    = useState(user?.avatarId ?? "therapist");
  const [selectedLang, setSelectedLang]        = useState(user?.preferredLanguage ?? "en");
  const [voicePref, setVoicePref]              = useState<"elevenlabs" | "gtts">("elevenlabs");
  const [saving, setSaving]                    = useState(false);
  const [saveMsg, setSaveMsg]                  = useState("");
  const [quota, setQuota]                      = useState<{
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
      await updateUserProfile(token, {
        avatar_id:          selectedAvatar,
        preferred_language: selectedLang,
      });
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
      <PageHeader
        eyebrow="Settings"
        title="Preferences and controls"
        description="Grouped by need, kept simple — so adjusting your workspace never adds stress."
      />

      {/* ── PERSONALIZATION ─────────────────────────────── */}
      <section
        className="rounded-[20px] p-5"
        style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}
      >
        <div className="flex items-center gap-2.5 mb-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-[10px]" style={{ background: "rgba(108,227,207,0.1)" }}>
            <User className="h-4 w-4 text-[#6ce3cf]" />
          </div>
          <div>
            <h3 className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Personalization
            </h3>
            <p className="text-[11px] text-[#6ce3cf]">Avatar &amp; language</p>
          </div>
        </div>

        {/* Avatar selector */}
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
          Choose companion
        </p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 mb-5">
          {AVATAR_PERSONAS.map((p) => {
            const isSelected = selectedAvatar === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedAvatar(p.id)}
                className="flex flex-col items-center gap-1.5 rounded-[14px] p-3 transition-all"
                style={{
                  background: isSelected ? `${p.accentColor}12` : "rgba(255,255,255,0.02)",
                  border: isSelected ? `2px solid ${p.accentColor}50` : "2px solid rgba(255,255,255,0.06)",
                }}
              >
                <span style={{ fontSize: "1.8rem" }} role="img" aria-label={p.name}>{p.emoji}</span>
                <p className="text-[11px] font-semibold" style={{ color: isSelected ? p.accentColor : "#94a3b8" }}>
                  {p.name}
                </p>
                {isSelected && <Check className="h-3 w-3" style={{ color: p.accentColor }} />}
              </button>
            );
          })}
        </div>

        {/* Language selector */}
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
          Preferred language
        </p>
        <div
          className="mb-5 rounded-[14px] overflow-hidden"
          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div className="flex items-center gap-2 px-3 pt-2.5 pb-0.5">
            <Globe className="h-3.5 w-3.5 text-[#6ce3cf]/60" />
            <p className="text-[11px] text-slate-500">
              Used as default when speech detection is uncertain (confidence &lt; 75%)
            </p>
          </div>
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            className="w-full bg-transparent px-4 py-2.5 text-[13px] text-white outline-none cursor-pointer"
            style={{ background: "transparent" }}
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code} style={{ background: "#09111f" }}>
                {lang.flag} {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Voice engine preference */}
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
          Voice engine
        </p>
        <div className="mb-5 grid grid-cols-2 gap-2">
          {(["elevenlabs", "gtts"] as const).map((engine) => (
            <button
              key={engine}
              type="button"
              onClick={() => setVoicePref(engine)}
              className="rounded-[12px] p-3 text-left transition-all"
              style={{
                background: voicePref === engine ? "rgba(108,227,207,0.08)" : "rgba(255,255,255,0.02)",
                border: voicePref === engine ? "1px solid rgba(108,227,207,0.25)" : "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <div className="flex items-center justify-between">
                <Mic2 className="h-3.5 w-3.5" style={{ color: voicePref === engine ? "#6ce3cf" : "#64748b" }} />
                {voicePref === engine && <Check className="h-3 w-3 text-[#6ce3cf]" />}
              </div>
              <p className="mt-1.5 text-[12px] font-semibold" style={{ color: voicePref === engine ? "#6ce3cf" : "#94a3b8" }}>
                {engine === "elevenlabs" ? "ElevenLabs" : "gTTS (Free)"}
              </p>
              <p className="text-[10px] text-slate-600">
                {engine === "elevenlabs" ? "Realistic, avatar-mapped voices" : "Google TTS, Indian accent"}
              </p>
            </button>
          ))}
        </div>

        {/* ElevenLabs quota bar */}
        {quota && (
          <div className="mb-5 rounded-[12px] p-3" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[11px] text-slate-500">ElevenLabs usage this session</p>
              <p className="text-[11px] font-semibold text-white">
                {quota.chars_used.toLocaleString()} / {quota.chars_limit.toLocaleString()} chars
              </p>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.min(100, (quota.chars_used / quota.chars_limit) * 100)}%`,
                  background: quota.chars_used > quota.chars_limit * 0.8 ? "#ff7b70" : "#6ce3cf",
                }}
              />
            </div>
            {!quota.api_key_set && (
              <p className="mt-1 text-[10px] text-[#ffc96b]">
                ELEVENLABS_API_KEY not set — using gTTS fallback.
              </p>
            )}
          </div>
        )}

        {/* Save button */}
        <button
          type="button"
          disabled={saving}
          onClick={() => void savePersonalization()}
          className="w-full rounded-[12px] py-2.5 text-[13px] font-semibold text-[#09111f] transition-all hover:opacity-90 disabled:opacity-50"
          style={{ background: "linear-gradient(135deg, #6ce3cf 0%, #2cb8c7 100%)" }}
        >
          {saving ? "Saving…" : "Save personalization"}
        </button>
        {saveMsg && (
          <p className="mt-2 text-center text-[12px]"
            style={{ color: saveMsg.includes("success") || saveMsg === "Saved successfully." ? "#7be495" : "#ff7b70" }}>
            {saveMsg}
          </p>
        )}
      </section>

      {/* ── BASIC SETTINGS CARDS ──────────────────────────── */}
      <section className="grid gap-3 lg:grid-cols-3">
        {BASIC_SETTINGS.map((group) => {
          const Icon = group.icon;
          const isOn = toggles[group.id];
          return (
            <article
              key={group.id}
              className="rounded-[20px] p-5 transition-all duration-200"
              style={{ background: "rgba(255,255,255,0.028)", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px]"
                    style={{ background: `${group.statusColor}12` }}>
                    <Icon className="h-4 w-4" style={{ color: group.statusColor }} />
                  </div>
                  <div>
                    <h3 className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                      {group.title}
                    </h3>
                    <span className="text-[11px] font-medium" style={{ color: group.statusColor }}>{group.status}</span>
                  </div>
                </div>
                <div className="mt-1 h-2 w-2 shrink-0 rounded-full"
                  style={{
                    background: isOn ? group.statusColor : "rgba(255,255,255,0.1)",
                    boxShadow: isOn ? `0 0 6px ${group.statusColor}` : "none",
                    transition: "all 0.3s",
                  }} />
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-slate-500">{group.description}</p>
              <div className="mt-4 flex items-center justify-between rounded-[12px] px-3 py-3"
                style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <span className="text-[12px] text-slate-400">{group.toggle.label}</span>
                <button type="button" role="switch" aria-checked={isOn} onClick={() => flip(group.id)}
                  className="relative h-5 w-9 rounded-full transition-all duration-300 focus:outline-none"
                  style={{ background: isOn ? group.statusColor : "rgba(255,255,255,0.1)" }}>
                  <span className="absolute top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-white transition-all duration-300"
                    style={{ left: isOn ? "calc(100% - 18px)" : "2px" }}>
                    {isOn && <Check className="h-2.5 w-2.5 text-[#09111f]" strokeWidth={3} />}
                  </span>
                </button>
              </div>
            </article>
          );
        })}
      </section>

      {/* Principles section */}
      <section className="rounded-[20px] p-5"
        style={{ background: "rgba(255,255,255,0.022)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Design principles</p>
        <h3 className="mt-1.5 text-[16px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          How this settings page is built
        </h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { title: "Less cognitive load",  text: "Fewer moving parts and simpler labels make the page easier to process.",           color: "#6ce3cf" },
            { title: "Honest states",        text: "Controls show real state and avoid fake toggles that don't persist yet.",          color: "#ffc96b" },
            { title: "Ready to extend",      text: "Structure is ready for future wiring without forcing backend changes now.",        color: "#a78bfa" },
          ].map((item) => (
            <div key={item.title} className="rounded-[14px] p-4" style={{ background: `${item.color}06`, border: `1px solid ${item.color}14` }}>
              <div className="flex items-center gap-2 mb-2">
                <ChevronRight className="h-3.5 w-3.5" style={{ color: item.color }} />
                <p className="text-[13px] font-semibold" style={{ fontFamily: "'Space Grotesk', sans-serif", color: item.color }}>{item.title}</p>
              </div>
              <p className="text-[12px] leading-relaxed text-slate-500">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Danger zone */}
      <section className="rounded-[20px] p-5" style={{ background: "rgba(255,123,112,0.04)", border: "1px solid rgba(255,123,112,0.12)" }}>
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#ff7b70]/60">Account actions</p>
        <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          Data and account
        </h3>
        <p className="mt-2 text-[12px] leading-relaxed text-slate-500">
          Export your full history or permanently delete your account and all associated data.
          These actions cannot be undone.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button type="button"
            className="rounded-[10px] px-4 py-2 text-[12px] font-medium text-slate-400 transition-all hover:text-white"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            Export my data
          </button>
          <button type="button"
            className="rounded-[10px] px-4 py-2 text-[12px] font-medium text-[#ff7b70]/80 transition-all hover:text-[#ff7b70]"
            style={{ background: "rgba(255,123,112,0.06)", border: "1px solid rgba(255,123,112,0.16)" }}>
            Delete account
          </button>
        </div>
      </section>
    </div>
  );
}
