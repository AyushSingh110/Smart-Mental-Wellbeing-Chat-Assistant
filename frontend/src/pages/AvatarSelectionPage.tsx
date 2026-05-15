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
      className="min-h-screen w-full flex items-center justify-center p-4"
      style={{ background: "#0c1220" }}
    >
      <div className="mx-auto w-full max-w-[900px]">
        {/* Header */}
        <div className="text-center mb-10">
          <p className="label-caps" style={{ color: "#4a84d6" }}>
            One-time setup
          </p>
          <h1
            className="mt-3 text-[clamp(1.8rem,4vw,2.6rem)] font-bold leading-tight tracking-tight text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Choose your companion
          </h1>
          <p className="mt-3 text-[14px] leading-relaxed max-w-md mx-auto" style={{ color: "#7a92a8" }}>
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
                className="relative flex flex-col items-center rounded-2xl p-6 text-left transition-all duration-200"
                style={{
                  background: isSelected ? `${persona.accentColor}10` : "#172032",
                  border: isSelected
                    ? `2px solid ${persona.accentColor}50`
                    : "2px solid rgba(55,75,105,0.45)",
                }}
              >
                {/* Selected check */}
                {isSelected && (
                  <div
                    className="absolute top-3 right-3 flex h-6 w-6 items-center justify-center rounded-full"
                    style={{ background: persona.accentColor }}
                  >
                    <Check className="h-3.5 w-3.5 text-white" strokeWidth={3} />
                  </div>
                )}

                {/* Avatar portrait */}
                <div
                  className="relative mb-4 flex h-[100px] w-[100px] items-center justify-center rounded-full"
                  style={{
                    background: isSelected ? `${persona.accentColor}14` : "#1d2940",
                    border: isSelected
                      ? `2px solid ${persona.accentColor}35`
                      : "2px solid rgba(55,75,105,0.4)",
                  }}
                >
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
                  className="text-[16px] font-semibold"
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    color: isSelected ? persona.accentColor : "white",
                  }}
                >
                  {persona.name}
                </h3>
                <p className="mt-1 text-center text-[12px] leading-relaxed" style={{ color: "#7a92a8" }}>
                  {persona.description}
                </p>

                {/* Voice description pill */}
                <div
                  className="mt-3 rounded-full px-3 py-1 text-[10px] font-medium"
                  style={{
                    background: `${persona.accentColor}10`,
                    color: persona.accentColor,
                    border: `1px solid ${persona.accentColor}28`,
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
            className="flex items-center gap-3 rounded-[14px] px-8 py-4 text-[14px] font-semibold text-white transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
            style={{ background: "#4a84d6", minWidth: "200px" }}
          >
            {saving ? (
              <>
                <span
                  className="h-4 w-4 rounded-full border-2 border-white/20 border-t-white animate-spinSlow"
                />
                Saving…
              </>
            ) : (
              "Continue to Dashboard"
            )}
          </button>

          {error && (
            <p className="text-[13px]" style={{ color: "#c04040" }}>{error}</p>
          )}

          <p className="text-[11px]" style={{ color: "#4a6278" }}>
            You can always change your companion later in Settings.
          </p>
        </div>
      </div>
    </div>
  );
}
