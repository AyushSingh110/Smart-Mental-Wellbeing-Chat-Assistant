import { useEffect, useRef, useState } from "react";
import { AVATAR_PERSONAS } from "../../types";

type AvatarPanelProps = {
  avatarId: string;
  speakAudioUrl: string | null;
  speakDurationMs: number;
  isSpeaking: boolean;
  isListening: boolean;
  onSpeakEnd: () => void;
  crisisTier?: string | null;
};

// ── Web Audio API: AnalyserNode mouth amplitude tracking
function useMouthAmplitude(
  audioRef: React.RefObject<HTMLAudioElement | null>,
  isSpeaking: boolean,
) {
  const [amplitude, setAmplitude] = useState(0);
  const ctxRef      = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef   = useRef<MediaElementAudioSourceNode | null>(null);
  const rafRef      = useRef<number | null>(null);

  useEffect(() => {
    if (!isSpeaking || !audioRef.current) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      setAmplitude(0);
      return;
    }

    try {
      if (!ctxRef.current || ctxRef.current.state === "closed") {
        ctxRef.current = new AudioContext();
      }
      const ctx = ctxRef.current;

      if (!sourceRef.current && audioRef.current) {
        try {
          sourceRef.current = ctx.createMediaElementSource(audioRef.current);
        } catch {
          // already connected to another context
        }
      }

      if (!analyserRef.current && sourceRef.current) {
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.5;
        sourceRef.current.connect(analyser);
        analyser.connect(ctx.destination);
        analyserRef.current = analyser;
      }

      if (!analyserRef.current) {
        setAmplitude(0);
        return;
      }

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      const tick = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteTimeDomainData(dataArray);
        let sum = 0;
        for (const v of dataArray) {
          const norm = (v - 128) / 128;
          sum += norm * norm;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        setAmplitude(Math.min(rms * 5, 1));
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } catch {
      // Web Audio API unavailable — fall back to interval-based lip sync
    }

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [isSpeaking, audioRef]);

  return amplitude;
}

// ── Fallback lip sync: periodic toggle when Web Audio unavailable
function useFallbackLipSync(isSpeaking: boolean) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!isSpeaking) { setOpen(false); return; }
    const interval = setInterval(() => setOpen((v) => !v), 120);
    return () => clearInterval(interval);
  }, [isSpeaking]);
  return open ? 0.5 : 0;
}

export function AvatarPanel({
  avatarId,
  speakAudioUrl,
  speakDurationMs: _speakDurationMs,
  isSpeaking,
  isListening,
  onSpeakEnd,
  crisisTier,
}: AvatarPanelProps) {
  const persona   = AVATAR_PERSONAS.find((p) => p.id === avatarId) ?? AVATAR_PERSONAS[0];
  const accent    = persona.accentColor;
  const audioRef  = useRef<HTMLAudioElement | null>(null);
  const [blink, setBlink] = useState(false);
  const [webAudioActive, setWebAudioActive] = useState(false);

  const webAudioAmplitude = useMouthAmplitude(audioRef, isSpeaking && webAudioActive);
  const fallbackAmplitude = useFallbackLipSync(isSpeaking && !webAudioActive);
  const amplitude = webAudioActive ? webAudioAmplitude : fallbackAmplitude;

  // Check Web Audio API availability
  useEffect(() => {
    setWebAudioActive(typeof AudioContext !== "undefined" || typeof (window as any).webkitAudioContext !== "undefined");
  }, []);

  // Eye blink: random interval 2-6s
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const scheduleBlink = () => {
      const delay = 2000 + Math.random() * 4000;
      timer = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 150);
        scheduleBlink();
      }, delay);
    };
    scheduleBlink();
    return () => clearTimeout(timer);
  }, []);

  // Play audio when speakAudioUrl changes
  useEffect(() => {
    if (!speakAudioUrl || !audioRef.current) return;
    audioRef.current.src = speakAudioUrl;
    void audioRef.current.play().catch(() => {});
  }, [speakAudioUrl]);

  const isCrisis     = crisisTier === "active" || crisisTier === "passive";
  const mouthOpen    = isSpeaking ? Math.max(amplitude, 0.05) : 0;
  const mouthHeight  = 4 + mouthOpen * 14;
  const mouthWidth   = 24 + mouthOpen * 8;

  return (
    <div className="flex flex-col items-center gap-3">
      {/* ── Portrait video-call frame (9:16 aspect) */}
      <div
        className="relative w-full overflow-hidden rounded-2xl"
        style={{
          aspectRatio: "9/16",
          maxHeight: "340px",
          background: "#172032",
          border: isCrisis
            ? "2px solid rgba(192,64,64,0.6)"
            : "1px solid rgba(55,75,105,0.5)",
          animation: isCrisis ? "crisisPulse 1.5s ease-in-out infinite" : undefined,
        }}
      >
        {/* LIVE dot */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-1.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{
              background: isCrisis ? "#c04040" : (isSpeaking ? "#4a84d6" : "#3d8a5c"),
              animation: "livePulse 2s ease-in-out infinite",
            }}
          />
          <span className="text-[10px] font-semibold uppercase tracking-widest"
            style={{ color: isCrisis ? "#c04040" : "#7a92a8" }}>
            {isCrisis ? "SOS" : "LIVE"}
          </span>
        </div>

        {/* Avatar portrait area */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 pt-8">
          {/* Head + face */}
          <div className="relative flex flex-col items-center">
            <div
              className="relative flex items-center justify-center rounded-full"
              style={{
                width: 88,
                height: 88,
                background: "#1d2940",
                border: "2px solid rgba(55,75,105,0.5)",
                animation: isSpeaking
                  ? "headBob 0.8s ease-in-out infinite"
                  : "avatarBreathe 4s ease-in-out infinite",
              }}
            >
              <span
                style={{ fontSize: "3.2rem", lineHeight: 1, userSelect: "none" }}
                role="img"
                aria-label={persona.name}
              >
                {persona.emoji}
              </span>
            </div>

            {/* SVG mouth driven by Web Audio amplitude */}
            <div
              className="absolute"
              style={{ bottom: -8, left: "50%", transform: "translateX(-50%)" }}
            >
              <svg
                width={mouthWidth + 12}
                height={mouthHeight + 12}
                style={{ overflow: "visible", display: "block" }}
              >
                <ellipse
                  cx={(mouthWidth + 12) / 2}
                  cy={(mouthHeight + 12) / 2}
                  rx={mouthWidth / 2}
                  ry={Math.max(2, mouthHeight / 2)}
                  fill={isSpeaking ? "rgba(74,132,214,0.35)" : "transparent"}
                  stroke="#4a84d6"
                  strokeWidth={1.5}
                  opacity={isSpeaking ? 0.9 : 0.25}
                  style={{ transition: "rx 0.06s ease, ry 0.06s ease" }}
                />
                {mouthOpen > 0.2 && (
                  <line
                    x1={(mouthWidth + 12) / 2 - mouthWidth / 2 + 4}
                    y1={(mouthHeight + 12) / 2}
                    x2={(mouthWidth + 12) / 2 + mouthWidth / 2 - 4}
                    y2={(mouthHeight + 12) / 2}
                    stroke="rgba(255,255,255,0.35)"
                    strokeWidth={0.8}
                  />
                )}
              </svg>
            </div>

            {/* Eye blink overlays */}
            {blink && (
              <>
                <div className="absolute" style={{ top: 28, left: 20, width: 10, height: 3, background: "#172032", borderRadius: 2 }} />
                <div className="absolute" style={{ top: 28, right: 20, width: 10, height: 3, background: "#172032", borderRadius: 2 }} />
              </>
            )}
          </div>

          {/* Name + status */}
          <div className="flex flex-col items-center gap-1">
            <p className="text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              {persona.name}
            </p>
            <p className="text-[11px]" style={{ color: isCrisis ? "#c04040" : "#4a84d6" }}>
              {isListening ? "Listening…" : isSpeaking ? "Speaking…" : isCrisis ? "Crisis Support" : "Ready"}
            </p>
          </div>

          {/* Speaking waveform bars */}
          {isSpeaking && (
            <div className="flex items-end gap-1" style={{ height: 20 }}>
              {[0.4, 0.7, 1.0, 0.7, 0.4].map((scale, i) => (
                <div
                  key={i}
                  className="rounded-full"
                  style={{
                    width: 3,
                    height: Math.max(4, 4 + amplitude * 16 * scale),
                    background: "#4a84d6",
                    opacity: 0.5 + amplitude * 0.5,
                    transition: "height 0.06s ease",
                  }}
                />
              ))}
            </div>
          )}

          {/* Listening pulse rings */}
          {isListening && !isSpeaking && (
            <div className="relative flex items-center justify-center" style={{ width: 40, height: 40 }}>
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="absolute rounded-full"
                  style={{
                    width: 40 + i * 16,
                    height: 40 + i * 16,
                    border: "1px solid rgba(74,132,214,0.5)",
                    opacity: 0.35 - i * 0.1,
                    animation: `listenRing 1.6s ease-out ${i * 0.4}s infinite`,
                  }}
                />
              ))}
              <div className="h-3 w-3 rounded-full" style={{ background: "#4a84d6" }} />
            </div>
          )}
        </div>

        {/* Bottom gradient */}
        <div
          className="absolute inset-x-0 bottom-0 h-16"
          style={{ background: "linear-gradient(to top, #172032, transparent)" }}
        />
      </div>

      {/* Hidden audio element */}
      <audio ref={audioRef} onEnded={onSpeakEnd} style={{ display: "none" }} />

      {/* Keyframe styles */}
      <style>{`
        @keyframes avatarBreathe {
          0%, 100% { transform: scale(1); }
          50%       { transform: scale(1.025); }
        }
        @keyframes headBob {
          0%, 100% { transform: translateY(0); }
          50%       { transform: translateY(-3px); }
        }
        @keyframes livePulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.35; }
        }
        @keyframes listenRing {
          0%   { transform: scale(0.7); opacity: 0.5; }
          100% { transform: scale(1.4); opacity: 0; }
        }
        @keyframes crisisPulse {
          0%, 100% { border-color: rgba(192,64,64,0.6); }
          50%       { border-color: rgba(192,64,64,0.9); }
        }
      `}</style>
    </div>
  );
}
