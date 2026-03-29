import { useEffect, useRef, useState } from "react";
import { Mic, MicOff, AudioLines, ShieldCheck } from "lucide-react";

type VoiceOrbProps = {
  onTranscript: (text: string) => void;
  disabled?: boolean;
};

type RecordingState = "idle" | "listening" | "processing" | "error";

export function VoiceOrb({ onTranscript, disabled = false }: VoiceOrbProps) {
  const [state, setState]           = useState<RecordingState>("idle");
  const [transcript, setTranscript] = useState("");
  const [errorMsg, setErrorMsg]     = useState("");
  const recognitionRef              = useRef<SpeechRecognition | null>(null);

  // Check browser support
  const SpeechRecognitionAPI =
    typeof window !== "undefined"
      ? window.SpeechRecognition ?? (window as any).webkitSpeechRecognition
      : null;
  const isSupported = Boolean(SpeechRecognitionAPI);

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
    };
  }, []);

  function startListening() {
    if (!isSupported || disabled) return;

    setErrorMsg("");
    setTranscript("");

    const recognition = new SpeechRecognitionAPI!();
    recognitionRef.current = recognition;

    recognition.continuous      = true;
    recognition.interimResults  = true;
    recognition.lang            = "";      // auto-detect language
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setState("listening");

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      let final   = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += t;
        else interim += t;
      }
      setTranscript(final || interim);
      if (final) {
        onTranscript(final.trim());
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const friendly: Record<string, string> = {
        "not-allowed":      "Microphone access was denied. Please allow it in browser settings.",
        "no-speech":        "No speech detected. Try speaking again.",
        "network":          "Network issue. Check your connection.",
        "audio-capture":    "Could not capture audio. Check your microphone.",
        "aborted":          "",
      };
      const msg = friendly[event.error] ?? `Error: ${event.error}`;
      if (msg) setErrorMsg(msg);
      setState("error");
    };

    recognition.onend = () => {
      setState((s) => (s === "listening" ? "idle" : s));
    };

    try {
      recognition.start();
    } catch {
      setErrorMsg("Could not start voice recognition.");
      setState("error");
    }
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setState("idle");
  }

  function toggleListening() {
    if (state === "listening") stopListening();
    else startListening();
  }

  const isActive = state === "listening";

  const STATUS_TEXT: Record<RecordingState, string> = {
    idle:       isSupported ? "Tap to start speaking" : "Voice not supported in this browser",
    listening:  "Listening… speak now",
    processing: "Processing…",
    error:      errorMsg || "Something went wrong",
  };

  return (
    <article
      className="flex flex-col rounded-[20px] p-5"
      style={{
        background: "rgba(255,255,255,0.028)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Header */}
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
          Voice input
        </p>
        <h3
          className="mt-1.5 text-[16px] font-semibold text-white"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          Speak in any language
        </h3>
      </div>

      {/* Orb */}
      <div className="my-6 flex flex-col items-center gap-5">
        <button
          type="button"
          onClick={toggleListening}
          disabled={!isSupported || disabled}
          aria-label={isActive ? "Stop recording" : "Start recording"}
          className="group relative flex h-[120px] w-[120px] items-center justify-center rounded-full transition-transform duration-200 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
          style={{ outline: "none" }}
        >
          {/* Animated rings when active */}
          {isActive && (
            <>
              <span
                className="absolute inset-0 rounded-full animate-ping opacity-20"
                style={{ background: "rgba(108,227,207,0.4)" }}
              />
              <span
                className="absolute -inset-3 rounded-full border border-[#6ce3cf]/20 animate-pulse"
              />
              <span
                className="absolute -inset-6 rounded-full border border-[#6ce3cf]/10 animate-pulse"
                style={{ animationDelay: "0.3s" }}
              />
            </>
          )}

          {/* Core button */}
          <div
            className="relative flex h-[120px] w-[120px] items-center justify-center rounded-full transition-all duration-300"
            style={{
              background: isActive
                ? "linear-gradient(135deg, #6ce3cf 0%, #2cb8c7 100%)"
                : "rgba(255,255,255,0.06)",
              border: isActive
                ? "2px solid rgba(108,227,207,0.5)"
                : "2px solid rgba(255,255,255,0.1)",
              boxShadow: isActive
                ? "0 0 40px rgba(108,227,207,0.35), 0 0 80px rgba(108,227,207,0.1)"
                : "none",
            }}
          >
            {isActive ? (
              <MicOff className="h-10 w-10 text-[#09111f]" strokeWidth={2} />
            ) : (
              <Mic
                className="h-10 w-10 text-slate-300 transition-colors group-hover:text-white"
                strokeWidth={1.5}
              />
            )}
          </div>
        </button>

        {/* Status text */}
        <p
          className="text-[13px] text-center"
          style={{ color: state === "error" ? "#ff7b70" : state === "listening" ? "#6ce3cf" : "#64748b" }}
        >
          {STATUS_TEXT[state]}
        </p>

        {/* Live transcript preview */}
        {transcript && (
          <div
            className="w-full rounded-[14px] p-4"
            style={{
              background: "rgba(108,227,207,0.06)",
              border: "1px solid rgba(108,227,207,0.14)",
            }}
          >
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6ce3cf]/60 mb-2">
              Transcript
            </p>
            <p className="text-[13px] leading-relaxed text-slate-300">{transcript}</p>
          </div>
        )}
      </div>

      {/* Info tiles */}
      <div className="mt-auto grid grid-cols-3 gap-2">
        {[
          { icon: <Mic className="h-3.5 w-3.5" />,          label: "Voice space",    value: "Auto language" },
          { icon: <AudioLines className="h-3.5 w-3.5" />,   label: "Mode",           value: "Speech to text" },
          { icon: <ShieldCheck className="h-3.5 w-3.5" />,  label: "Safety layer",   value: "Context-aware" },
        ].map((item) => (
          <div
            key={item.label}
            className="rounded-[12px] p-3"
            style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
            }}
          >
            <div className="text-[#6ce3cf]/70">{item.icon}</div>
            <p className="mt-2 text-[10px] uppercase tracking-[0.16em] text-slate-600">{item.label}</p>
            <p className="mt-1 text-[11px] font-medium text-slate-400">{item.value}</p>
          </div>
        ))}
      </div>
    </article>
  );
}