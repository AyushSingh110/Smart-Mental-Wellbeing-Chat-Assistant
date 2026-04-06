import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check } from "lucide-react";
import { AVATAR_PERSONAS } from "../types";
import { updateUserProfile } from "../lib/api";
import { useAuth } from "../lib/auth";

export function AvatarSelectionPage() {
  const { token, user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string>("therapist");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleContinue() {
    if (!token || !user) return;
    setSaving(true);
    setError("");
    try {
      await updateUserProfile(token, { avatar_id: selected });
      await refreshUser();
      window.localStorage.setItem(`avatar_chosen_${user.id}`, "1");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save avatar.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="relative min-h-screen w-full overflow-hidden text-white flex items-center justify-center p-4"
      style={{ background: "#09111f" }}
    >
      {/* Background mesh */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(108,227,207,0.07) 0%, transparent 60%)",
        }}
      />

      <div className="relative mx-auto w-full max-w-[900px]">
        {/* Header */}
        <div className="text-center mb-10">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#6ce3cf]/70">
            One-time setup
          </p>
          <h1
            className="mt-3 text-[clamp(1.8rem,4vw,2.8rem)] font-bold leading-tight tracking-[-0.025em] text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Choose your companion
          </h1>
          <p className="mt-3 text-[14px] leading-relaxed text-slate-400 max-w-md mx-auto">
            Your companion will be with you throughout your sessions — speaking,
            listening, and guiding. You can change this anytime in Settings.
          </p>
        </div>

        {/* Avatar cards grid */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {AVATAR_PERSONAS.map((persona) => {
            const isSelected = selected === persona.id;
            return (
              <button
                key={persona.id}
                type="button"
                onClick={() => setSelected(persona.id)}
                className="group relative flex flex-col items-center rounded-[24px] p-6 text-left transition-all duration-300"
                style={{
                  background: isSelected
                    ? `${persona.accentColor}12`
                    : "rgba(255,255,255,0.03)",
                  border: isSelected
                    ? `2px solid ${persona.accentColor}60`
                    : "2px solid rgba(255,255,255,0.07)",
                  transform: isSelected ? "translateY(-4px)" : "none",
                  boxShadow: isSelected
                    ? `0 12px 40px ${persona.accentColor}20`
                    : "none",
                }}
              >
                {/* Selected check */}
                {isSelected && (
                  <div
                    className="absolute top-3 right-3 flex h-6 w-6 items-center justify-center rounded-full"
                    style={{ background: persona.accentColor }}
                  >
                    <Check className="h-3.5 w-3.5 text-[#09111f]" strokeWidth={3} />
                  </div>
                )}

                {/* Avatar illustration — animated CSS avatar */}
                <div
                  className="relative mb-4 flex h-[100px] w-[100px] items-center justify-center rounded-full"
                  style={{
                    background: isSelected
                      ? `${persona.accentColor}18`
                      : "rgba(255,255,255,0.05)",
                    border: isSelected
                      ? `2px solid ${persona.accentColor}40`
                      : "2px solid rgba(255,255,255,0.08)",
                  }}
                >
                  {/* Idle breathing animation */}
                  {isSelected && (
                    <span
                      className="absolute inset-0 rounded-full animate-ping opacity-10"
                      style={{ background: persona.accentColor }}
                    />
                  )}
                  <span
                    className="select-none"
                    style={{ fontSize: "3.5rem", lineHeight: 1 }}
                    role="img"
                    aria-label={persona.name}
                  >
                    {persona.emoji}
                  </span>
                </div>

                <h3
                  className="text-[16px] font-semibold text-white"
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    color: isSelected ? persona.accentColor : "white",
                  }}
                >
                  {persona.name}
                </h3>
                <p className="mt-1 text-center text-[12px] leading-relaxed text-slate-400">
                  {persona.description}
                </p>

                {/* Voice description pill */}
                <div
                  className="mt-3 rounded-full px-3 py-1 text-[10px] font-medium"
                  style={{
                    background: `${persona.accentColor}10`,
                    color: persona.accentColor,
                    border: `1px solid ${persona.accentColor}25`,
                  }}
                >
                  {persona.voiceDescription}
                </div>
              </button>
            );
          })}
        </div>

        {/* Continue button */}
        <div className="mt-10 flex flex-col items-center gap-3">
          <button
            type="button"
            onClick={() => void handleContinue()}
            disabled={saving}
            className="flex items-center gap-3 rounded-[14px] px-8 py-4 text-[14px] font-semibold text-[#09111f] transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
            style={{
              background: "linear-gradient(135deg, #6ce3cf 0%, #2cb8c7 100%)",
              minWidth: "200px",
            }}
          >
            {saving ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#09111f]/20 border-t-[#09111f]" />
                Saving…
              </>
            ) : (
              "Continue to Dashboard"
            )}
          </button>

          {error && (
            <p className="text-[13px]" style={{ color: "#ff7b70" }}>{error}</p>
          )}

          <p className="text-[11px] text-slate-600">
            You can always change your companion later in Settings.
          </p>
        </div>
      </div>
    </div>
  );
}
