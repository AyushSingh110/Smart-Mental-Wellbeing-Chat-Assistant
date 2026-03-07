#voice_service.py
from __future__ import annotations

import io
import logging
import os
import re
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Voice profiles ────────────────────────────────────────────────────────────

_PYTTSX3_PROFILES: dict[str, dict] = {
    "crisis":  {"rate": 138, "volume": 0.95},
    "sadness": {"rate": 152, "volume": 0.90},
    "fear":    {"rate": 156, "volume": 0.90},
    "anxiety": {"rate": 158, "volume": 0.90},
    "anger":   {"rate": 152, "volume": 0.88},
    "stress":  {"rate": 160, "volume": 0.92},
    "neutral": {"rate": 174, "volume": 1.00},
    "default": {"rate": 168, "volume": 0.95},
}

_GTTS_SLOW: dict[str, bool] = {
    "crisis": True,  "sadness": True,  "fear": True,
    "anxiety": True, "anger": True,    "stress": False,
    "neutral": False, "default": False,
}

# Blobs smaller than this are silent/header-only — skip transcription
_MIN_AUDIO_BYTES = 3_000


class VoiceService:

    def __init__(self):
        self._whisper_model = None
        self._tts_backend   = self._detect_tts()
        self._stt_backend   = self._detect_stt()
        logger.info("VoiceService | STT=%s | TTS=%s", self._stt_backend, self._tts_backend)

    # ── Detection ─────────────────────────────────────────────────────────────

    def _detect_stt(self) -> str:
        try:
            from faster_whisper import WhisperModel  # noqa
            return "whisper"
        except ImportError:
            pass
        try:
            import speech_recognition  # noqa
            return "google_sr"
        except ImportError:
            pass
        return "none"

    def _detect_tts(self) -> str:
        try:
            import pyttsx3  # noqa
            return "pyttsx3"
        except ImportError:
            pass
        try:
            from gtts import gTTS  # noqa
            return "gtts"
        except ImportError:
            pass
        return "none"

    # ── WAV conversion ─────────────────────────────────────────────────────────

    def _to_wav_file(self, audio_bytes: bytes, fmt: str) -> str:
        """
        Write audio_bytes to a temp WAV file (mono 16 kHz).
        Returns the path. Caller must delete the file.
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()

        if fmt == "wav":
            Path(tmp.name).write_bytes(audio_bytes)
            return tmp.name

        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
            seg = seg.set_channels(1).set_frame_rate(16_000).set_sample_width(2)
            seg.export(tmp.name, format="wav")
        except Exception as exc:
            logger.warning("pydub conversion failed (%s) — writing raw bytes.", exc)
            Path(tmp.name).write_bytes(audio_bytes)

        return tmp.name

    # ── STT ───────────────────────────────────────────────────────────────────

    def transcribe(self, audio_bytes: bytes, audio_format: str = "webm") -> str:
        """
        Returns transcript string, or "" for silence / no speech.
        Raises RuntimeError only when no backend is installed.
        """
        if self._stt_backend == "none":
            raise RuntimeError(
                "No STT backend. Install: pip install faster-whisper"
            )

        # Guard: tiny blob = silence or just container headers
        if len(audio_bytes) < _MIN_AUDIO_BYTES:
            logger.debug("Audio blob too small (%d B) — likely silent.", len(audio_bytes))
            return ""

        wav_path = self._to_wav_file(audio_bytes, audio_format)
        try:
            if self._stt_backend == "whisper":
                return self._whisper(wav_path)
            if self._stt_backend == "google_sr":
                return self._google_sr(wav_path)
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass
        return ""

    def _load_whisper(self):
        if self._whisper_model is None:
            from faster_whisper import WhisperModel
            self._whisper_model = WhisperModel(
                "base", device="cpu", compute_type="int8"
            )
            logger.info("Whisper 'base' model loaded.")
        return self._whisper_model

    def _whisper(self, wav_path: str) -> str:
        model = self._load_whisper()
        try:
            segs, info = model.transcribe(
                wav_path,
                language="en",
                beam_size=5,
                vad_filter=True,                        # skips silent chunks
                vad_parameters={"min_silence_duration_ms": 400},
            )
            text = " ".join(s.text.strip() for s in segs).strip()
            logger.debug("Whisper lang=%s text=%r", info.language, text[:80])
            return text
        except Exception as exc:
            logger.error("Whisper failed: %s", exc)
            return ""

    def _google_sr(self, wav_path: str) -> str:
        import speech_recognition as sr
        r = sr.Recognizer()
        try:
            with sr.AudioFile(wav_path) as src:
                r.adjust_for_ambient_noise(src, duration=0.3)
                audio = r.record(src)
            return r.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except Exception as exc:
            logger.warning("Google SR failed: %s", exc)
            return ""

    # ── TTS ───────────────────────────────────────────────────────────────────

    def synthesize(
        self,
        text: str,
        emotion_label: str = "default",
        crisis_tier: str = "none",
    ) -> bytes:
        if self._tts_backend == "none":
            raise RuntimeError("No TTS backend. Install: pip install pyttsx3")

        clean = re.sub(r"\*{1,3}|#{1,6}\s?|`{1,3}|_{1,2}|-{2,}|\[|\]|\(.*?\)", "", text)
        clean = re.sub(r"\n+", " ", clean).strip()
        key   = "crisis" if crisis_tier in ("active", "passive") else emotion_label

        if self._tts_backend == "pyttsx3":
            return self._pyttsx3(clean, key)
        if self._tts_backend == "gtts":
            return self._gtts(clean, key)
        return b""

    def _pyttsx3(self, text: str, key: str) -> bytes:
        import pyttsx3
        profile = _PYTTSX3_PROFILES.get(key, _PYTTSX3_PROFILES["default"])
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        try:
            eng = pyttsx3.init()
            eng.setProperty("rate",   profile["rate"])
            eng.setProperty("volume", profile["volume"])
            female = next(
                (v for v in eng.getProperty("voices")
                 if "female" in v.name.lower() or "zira" in v.name.lower()),
                None,
            )
            if female:
                eng.setProperty("voice", female.id)
            eng.save_to_file(text, tmp.name)
            eng.runAndWait()
            return Path(tmp.name).read_bytes()
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    def _gtts(self, text: str, key: str) -> bytes:
        from gtts import gTTS
        slow = _GTTS_SLOW.get(key, False)
        tts  = gTTS(text=text, lang="en", slow=slow, tld="co.uk")
        buf  = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
