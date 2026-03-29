import { GoogleLogin } from "@react-oauth/google";
import { Activity, LockKeyhole, ShieldCheck, HeartPulse, Sparkles } from "lucide-react";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const { loginWithGoogleCredential, error, isLoading, clearError } = useAuth();
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const hasGoogleClientId = Boolean(googleClientId && googleClientId.trim());

  return (
    <div
      className="relative min-h-screen w-full overflow-hidden text-white"
      style={{ background: "#09111f" }}
    >
      {/* Background mesh */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 20% 0%, rgba(108,227,207,0.08) 0%, transparent 55%), " +
            "radial-gradient(ellipse 50% 40% at 90% 80%, rgba(255,201,107,0.05) 0%, transparent 50%)",
        }}
      />

      {/* Grain texture overlay */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")",
          backgroundSize: "128px 128px",
        }}
      />

      <div className="relative mx-auto flex min-h-screen max-w-[1300px] items-stretch gap-4 p-4 lg:gap-5 lg:p-5">

        {/* ── LEFT PANEL ─────────────────────────────── */}
        <div
          className="hidden flex-1 flex-col justify-between overflow-hidden rounded-[28px] p-10 lg:flex lg:p-14"
          style={{
            background: "linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          {/* Top content */}
          <div>
            {/* Brand pill */}
            <div className="inline-flex items-center gap-2.5 rounded-full px-4 py-2"
              style={{ background: "rgba(108,227,207,0.1)", border: "1px solid rgba(108,227,207,0.2)" }}>
              <HeartPulse className="h-3.5 w-3.5 text-[#6ce3cf]" />
              <span className="text-xs font-medium tracking-wide text-[#6ce3cf]">
                Smart Well-Being Assistant
              </span>
            </div>

            {/* Main headline */}
            <h1
              className="mt-10 text-[clamp(2.6rem,4.2vw,3.8rem)] font-bold leading-[1.04] tracking-[-0.03em]"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              <span className="text-white">Calm, private</span>
              <br />
              <span className="text-white">support.</span>
              <br />
              <span
                style={{
                  background: "linear-gradient(120deg, #6ce3cf 0%, #45d5cf 35%, #a3f0e0 70%, #6ce3cf 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundSize: "200% auto",
                }}
              >
                Designed for clarity.
              </span>
            </h1>

            <p className="mt-6 max-w-[420px] text-[15px] leading-[1.8] text-slate-400">
              A focused space to track your emotional well-being — with guided
              check-ins, personal insights, and support that respects your pace.
            </p>

            {/* Feature cards */}
            <div className="mt-10 grid gap-3 sm:grid-cols-3">
              <FeatureCard
                icon={<ShieldCheck className="h-4 w-4" />}
                title="Verified access"
                text="Your workspace stays personal and private."
              />
              <FeatureCard
                icon={<LockKeyhole className="h-4 w-4" />}
                title="Private records"
                text="All scores and conversations are yours alone."
              />
              <FeatureCard
                icon={<Activity className="h-4 w-4" />}
                title="Guided rhythm"
                text="One clear action. No visual overload."
              />
            </div>
          </div>

          {/* Bottom quote */}
          <div
            className="mt-12 rounded-[20px] p-5"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}
          >
            <div className="flex items-start gap-3">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-[#6ce3cf]/60" />
              <p className="text-[13px] italic leading-relaxed text-slate-500">
                "A focused layout helps people move from sign-in to support —
                without noise getting in the way."
              </p>
            </div>
          </div>
        </div>

        {/* ── RIGHT PANEL ─────────────────────────────── */}
        <div
          className="flex w-full flex-col justify-center rounded-[28px] p-6 sm:p-8 lg:w-[460px] lg:shrink-0"
          style={{
            background: "linear-gradient(145deg, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.015) 100%)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <div className="mx-auto w-full max-w-[360px]">

            {/* Mobile brand (hidden on desktop) */}
            <div className="mb-8 flex items-center gap-2.5 lg:hidden">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-xl"
                style={{ background: "linear-gradient(135deg, #6ce3cf, #1b9db6)" }}
              >
                <HeartPulse className="h-4.5 w-4.5 text-[#09111f]" />
              </div>
              <span className="text-sm font-semibold text-[#6ce3cf]">Well-Being AI</span>
            </div>

            {/* Sign in label */}
            <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-slate-500">
              Sign In
            </p>

            {/* Heading */}
            <h2
              className="mt-3 text-[2rem] font-bold leading-[1.1] tracking-[-0.025em] text-white"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              Continue with<br />Google
            </h2>

            <p className="mt-3 text-[14px] leading-relaxed text-slate-400">
              Your identity is verified and exchanged for a secure session.
              No passwords, no friction.
            </p>

            {/* Main auth card */}
            <div
              className="mt-7 rounded-[22px] p-1.5"
              style={{
                background: "linear-gradient(145deg, rgba(108,227,207,0.12) 0%, rgba(255,255,255,0.04) 100%)",
                border: "1px solid rgba(108,227,207,0.15)",
              }}
            >
              <div className="rounded-[18px] p-4" style={{ background: "rgba(9,17,31,0.6)" }}>
                {hasGoogleClientId ? (
                  <div className="space-y-3">
                    {/* Google button */}
                    <div
                      className="overflow-hidden rounded-[14px]"
                      style={{ background: "#fff", border: "1px solid rgba(0,0,0,0.08)" }}
                    >
                      <div className="flex flex-col items-center px-6 py-5">
                        <p className="mb-4 text-xs font-medium tracking-wide text-slate-500">
                          SIGN IN WITH YOUR GOOGLE ACCOUNT
                        </p>
                        <GoogleLogin
                          theme="outline"
                          shape="pill"
                          text="continue_with"
                          width="300"
                          onSuccess={(credentialResponse) => {
                            clearError();
                            if (!credentialResponse.credential) return;
                            void loginWithGoogleCredential(credentialResponse.credential);
                          }}
                          onError={() => { clearError(); }}
                        />
                      </div>
                    </div>

                    {/* Status */}
                    {!isLoading && !error && (
                      <div
                        className="flex items-center gap-2.5 rounded-[12px] px-4 py-3"
                        style={{
                          background: "rgba(108,227,207,0.07)",
                          border: "1px solid rgba(108,227,207,0.14)",
                        }}
                      >
                        <span
                          className="h-2 w-2 shrink-0 rounded-full"
                          style={{ background: "#6ce3cf", boxShadow: "0 0 6px #6ce3cf" }}
                        />
                        <p className="text-[13px] text-[#6ce3cf]/90">
                          Google sign-in is available
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    className="rounded-[14px] p-4"
                    style={{
                      background: "rgba(255,201,107,0.06)",
                      border: "1px solid rgba(255,201,107,0.15)",
                    }}
                  >
                    <p className="text-sm leading-relaxed text-amber-200/80">
                      Google sign-in is temporarily unavailable. Please ask an
                      administrator to verify the client configuration.
                    </p>
                  </div>
                )}

                {/* Loading */}
                {isLoading && (
                  <div
                    className="mt-3 flex items-center gap-3 rounded-[12px] px-4 py-3"
                    style={{ background: "rgba(108,227,207,0.06)" }}
                  >
                    <span
                      className="h-4 w-4 animate-spin rounded-full border-2 border-[#6ce3cf]/20 border-t-[#6ce3cf]"
                    />
                    <p className="text-sm text-[#6ce3cf]/80">Signing you in…</p>
                  </div>
                )}

                {/* Error */}
                {error && (
                  <div
                    className="mt-3 rounded-[12px] p-4"
                    style={{
                      background: "rgba(255,123,112,0.07)",
                      border: "1px solid rgba(255,123,112,0.18)",
                    }}
                  >
                    <p className="text-sm leading-relaxed text-[#ff7b70]/90">{error}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Security note */}
            <div
              className="mt-4 rounded-[18px] p-4"
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
              }}
            >
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#6ce3cf]/60" />
                <div>
                  <p className="text-[13px] font-medium text-white/70">
                    Why this feels quieter
                  </p>
                  <p className="mt-1.5 text-[12px] leading-relaxed text-slate-500">
                    Spacious typography, a single clear action, and no unnecessary
                    steps — so you arrive without extra cognitive load.
                  </p>
                </div>
              </div>
            </div>

            {/* Fine print */}
            <p className="mt-6 text-center text-[11px] leading-relaxed text-slate-600">
              By signing in you agree to keep this workspace personal.
              <br />
              Your data is never sold or shared.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  text,
}: {
  icon: React.ReactNode;
  title: string;
  text: string;
}) {
  return (
    <article
      className="group rounded-[18px] p-4 transition-all duration-300"
      style={{
        background: "rgba(255,255,255,0.025)",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.border = "1px solid rgba(108,227,207,0.2)";
        (e.currentTarget as HTMLElement).style.background = "rgba(108,227,207,0.04)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.border = "1px solid rgba(255,255,255,0.06)";
        (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.025)";
      }}
    >
      <div
        className="inline-flex rounded-xl p-2.5 text-[#6ce3cf]"
        style={{ background: "rgba(108,227,207,0.1)" }}
      >
        {icon}
      </div>
      <h3
        className="mt-3 text-[14px] font-semibold text-white"
        style={{ fontFamily: "'Space Grotesk', sans-serif" }}
      >
        {title}
      </h3>
      <p className="mt-1.5 text-[12px] leading-relaxed text-slate-500">{text}</p>
    </article>
  );
}