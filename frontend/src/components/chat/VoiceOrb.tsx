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
      className="flex flex-col rounded-2xl p-5"
      style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
    >
      {/* Header */}
      <div>
        <p className="label-caps">Voice input</p>
        <h3 className="mt-1.5 text-[15px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          Speak in any language
        </h3>
        <p className="mt-0.5 text-[11px]" style={{ color: "#4a6278" }}>
          Hindi, Tamil, Telugu, Bengali &amp; 10 more — auto-detected
        </p>
      </div>

      {/* Orb */}
      <div className="my-5 flex flex-col items-center gap-4">
        <button
          type="button"
          onClick={toggleListening}
          disabled={orbDisabled}
          aria-label={isListening ? "Stop recording" : "Start recording"}
          className="group relative flex h-[100px] w-[100px] items-center justify-center rounded-full transition-transform duration-150 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
          style={{ outline: "none" }}
        >
          {/* Pulse ring while recording */}
          {isListening && (
            <span className="absolute inset-0 rounded-full animate-ping opacity-15"
              style={{ background: "rgba(74,132,214,0.35)" }} />
          )}

          {/* Processing spinner */}
          {isProcessing && (
            <span className="absolute inset-0 rounded-full border-2 animate-spinSlow"
              style={{ borderColor: "rgba(181,130,42,0.25)", borderTopColor: "#b5822a" }} />
          )}

          <div
            className="relative flex h-[100px] w-[100px] items-center justify-center rounded-full transition-all duration-200"
            style={{
              background: isListening
                ? "#4a84d6"
                : isProcessing
                ? "rgba(181,130,42,0.1)"
                : "#1d2940",
              border: isListening
                ? "2px solid rgba(74,132,214,0.6)"
                : isProcessing
                ? "2px solid rgba(181,130,42,0.35)"
                : "2px solid rgba(55,75,105,0.5)",
            }}
          >
            {isListening ? (
              <Square className="h-7 w-7 text-white" strokeWidth={2} fill="currentColor" />
            ) : isProcessing ? (
              <span className="text-[11px] font-semibold" style={{ color: "#b5822a" }}>AI</span>
            ) : (
              <Mic className="h-9 w-9 transition-colors" style={{ color: "#7a92a8" }} strokeWidth={1.5} />
            )}
          </div>
        </button>

        {/* Waveform while recording */}
        {isListening && (
          <div className="flex items-end gap-[2px]" style={{ height: 28, width: 100 }}>
            {waveformBars.map((h, i) => (
              <div
                key={i}
                className="rounded-full flex-1"
                style={{
                  height: `${Math.max(8, h)}%`,
                  background: "#4a84d6",
                  opacity: 0.4 + (h / 100) * 0.6,
                  transition: "height 0.08s ease",
                  minWidth: 3,
                }}
              />
            ))}
          </div>
        )}

        {/* Status text */}
        <p
          className="text-[12px] text-center leading-relaxed"
          style={{
            color: state === "error"  ? "#c04040"
                 : isListening        ? "#4a84d6"
                 : isProcessing       ? "#b5822a"
                 : "#4a6278",
          }}
        >
          {STATUS_TEXT[state]}
        </p>

        {/* Transcript result */}
        {transcript && (
          <div
            className="w-full rounded-xl p-4"
            style={{ background: "rgba(74,132,214,0.07)", border: "1px solid rgba(74,132,214,0.18)" }}
          >
            <div className="flex items-center justify-between mb-2">
              <p className="text-[10px] font-bold uppercase tracking-[0.18em]" style={{ color: "#4a6278" }}>
                Transcript
              </p>
              {detectedLang && (
                <span
                  className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                  style={{ background: "rgba(74,132,214,0.12)", border: "1px solid rgba(74,132,214,0.22)", color: "#4a84d6" }}
                >
                  {detectedLang}
                </span>
              )}
            </div>
            <p className="text-[13px] leading-relaxed" style={{ color: "#c8d8ea" }}>{transcript}</p>
          </div>
        )}
      </div>

      {/* Info tiles */}
      <div className="mt-auto grid grid-cols-3 gap-2">
        {[
          { icon: <Mic className="h-3 w-3" />,         label: "Engine",       value: "Whisper" },
          { icon: <AudioLines className="h-3 w-3" />,  label: "Languages",    value: "14 + EN" },
          { icon: <ShieldCheck className="h-3 w-3" />, label: "Safety",       value: "Context-aware" },
        ].map((item) => (
          <div
            key={item.label}
            className="rounded-xl p-2.5"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(55,75,105,0.35)" }}
          >
            <div style={{ color: "#4a6278" }}>{item.icon}</div>
            <p className="mt-1.5 text-[9px] uppercase tracking-[0.16em]" style={{ color: "#4a6278" }}>{item.label}</p>
            <p className="mt-0.5 text-[10px] font-medium" style={{ color: "#7a92a8" }}>{item.value}</p>
          </div>
        ))}
      </div>
    </article>
  );
}
