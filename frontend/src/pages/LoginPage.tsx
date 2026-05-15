import { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { Activity, Globe, HeartPulse, LockKeyhole, ShieldCheck } from "lucide-react";
import { useAuth } from "../lib/auth";
import { SUPPORTED_LANGUAGES } from "../types";

export function LoginPage() {
  const { loginWithGoogleCredential, error, isLoading, clearError } = useAuth();
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const hasGoogleClientId = Boolean(googleClientId && googleClientId.trim());
  const [preferredLang, setPreferredLang] = useState("en");

  async function handleGoogleSuccess(credential: string) {
    clearError();
    window.localStorage.setItem("preferred_language_pending", preferredLang);
    await loginWithGoogleCredential(credential);
  }

  return (
    <div className="min-h-screen w-full" style={{ background: "#0c1220" }}>
      <div className="mx-auto flex min-h-screen max-w-[1200px] items-stretch gap-0">

        {/* ── LEFT PANEL ─────────────────────────────────── */}
        <div
          className="hidden flex-1 flex-col justify-between p-12 lg:flex xl:p-16"
          style={{ borderRight: "1px solid rgba(55,75,105,0.4)" }}
        >
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div
              className="flex h-9 w-9 items-center justify-center rounded-xl"
              style={{ background: "#4a84d6" }}
            >
              <HeartPulse className="h-5 w-5 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Smart Well-Being Assistant
            </span>
          </div>

          {/* Main content */}
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.25em]" style={{ color: "#4a84d6" }}>
              Mental Wellbeing Support
            </p>

            <h1
              className="mt-5 text-[clamp(2.2rem,3.6vw,3.4rem)] font-bold leading-[1.1] tracking-[-0.02em] text-white"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              Calm, private
              <br />
              support designed
              <br />
              for clarity.
            </h1>

            <p className="mt-6 max-w-[400px] text-[15px] leading-[1.8]" style={{ color: "#7a92a8" }}>
              A focused space to track your emotional well-being — with guided
              check-ins, personal insights, and support that respects your pace.
            </p>

            {/* Feature list */}
            <div className="mt-10 space-y-3">
              {[
                { icon: ShieldCheck, title: "Private and secure",    text: "Your workspace stays personal. No data is sold or shared." },
                { icon: LockKeyhole, title: "Confidential records",  text: "All scores and conversations are linked only to your account." },
                { icon: Activity,    title: "Evidence-based support", text: "CBT-guided responses with crisis detection and safety checks." },
              ].map(({ icon: Icon, title, text }) => (
                <div key={title} className="flex items-start gap-3">
                  <div
                    className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg"
                    style={{ background: "rgba(74,132,214,0.12)", border: "1px solid rgba(74,132,214,0.2)" }}
                  >
                    <Icon className="h-3.5 w-3.5" style={{ color: "#4a84d6" }} />
                  </div>
                  <div>
                    <p className="text-[13px] font-semibold text-white">{title}</p>
                    <p className="text-[12px] leading-relaxed" style={{ color: "#4a6278" }}>{text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom note */}
          <p className="text-[12px]" style={{ color: "#4a6278" }}>
            Supports 14 Indian languages · Crisis detection · CBT-guided responses
          </p>
        </div>

        {/* ── RIGHT PANEL ────────────────────────────────── */}
        <div
          className="flex w-full flex-col justify-center p-6 sm:p-10 lg:w-[420px] lg:shrink-0 xl:w-[460px]"
          style={{ background: "#111c2e" }}
        >
          <div className="mx-auto w-full max-w-[340px]">

            {/* Mobile brand */}
            <div className="mb-8 flex items-center gap-2.5 lg:hidden">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: "#4a84d6" }}>
                <HeartPulse className="h-4 w-4 text-white" />
              </div>
              <span className="text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Well-Being AI
              </span>
            </div>

            <p className="text-[10px] font-bold uppercase tracking-[0.25em]" style={{ color: "#4a6278" }}>
              Sign In
            </p>

            <h2
              className="mt-3 text-[1.75rem] font-bold leading-[1.15] tracking-[-0.02em] text-white"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              Continue with<br />Google
            </h2>

            <p className="mt-2.5 text-[13px] leading-relaxed" style={{ color: "#7a92a8" }}>
              Your identity is verified and exchanged for a secure session.
              No passwords required.
            </p>

            {/* Language selector */}
            <div className="mt-6">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="h-3.5 w-3.5" style={{ color: "#4a6278" }} />
                <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#4a6278" }}>
                  Preferred language
                </p>
              </div>
              <select
                value={preferredLang}
                onChange={(e) => setPreferredLang(e.target.value)}
                className="field w-full px-3 py-2.5 text-[13px] text-white outline-none cursor-pointer rounded-[10px]"
                style={{
                  background: "#0c1220",
                  border: "1px solid rgba(55,75,105,0.5)",
                  color: "#c8d8ea",
                }}
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code} style={{ background: "#0c1220" }}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
              <p className="mt-1.5 text-[11px]" style={{ color: "#4a6278" }}>
                The assistant will respond in this language by default.
              </p>
            </div>

            {/* Auth area */}
            <div
              className="mt-5 rounded-2xl p-1"
              style={{
                background: "rgba(74,132,214,0.08)",
                border: "1px solid rgba(74,132,214,0.2)",
              }}
            >
              <div
                className="rounded-[14px] p-4"
                style={{ background: "#0c1220" }}
              >
                {hasGoogleClientId ? (
                  <div className="space-y-3">
                    <div
                      className="overflow-hidden rounded-xl"
                      style={{ background: "#fff", border: "1px solid rgba(0,0,0,0.08)" }}
                    >
                      <div className="flex flex-col items-center px-5 py-5">
                        <p className="mb-4 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                          Sign in with your Google account
                        </p>
                        <GoogleLogin
                          theme="outline"
                          shape="pill"
                          text="continue_with"
                          width="300"
                          onSuccess={(credentialResponse) => {
                            if (!credentialResponse.credential) return;
                            void handleGoogleSuccess(credentialResponse.credential);
                          }}
                          onError={() => { clearError(); }}
                        />
                      </div>
                    </div>

                    {!isLoading && !error && (
                      <div
                        className="flex items-center gap-2.5 rounded-xl px-3 py-2.5"
                        style={{ background: "rgba(61,138,92,0.08)", border: "1px solid rgba(61,138,92,0.2)" }}
                      >
                        <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: "#3d8a5c" }} />
                        <p className="text-[12px]" style={{ color: "#3d8a5c" }}>
                          Google sign-in is available
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    className="rounded-xl p-4"
                    style={{ background: "rgba(181,130,42,0.08)", border: "1px solid rgba(181,130,42,0.2)" }}
                  >
                    <p className="text-[13px] leading-relaxed" style={{ color: "#b5822a" }}>
                      Google sign-in is temporarily unavailable. Please ask an
                      administrator to verify the client configuration.
                    </p>
                  </div>
                )}

                {isLoading && (
                  <div
                    className="mt-3 flex items-center gap-3 rounded-xl px-3 py-2.5"
                    style={{ background: "rgba(74,132,214,0.08)" }}
                  >
                    <span className="h-4 w-4 rounded-full border-2 animate-spinSlow" style={{ borderColor: "rgba(74,132,214,0.2)", borderTopColor: "#4a84d6" }} />
                    <p className="text-[13px]" style={{ color: "#4a84d6" }}>Signing you in…</p>
                  </div>
                )}

                {error && (
                  <div
                    className="mt-3 rounded-xl p-3"
                    style={{ background: "rgba(192,64,64,0.08)", border: "1px solid rgba(192,64,64,0.2)" }}
                  >
                    <p className="text-[13px] leading-relaxed" style={{ color: "#c04040" }}>{error}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Security note */}
            <div
              className="mt-4 flex items-start gap-3 rounded-xl p-4"
              style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.3)" }}
            >
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" style={{ color: "#3d8a5c" }} />
              <div>
                <p className="text-[12px] font-medium text-white">Your data stays private</p>
                <p className="mt-1 text-[11px] leading-relaxed" style={{ color: "#4a6278" }}>
                  Conversations, scores, and journals are stored securely and are
                  never sold, shared, or used for advertising.
                </p>
              </div>
            </div>

            <p className="mt-5 text-center text-[11px] leading-relaxed" style={{ color: "#4a6278" }}>
              By signing in you agree to keep this workspace personal.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
