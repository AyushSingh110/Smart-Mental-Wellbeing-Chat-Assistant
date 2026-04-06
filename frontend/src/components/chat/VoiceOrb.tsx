/**
 * VoiceOrb — records microphone audio via MediaRecorder,
 * sends the blob to backend /voice/transcribe (Whisper),
 * and returns transcript + detected language code + confidence.
 *
 * This replaces browser SpeechRecognition which only works in English.
 * Whisper auto-detects Hindi, Bengali, Tamil, Telugu, etc. perfectly.
 */
import { useEffect, useRef, useState } from "react";
import { Mic, AudioLines, ShieldCheck, Square } from "lucide-react";
import { API_BASE_URL } from "../../lib/api";

type VoiceOrbProps = {
  token: string | null;
  onTranscript: (text: string, confidence?: number, languageCode?: string, languageName?: string) => void;
  disabled?: boolean;
  preferredLanguage?: string;
};

type RecordingState = "idle" | "listening" | "processing" | "error";

// ── Web Audio API waveform from microphone stream (20 frequency bars)
function useMicWaveform(stream: MediaStream | null) {
  const [bars, setBars] = useState<number[]>(Array(20).fill(0));
  const ctxRef      = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef      = useRef<number | null>(null);

  useEffect(() => {
    if (!stream) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      setBars(Array(20).fill(0));
      ctxRef.current?.close().catch(() => {});
      ctxRef.current    = null;
      analyserRef.current = null;
      return;
    }

    try {
      const ctx      = new AudioContext();
      ctxRef.current = ctx;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.6;
      analyserRef.current = analyser;
      ctx.createMediaStreamSource(stream).connect(analyser);

      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        const step = Math.floor(data.length / 20);
        setBars(Array.from({ length: 20 }, (_, i) =>
          Math.round((data[i * step] / 255) * 100),
        ));
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } catch {
      // Web Audio unavailable — bars stay silent
    }

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      ctxRef.current?.close().catch(() => {});
      ctxRef.current    = null;
      analyserRef.current = null;
    };
  }, [stream]);

  return bars;
}

// Best MIME type the browser supports for recording
function getSupportedMimeType(): string {
  const types = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
    "audio/mp4",
  ];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return "";
}

export function VoiceOrb({
  token,
  onTranscript,
  disabled = false,
  preferredLanguage = "en",
}: VoiceOrbProps) {
  const [state, setState]           = useState<RecordingState>("idle");
  const [transcript, setTranscript] = useState("");
  const [detectedLang, setDetectedLang] = useState<string>("");
  const [errorMsg, setErrorMsg]     = useState("");
  const [stream, setStream]         = useState<MediaStream | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef   = useRef<Blob[]>([]);

  const isListening  = state === "listening";
  const isProcessing = state === "processing";
  const waveformBars = useMicWaveform(stream);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      recorderRef.current?.stop();
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [stream]);

  async function startRecording() {
    if (disabled || !token) return;
    setErrorMsg("");
    setTranscript("");
    setDetectedLang("");

    let micStream: MediaStream;
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setErrorMsg("Microphone access denied. Please allow it in browser settings.");
      setState("error");
      return;
    }

    const mimeType = getSupportedMimeType();
    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(micStream, mimeType ? { mimeType } : undefined);
    } catch {
      setErrorMsg("MediaRecorder not supported in this browser.");
      setState("error");
      micStream.getTracks().forEach((t) => t.stop());
      return;
    }

    chunksRef.current = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
      micStream.getTracks().forEach((t) => t.stop());
      setStream(null);

      // Only block truly empty blobs (browser produced 0 audio bytes at all)
      if (blob.size === 0) {
        setErrorMsg("No audio captured. Please check your microphone.");
        setState("error");
        return;
      }

      setState("processing");
      await sendToWhisper(blob, mimeType);
    };

    recorder.onerror = () => {
      setErrorMsg("Recording failed.");
      setState("error");
      micStream.getTracks().forEach((t) => t.stop());
      setStream(null);
    };

    recorderRef.current = recorder;
    setStream(micStream);
    // No timeslice: browser buffers all audio and fires one ondataavailable on stop.
    // This is the most reliable approach on Windows Chrome/Edge — avoids 0-byte blobs
    // that happen when requestData() or short timeslices race with the stop event.
    recorder.start();
    setState("listening");
  }

  async function sendToWhisper(blob: Blob, mimeType: string) {
    if (!token) return;
    try {
      const formData = new FormData();
      // Determine file extension from MIME type
      const ext = mimeType.includes("ogg") ? "ogg"
                : mimeType.includes("mp4") ? "mp4"
                : mimeType.includes("wav") ? "wav"
                : "webm";
      formData.append("audio", blob, `recording.${ext}`);
      // Pass preferred language as a hint (Whisper will still auto-detect,
      // but uses this as a fallback when confidence < 75%)
      formData.append("language", preferredLanguage);

      const response = await fetch(`${API_BASE_URL}/voice/transcribe`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${response.status}`);
      }

      const data = await response.json() as {
        transcript:    string;
        language_code: string;
        language_name: string;
        confidence:    number;
        detected_lang: string;
      };

      const text = data.transcript?.trim() ?? "";
      if (!text) {
        setErrorMsg("No speech detected. Try speaking more clearly.");
        setState("error");
        return;
      }

      setTranscript(text);
      setDetectedLang(data.language_name);
      setState("idle");
      onTranscript(text, data.confidence, data.language_code, data.language_name);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Transcription failed.";
      setErrorMsg(msg);
      setState("error");
    }
  }

  function stopRecording() {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop(); // fires ondataavailable with all buffered audio, then onstop
    }
  }

  function toggleListening() {
    if (isListening) stopRecording();
    else if (state === "idle" || state === "error") void startRecording();
  }

  const isMediaRecorderSupported = typeof MediaRecorder !== "undefined";

  const STATUS_TEXT: Record<RecordingState, string> = {
    idle:       isMediaRecorderSupported
                  ? (token ? "Tap to start — speak in any language" : "Sign in to use voice")
                  : "Voice not supported in this browser",
    listening:  "Recording… tap again to stop",
    processing: "Transcribing with Whisper…",
    error:      errorMsg || "Something went wrong. Try again.",
  };

  const orbDisabled = !isMediaRecorderSupported || disabled || !token || isProcessing;

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
        <p className="mt-0.5 text-[11px] text-slate-600">
          Hindi, Tamil, Telugu, Bengali &amp; 10 more — auto-detected
        </p>
      </div>

      {/* Orb */}
      <div className="my-6 flex flex-col items-center gap-5">
        <button
          type="button"
          onClick={toggleListening}
          disabled={orbDisabled}
          aria-label={isListening ? "Stop recording" : "Start recording"}
          className="group relative flex h-[120px] w-[120px] items-center justify-center rounded-full transition-transform duration-200 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
          style={{ outline: "none" }}
        >
          {/* Pulse rings while recording */}
          {isListening && (
            <>
              <span className="absolute inset-0 rounded-full animate-ping opacity-20"
                style={{ background: "rgba(108,227,207,0.4)" }} />
              <span className="absolute -inset-3 rounded-full border border-[#6ce3cf]/20 animate-pulse" />
              <span className="absolute -inset-6 rounded-full border border-[#6ce3cf]/10 animate-pulse"
                style={{ animationDelay: "0.3s" }} />
            </>
          )}

          {/* Processing spinner rings */}
          {isProcessing && (
            <span className="absolute inset-0 rounded-full border-2 border-[#ffc96b]/30 border-t-[#ffc96b] animate-spin" />
          )}

          <div
            className="relative flex h-[120px] w-[120px] items-center justify-center rounded-full transition-all duration-300"
            style={{
              background: isListening
                ? "linear-gradient(135deg, #6ce3cf 0%, #2cb8c7 100%)"
                : isProcessing
                ? "rgba(255,201,107,0.1)"
                : "rgba(255,255,255,0.06)",
              border: isListening
                ? "2px solid rgba(108,227,207,0.5)"
                : isProcessing
                ? "2px solid rgba(255,201,107,0.3)"
                : "2px solid rgba(255,255,255,0.1)",
              boxShadow: isListening
                ? "0 0 40px rgba(108,227,207,0.35), 0 0 80px rgba(108,227,207,0.1)"
                : "none",
            }}
          >
            {isListening ? (
              <Square className="h-8 w-8 text-[#09111f]" strokeWidth={2} fill="currentColor" />
            ) : isProcessing ? (
              <span className="text-[11px] font-semibold text-[#ffc96b]">AI</span>
            ) : (
              <Mic className="h-10 w-10 text-slate-300 transition-colors group-hover:text-white" strokeWidth={1.5} />
            )}
          </div>
        </button>

        {/* Waveform visualizer — only while recording */}
        {isListening && (
          <div className="flex items-end gap-[2px]" style={{ height: 32, width: 120 }}>
            {waveformBars.map((h, i) => (
              <div
                key={i}
                className="rounded-full flex-1"
                style={{
                  height: `${Math.max(8, h)}%`,
                  background: "linear-gradient(to top, #6ce3cf, #2cb8c7)",
                  opacity: 0.5 + (h / 100) * 0.5,
                  transition: "height 0.08s ease",
                  minWidth: 3,
                }}
              />
            ))}
          </div>
        )}

        {/* Status text */}
        <p
          className="text-[13px] text-center leading-relaxed"
          style={{
            color: state === "error"      ? "#ff7b70"
                 : isListening            ? "#6ce3cf"
                 : isProcessing           ? "#ffc96b"
                 : "#64748b",
          }}
        >
          {STATUS_TEXT[state]}
        </p>

        {/* Transcript result with language badge */}
        {transcript && (
          <div
            className="w-full rounded-[14px] p-4"
            style={{
              background: "rgba(108,227,207,0.06)",
              border: "1px solid rgba(108,227,207,0.14)",
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6ce3cf]/60">
                Transcript
              </p>
              {detectedLang && (
                <span
                  className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  style={{
                    background: "rgba(108,227,207,0.12)",
                    border: "1px solid rgba(108,227,207,0.2)",
                    color: "#6ce3cf",
                  }}
                >
                  {detectedLang}
                </span>
              )}
            </div>
            <p className="text-[13px] leading-relaxed text-slate-300">{transcript}</p>
          </div>
        )}
      </div>

      {/* Info tiles */}
      <div className="mt-auto grid grid-cols-3 gap-2">
        {[
          { icon: <Mic className="h-3.5 w-3.5" />,         label: "Engine",       value: "OpenAI Whisper" },
          { icon: <AudioLines className="h-3.5 w-3.5" />,  label: "Languages",    value: "14 Indian + EN" },
          { icon: <ShieldCheck className="h-3.5 w-3.5" />, label: "Safety layer", value: "Context-aware" },
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
