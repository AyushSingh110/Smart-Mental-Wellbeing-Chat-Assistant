"""
rag_service_final.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Therapist-flow RAG service.

Changes vs rag_service.py
──────────────────────────
1. System prompt rewritten for a warm, trusted-friend persona.
   The AI validates before anything else, never gives unsolicited
   advice, and always ends with ONE natural question.

2. Therapist flow embedded in the prompt:
     Validate → Reflect → Explore → Support (only when earned)
   The prompt explicitly tells the model to echo the user's exact
   words back rather than using stock phrases like "That must be hard".

3. Language instruction injected from multilingual_voice_service.
   If language_code != "en", the LLM is told to respond in that
   language. No model fine-tuning required.

4. Response length calibrated per category — same as before but
   tightened for High Risk / Depression Risk (1–2 sentences only,
   pure warmth, no advice).

5. Signature extended with language_code parameter.
   Returns (response_text, llm_failed) tuple — unchanged.
"""
from __future__ import annotations

import json
import logging
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.services.llm_service import generate_llm_response

logger = logging.getLogger(__name__)

MODEL_NAME           = "all-MiniLM-L6-v2"
INDEX_PATH           = "backend/rag/faiss_index.index"
METADATA_PATH        = "backend/rag/metadata.json"
SIMILARITY_THRESHOLD = 2.0
TOP_K                = 3

# ── System prompt — warm friend / trusted companion ───────────────────────────
# Key design decisions:
#   • No clinical labels, no "I understand how you feel" stock phrases
#   • The AI echoes the user's exact words (specific > generic)
#   • Questions feel like natural curiosity, not an intake form
#   • CBT techniques are woven in invisibly — never named
_SYSTEM_PROMPT = """
You are a caring, warm companion — like a close friend who genuinely listens.
You have deep knowledge of CBT and emotional wellbeing, but you never sound clinical.

YOUR PERSONALITY:
- Present, curious, and genuinely interested in the person's experience
- You remember what they said earlier in this conversation and connect to it
- You sound like a real person texting a close friend — warm, unhurried, specific
- You sit with the person in their feeling before moving anywhere

YOUR APPROACH (do these naturally — never name them):
Step 1 — Validate: Reflect the person's feeling back using THEIR exact words.
         Not "That sounds hard" but "So the thing with [their specific situation] is really weighing on you."
Step 2 — Explore: Ask ONE question that goes deeper into what they said.
         Not "How does that make you feel?" but something specific to their situation.
Step 3 — Support: Only offer a reframe or coping thought AFTER validating.
         Never jump straight to advice. Let them feel heard first.

TONE RULES:
- Never say: "That must be hard", "I understand", "Of course", "Absolutely", "That's valid"
- Instead: echo their words, use "it sounds like…", "I wonder if…", "maybe…"
- Keep it conversational. Short sentences. No stiff phrasing.
- One warm acknowledgment per response is fine: "I'm really glad you shared that"

LANGUAGE RULE (MANDATORY — check below for instruction):
If a LANGUAGE INSTRUCTION is present, respond ENTIRELY in that language.
Every single word. Do not switch to English mid-response.

RESPONSE LENGTH:
Follow the LENGTH INSTRUCTION below exactly. Count sentences before responding.
End with exactly ONE question. It must feel like natural curiosity, not an interview.

SAFETY:
- For crisis_tier active or passive: the safety system handles this — do not generate
- For distress tier: validate warmly, one grounding thought, one gentle question
- Never say "everyone goes through this" or minimize the person's pain
- Never mention suicide, self-harm, or crisis resources unless they bring it up
"""

# ── Category → length + tone instruction ─────────────────────────────────────
_LENGTH_INSTRUCTIONS: dict[str, str] = {
    "Stable": (
        "Write 3 to 4 warm, conversational sentences. "
        "Keep it light — you're checking in on a friend. "
        "End with one curious, natural question about something they said."
    ),
    "Mild Stress": (
        "Write 3 to 4 sentences. "
        "Open with one sentence that reflects back what they said (use their words). "
        "Then one brief supportive thought. "
        "End with one open question that invites them to say more."
    ),
    "Moderate Distress": (
        "Write 2 to 3 sentences. "
        "Lead with emotional validation — echo their specific words back to them. "
        "No advice yet. "
        "End with one gentle question: what's the heaviest part of this for them?"
    ),
    "High Risk": (
        "Write 1 to 2 sentences only. "
        "Be purely warm and present. Zero advice, zero reframes, zero techniques. "
        "Just show you're here. End with: what would help most right now?"
    ),
    "Depression Risk": (
        "Write 1 to 2 sentences only. "
        "Acknowledge how heavy and exhausting things feel. "
        "End with one simple, caring question: are you okay right now?"
    ),
    # Crisis Risk → intercepted by main.py before RAG is ever called
}

_LENGTH_DEFAULT = (
    "Write 2 to 3 warm conversational sentences. "
    "Validate first, then one open question."
)


class RAGService:

    def __init__(self):
        self.embed_model = SentenceTransformer(MODEL_NAME)
        self.index       = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    # ── Context retrieval ─────────────────────────────────────────────────────

    def retrieve_context(self, query: str) -> list[dict]:
        embedding          = self.embed_model.encode([query])
        distances, indices = self.index.search(np.array(embedding), TOP_K)
        results = [
            self.metadata[idx]
            for i, idx in enumerate(indices[0])
            if distances[0][i] <= SIMILARITY_THRESHOLD
        ]
        if not results:
            results = [self.metadata[indices[0][0]]]
        return results

    # ── Prompt builder ────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        user_message:    str,
        emotion_label:   str,
        emotion_score:   float,
        intent:          str,
        mhi:             float,
        crisis_score:    float,
        crisis_tier:     str,
        category:        str,
        language_code:   str,
        chunks:          list[dict],
    ) -> str:
        context_text = "\n\n".join(
            f"Wellbeing technique {i+1}:\n{c['text']}" for i, c in enumerate(chunks)
        )
        length_instruction = _LENGTH_INSTRUCTIONS.get(category, _LENGTH_DEFAULT)

        # Language instruction from multilingual service
        lang_instruction = ""
        try:
            from backend.services.multilingual_voice_service import build_language_instruction
            lang_instruction = build_language_instruction(language_code)
        except ImportError:
            if language_code and language_code != "en":
                from backend.services.multilingual_voice_service import _LANG_META
                lang_name = _LANG_META.get(language_code, {}).get("name", language_code.upper())
                lang_instruction = (
                    f"\nLANGUAGE INSTRUCTION (MANDATORY):\n"
                    f"The user spoke in {lang_name}. "
                    f"Respond ENTIRELY in {lang_name}. No English except common loan-words.\n"
                )

        return f"""{_SYSTEM_PROMPT}
{lang_instruction}

Background wellbeing knowledge (use naturally, never cite or name):
{context_text}

Session context:
  Emotion   : {emotion_label} (score {emotion_score:.2f})
  Intent    : {intent}
  MHI score : {mhi:.0f} / 100
  Crisis p  : {crisis_score:.2f}
  Tier      : {crisis_tier}
  Category  : {category}

LENGTH INSTRUCTION (MANDATORY — count your sentences before sending):
{length_instruction}

The user just said:
"{user_message}"

Respond now. Natural prose only — no bullet points, no headers, no lists.
Follow the sentence count. End with exactly one question.
"""

    # ── Main generate ─────────────────────────────────────────────────────────

    def generate_response(
        self,
        user_message:        str,
        emotion_label:       str,
        emotion_score:       float,
        intent:              str,
        mental_health_index: float,
        crisis_probability:  float,
        crisis_tier:         str = "none",
        category:            str = "Stable",
        language_code:       str = "en",
    ) -> tuple[str, bool]:
        """
        Returns (response_text, llm_failed).
        main.py intercepts active/passive crisis tiers before calling this.
        """
        if crisis_tier in ("active", "passive"):
            logger.warning(
                "RAGService called for crisis_tier=%s — returning empty (safety_service handles)",
                crisis_tier,
            )
            return "", False

        try:
            chunks  = self.retrieve_context(user_message)
            prompt  = self._build_prompt(
                user_message, emotion_label, emotion_score,
                intent, mental_health_index, crisis_probability,
                crisis_tier, category, language_code, chunks,
            )
            result = generate_llm_response(prompt)

            if not result or not result.strip():
                logger.warning("RAGService | LLM returned empty")
                return "", True

            return result, False

        except Exception as exc:
            logger.error("RAGService.generate_response error: %s", exc)
            return "", True