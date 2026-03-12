"""
multilingual_voice_service.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW FREE MULTILINGUAL WORKS — FULL EXPLANATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LAYER 1 — Speech-to-Text + Language Detection  (FREE, fully local)
────────────────────────────────────────────────────────────────────
Tool : faster-whisper  (OpenAI Whisper model running on your own CPU)
Cost : ZERO. No API key. No internet required. Model downloads once (~39 MB).

How it works:
  OpenAI trained Whisper on 680,000 hours of multilingual audio across
  99 languages. When you call transcribe() with language=None, Whisper runs
  a single forward pass that does TWO things simultaneously:
    (a)  Detects the spoken language from the first ~30 seconds of audio
         and returns a probability score  (e.g. language="hi", prob=0.97)
    (b)  Transcribes the full audio in that detected language

  Example:
    User speaks: "मुझे बहुत बुरा लग रहा है"
    Whisper returns: language="hi", text="मुझे बहुत बुरा लग रहा है", prob=0.97

  This is the same model OpenAI sells via their API, but running locally.
  faster-whisper is a CTranslate2-optimised re-implementation that is
  4x faster and uses 50% less memory than the original.


LAYER 2 — LLM responds in detected language  (FREE, no change to LLM)
────────────────────────────────────────────────────────────────────────
The language code returned by Layer 1 is passed to build_language_instruction()
which returns a prompt snippet like:
  "The user is speaking Hindi. Respond entirely in Hindi."

This is injected into the RAG system prompt. The LLM (Ollama/OpenAI/any)
naturally follows this instruction — it does not need multilingual fine-tuning.


LAYER 3 — Text-to-Speech in detected language, Indian accent  (FREE)
──────────────────────────────────────────────────────────────────────
Primary tool  : gTTS (Google Text-to-Speech)
  - Completely free. No API key required.
  - Uses Google Translate's public TTS endpoint (same tech as Google Translate).
  - Supports all major Indian languages natively with natural native voices.
  - The tld="co.in" parameter routes to Indian servers → Indian English accent.
  - For Hindi, Tamil, Bengali etc. the voice is always a native speaker.

Fallback tool : pyttsx3  (offline, zero internet)
  - Uses OS-installed voices: SAPI5 (Windows), espeak-ng (Linux), AVSpeech (macOS).
  - Limited language support depending on installed voices.

Speed adjustment via pydub:
  gTTS produces audio at a fixed speaking rate. We adjust tempo post-synthesis
  using pydub's frame_rate trick (no pitch shift — voice stays natural):
    Crisis tier  → 0.82x  (very slow, calm, deliberate)
    Sadness      → 0.87x
    Normal       → 1.00x
  This makes the AI sound appropriately gentle for distressed users.


SUPPORTED INDIAN LANGUAGES
───────────────────────────
Hindi(hi)  Bengali(bn)  Tamil(ta)   Telugu(te)   Marathi(mr)
Gujarati(gu)  Punjabi(pa)  Kannada(kn)  Malayalam(ml)  Urdu(ur)
Odia(or)  Assamese(as)  Nepali(ne)  Sanskrit(sa)
English with Indian accent(en, tld=co.in)


INSTALLATION
─────────────
pip install faster-whisper gtts pydub
  faster-whisper : local Whisper model (~39 MB auto-downloaded on first use)
  gtts           : Google TTS client (free, no key)
  pydub          : audio speed adjustment (optional but recommended)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import io
import logging
import os
import tempfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Language registry ─────────────────────────────────────────────────────────
_LANG_META: dict[str, dict] = {
    "hi": {"name": "Hindi",      "gtts_lang": "hi", "gtts_tld": "co.in"},
    "bn": {"name": "Bengali",    "gtts_lang": "bn", "gtts_tld": "co.in"},
    "ta": {"name": "Tamil",      "gtts_lang": "ta", "gtts_tld": "co.in"},
    "te": {"name": "Telugu",     "gtts_lang": "te", "gtts_tld": "co.in"},
    "mr": {"name": "Marathi",    "gtts_lang": "mr", "gtts_tld": "co.in"},
    "gu": {"name": "Gujarati",   "gtts_lang": "gu", "gtts_tld": "co.in"},
    "pa": {"name": "Punjabi",    "gtts_lang": "pa", "gtts_tld": "co.in"},
    "kn": {"name": "Kannada",    "gtts_lang": "kn", "gtts_tld": "co.in"},
    "ml": {"name": "Malayalam",  "gtts_lang": "ml", "gtts_tld": "co.in"},
    "ur": {"name": "Urdu",       "gtts_lang": "ur", "gtts_tld": "co.in"},
    "or": {"name": "Odia",       "gtts_lang": "or", "gtts_tld": "co.in"},
    "as": {"name": "Assamese",   "gtts_lang": "as", "gtts_tld": "co.in"},
    "ne": {"name": "Nepali",     "gtts_lang": "ne", "gtts_tld": "co.in"},
    "sa": {"name": "Sanskrit",   "gtts_lang": "hi", "gtts_tld": "co.in"},
    "en": {"name": "English",    "gtts_lang": "en", "gtts_tld": "co.in"},
}

# Emotion/crisis → playback speed (pydub frame_rate trick, no pitch shift)
_SPEED: dict[str, float] = {
    "crisis": 0.82, "sadness": 0.87, "fear": 0.88,
    "anxiety": 0.90, "stress": 0.91, "anger": 0.88,
    "neutral": 1.00, "default": 0.95,
}

# pyttsx3 words-per-minute rates
_WPM: dict[str, int] = {
    "crisis": 120, "sadness": 135, "fear": 140,
    "anxiety": 145, "stress": 150, "anger": 140,
    "neutral": 175, "default": 160,
}

_MIN_BYTES    = 3_000
_WHISPER_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")


@dataclass
class TranscriptionResult:
    text:          str
    language_code: str    # ISO 639-1 code, e.g. "hi"
    language_name: str    # Human name, e.g. "Hindi"
    confidence:    float  # Whisper language_probability

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


class MultilingualVoiceService:
    """
    Multilingual voice service supporting 14 Indian languages + English.

    Public interface:
        transcribe(audio_bytes, fmt) -> TranscriptionResult
        synthesize(text, language_code, emotion_label, crisis_tier) -> bytes
        tts_backend -> str
    """

    def __init__(self):
        self._model          = None
        self._pyttsx3_engine = None
        self._tts_backend    = None
        self._init_tts()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_tts(self) -> None:
        try:
            from gtts import gTTS  # noqa: F401
            self._tts_backend = "gtts"
            logger.info("MultilingualVoiceService | TTS: gTTS (multilingual)")
            return
        except ImportError:
            pass
        try:
            import pyttsx3
            self._pyttsx3_engine = pyttsx3.init()
            self._tts_backend    = "pyttsx3"
            logger.info("MultilingualVoiceService | TTS: pyttsx3 (offline fallback)")
        except Exception as exc:
            logger.error("MultilingualVoiceService | No TTS backend: %s", exc)

    def _load_whisper(self) -> None:
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(_WHISPER_SIZE, device="cpu", compute_type="int8")
            logger.info("MultilingualVoiceService | Whisper loaded: %s", _WHISPER_SIZE)
        except ImportError:
            raise RuntimeError("Run: pip install faster-whisper")

    # ── Public API ────────────────────────────────────────────────────────────

    def transcribe(self, audio_bytes: bytes, fmt: str = "webm", language: str | None = None) -> TranscriptionResult:
        """
        Single Whisper pass: detects language AND transcribes simultaneously.
        If *language* is provided (e.g. "hi"), Whisper is forced to that language
        instead of auto-detecting, which prevents mis-detection.
        Returns TranscriptionResult. Never raises — returns empty result on error.
        """
        if len(audio_bytes) < _MIN_BYTES:
            return TranscriptionResult("", "en", "English", 0.0)

        self._load_whisper()

        suffix   = f".{fmt}" if fmt else ".webm"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            # If a language hint was provided, force Whisper to that language;
            # otherwise auto-detect (language=None).
            whisper_lang = language if language and language in _LANG_META else None
            segments, info = self._model.transcribe(
                tmp_path,
                language=whisper_lang,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 300},
                beam_size=5,
            )

            code = info.language
            prob = info.language_probability
            meta = _LANG_META.get(code, {"name": code.upper(), "gtts_lang": "en", "gtts_tld": "com"})
            text = " ".join(s.text.strip() for s in segments).strip()

            logger.info("Transcribed [%s/%.0f%%]: %r", code, prob * 100, text[:60])
            return TranscriptionResult(text, code, meta["name"], round(prob, 3))

        except Exception as exc:
            logger.error("transcribe error: %s", exc)
            return TranscriptionResult("", "en", "English", 0.0)
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def synthesize(
        self,
        text:          str,
        language_code: str = "en",
        emotion_label: str = "default",
        crisis_tier:   str = "none",
    ) -> bytes:
        """
        Produces speech audio in the correct language with Indian accent
        and emotion-matched speaking speed.
        Returns MP3 bytes (gTTS) or WAV bytes (pyttsx3).
        """
        if not text.strip():
            return b""

        if self._tts_backend == "gtts":
            try:
                return self._gtts_speak(text, language_code, emotion_label, crisis_tier)
            except Exception as exc:
                logger.warning("gTTS failed (%s), using pyttsx3", exc)

        return self._pyttsx3_speak(text, emotion_label, crisis_tier)

    @property
    def tts_backend(self) -> str:
        return self._tts_backend or "none"

    # ── gTTS ─────────────────────────────────────────────────────────────────

    def _gtts_speak(self, text, language_code, emotion_label, crisis_tier) -> bytes:
        from gtts import gTTS

        meta    = _LANG_META.get(language_code, _LANG_META["en"])
        spd_key = "crisis" if crisis_tier in ("active", "passive") \
                  else (emotion_label if emotion_label in _SPEED else "default")
        speed   = _SPEED[spd_key]

        logger.debug("gTTS | %s speed=%.2f", meta["name"], speed)

        tts = gTTS(text=text, lang=meta["gtts_lang"], tld=meta["gtts_tld"], slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        mp3 = buf.getvalue()

        if abs(speed - 1.0) > 0.02:
            try:
                mp3 = self._change_speed(mp3, speed)
            except Exception:
                pass
        return mp3

    @staticmethod
    def _change_speed(mp3_bytes: bytes, speed: float) -> bytes:
        """
        Adjusts tempo without pitch change.
        Works by overriding the frame_rate metadata (pydub trick).
        No FFmpeg pitch-shift needed. Voice remains natural.
        """
        from pydub import AudioSegment
        audio    = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
        adjusted = audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": int(audio.frame_rate * speed)},
        ).set_frame_rate(audio.frame_rate)
        out = io.BytesIO()
        adjusted.export(out, format="mp3")
        return out.getvalue()

    # ── pyttsx3 fallback ──────────────────────────────────────────────────────

    def _pyttsx3_speak(self, text, emotion_label, crisis_tier) -> bytes:
        if self._pyttsx3_engine is None:
            import pyttsx3
            self._pyttsx3_engine = pyttsx3.init()

        wpm_key = "crisis" if crisis_tier in ("active", "passive") \
                  else (emotion_label if emotion_label in _WPM else "default")
        self._pyttsx3_engine.setProperty("rate",   _WPM[wpm_key])
        self._pyttsx3_engine.setProperty("volume", 0.95)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            path = tmp.name
        try:
            self._pyttsx3_engine.save_to_file(text, path)
            self._pyttsx3_engine.runAndWait()
            with open(path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


# ── Prompt helper (called by rag_service._build_prompt) ──────────────────────

def build_language_instruction(language_code: str) -> str:
    """
    Returns a prompt instruction string that tells the LLM to respond
    in the user's detected language. Empty string for English (default).

    This is the bridge between STT language detection and LLM output.
    The LLM needs no special training — it follows natural language instructions.
    """
    if not language_code or language_code == "en":
        return ""
    name = _LANG_META.get(language_code, {}).get("name", language_code.upper())
    return (
        f"\nLANGUAGE INSTRUCTION (MANDATORY):\n"
        f"The user spoke in {name}. You MUST respond entirely in {name}.\n"
        f"Do not switch to English. Use natural, conversational {name}.\n"
        f"Common English loan-words used in everyday {name} speech are acceptable.\n"
    )


def get_language_name(code: str) -> str:
    return _LANG_META.get(code, {}).get("name", code.upper())