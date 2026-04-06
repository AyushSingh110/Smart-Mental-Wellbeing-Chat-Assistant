from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np

try:
    import faiss
except ImportError:  # pragma: no cover - depends on local env
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - depends on local env
    SentenceTransformer = None

from backend.config import settings
from backend.services.llm_service import generate_llm_response

logger = logging.getLogger(__name__)

MODEL_NAME = settings.SENTENCE_MODEL_NAME
INDEX_PATH = settings.FAISS_INDEX_PATH
METADATA_PATH = settings.RAG_METADATA_PATH
SIMILARITY_THRESHOLD = 2.0
TOP_K = settings.RAG_TOP_K

_SYSTEM_PROMPT = """
You are a caring, warm companion who responds like a grounded and attentive friend.
You understand CBT-informed support, but you never sound clinical or robotic.

YOUR APPROACH:
- Start by reflecting the user's actual words or situation.
- Match the emotional intensity of the user without mirroring panic.
- Ask at most one natural follow-up question.
- Offer one practical, gentle thought only after validation.
- Keep the reply focused on the user's current moment instead of giving generic speeches.

TONE:
- Warm, specific, calm, and human.
- Avoid canned phrases like "That must be hard" or "I understand exactly how you feel."
- Do not use bullet points, headers, or lists in the final response.

SAFETY:
- Active and passive crisis are handled elsewhere. Do not generate crisis instructions.
- For distress, prioritize steadiness, containment, and one small next step.
- Never minimize pain or promise outcomes.

LANGUAGE:
- If a language instruction appears below, respond fully in that language.
- If responding in Hindi, use the informal "tum" register rather than "aap" — it feels warmer and less clinical.
"""

_LENGTH_INSTRUCTIONS: dict[str, str] = {
    "Flourishing": (
        "Write 2 to 3 warm, celebratory sentences. Acknowledge the positive state and invite further reflection."
    ),
    "Stable": (
        "Write 3 to 4 short conversational sentences. Validate, respond naturally, and end with one light question."
    ),
    "Mild Stress": (
        "Write 3 to 4 sentences. Reflect what the user said, add one supportive thought, and end with one open question."
    ),
    "Moderate Distress": (
        "Write 2 to 3 sentences. Lead with emotional validation, keep advice minimal, and end with one gentle question. "
        "If the session context includes a CBT technique hint, weave it in naturally as a suggestion — never as a directive."
    ),
    "High Risk": (
        "Write 1 to 2 very calm sentences. Be present, do not overload the user, and end with one grounding question."
    ),
    "Severe Risk": (
        "Write 1 to 2 caring sentences. Acknowledge heaviness, gently mention that support is available, "
        "and ask one simple check-in question."
    ),
    "Depression Risk": (
        "Write 1 to 2 caring sentences. Acknowledge heaviness and ask one simple check-in question."
    ),
}

_LENGTH_DEFAULT = "Write 2 to 3 warm conversational sentences and end with one open question."

# ── Banned boilerplate phrases that the LLM tends to overuse
_BANNED_PHRASES = re.compile(
    r"(that\s+must\s+be\s+(so\s+)?hard|"
    r"i\s+understand\s+exactly\s+how\s+you\s+feel|"
    r"i'?m\s+so\s+sorry\s+to\s+hear\s+that|"
    r"it'?s?\s+okay\s+to\s+not\s+be\s+okay|"
    r"you'?re?\s+not\s+alone\s+in\s+this|"
    r"remember\s+that\s+you\s+are\s+strong|"
    r"things\s+will\s+get\s+better)",
    re.IGNORECASE,
)

# ── CBT technique hints that can be woven naturally into Moderate Distress responses
_CBT_NATURAL_HINTS: dict[str, str] = {
    "breathing":        "gentle breathing techniques (like slowing the exhale) can help settle the body",
    "grounding":        "grounding exercises — noticing what's around you right now — can help break the spiral",
    "thought_record":   "writing down what's happening and how it's making you feel can sometimes create a little distance",
    "cognitive_reframe":"trying to gently question whether that thought is 100% true can sometimes ease the pressure",
    "body_scan":        "a quick body scan — just noticing where you're holding tension — can be surprisingly settling",
}


class RAGService:
    def __init__(self):
        self.embed_model = None
        self.index = None
        self.metadata: list[dict] = []
        self._rag_available = False

        try:
            index_path = Path(INDEX_PATH)
            metadata_path = Path(METADATA_PATH)
            if faiss is None or SentenceTransformer is None:
                logger.warning("RAG dependencies unavailable; continuing without retrieval")
            elif index_path.exists() and metadata_path.exists():
                self.embed_model = SentenceTransformer(MODEL_NAME)
                self.index = faiss.read_index(str(index_path))
                with metadata_path.open("r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self._rag_available = bool(self.metadata)
            else:
                logger.warning("RAG assets missing; continuing without retrieval")
        except Exception as exc:
            logger.warning("RAG initialisation failed; continuing without retrieval: %s", exc)
            self.embed_model = None
            self.index = None
            self.metadata = []
            self._rag_available = False

    def retrieve_context(self, query: str) -> list[dict]:
        if not self._rag_available or self.embed_model is None or self.index is None:
            return []
        embedding = self.embed_model.encode([query])
        distances, indices = self.index.search(np.array(embedding), TOP_K)
        results = [
            self.metadata[idx]
            for i, idx in enumerate(indices[0])
            if 0 <= idx < len(self.metadata) and distances[0][i] <= SIMILARITY_THRESHOLD
        ]
        if not results and len(indices[0]) > 0 and 0 <= indices[0][0] < len(self.metadata):
            results = [self.metadata[indices[0][0]]]
        return results

    def _build_prompt(
        self,
        user_message: str,
        emotion_label: str,
        emotion_score: float,
        intent: str,
        mhi: float,
        crisis_score: float,
        crisis_tier: str,
        category: str,
        language_code: str,
        chunks: list[dict],
        conversation_pairs: list[dict[str, str]] | None = None,
        cbt_hint: str | None = None,
        cross_session_ref: bool = False,
        crisis_velocity: float = 0.0,
        mhi_trajectory: str = "stable",
    ) -> str:
        context_text = "\n\n".join(
            f"Wellbeing technique {i + 1}:\n{chunk['text']}" for i, chunk in enumerate(chunks)
        ) or "No retrieved knowledge available."

        conversation_text = ""
        if conversation_pairs:
            snippets: list[str] = []
            for pair in conversation_pairs[-3:]:
                user_turn = pair.get("user", "").strip()
                assistant_turn = pair.get("assistant", "").strip()
                if user_turn:
                    snippets.append(f'User: "{user_turn}"')
                if assistant_turn:
                    snippets.append(f'Assistant: "{assistant_turn}"')
            if snippets:
                conversation_text = "Recent conversation:\n" + "\n".join(snippets)

        lang_instruction = ""
        try:
            from backend.services.multilingual_voice_service import build_language_instruction
            lang_instruction = build_language_instruction(language_code).strip()
        except ImportError:
            if language_code and language_code != "en":
                lang_instruction = f"Respond entirely in {language_code}."

        # Hindi tum register hint
        if language_code in ("hi", "hi-IN"):
            lang_instruction += " Use the informal 'tum' (तुम) form of address rather than 'aap' — it's warmer and more personal."

        # CBT natural injection for Moderate Distress
        cbt_section = ""
        if category == "Moderate Distress" and cbt_hint:
            hint_text = _CBT_NATURAL_HINTS.get(cbt_hint, "")
            if hint_text:
                cbt_section = f"Self-help suggestion to weave in naturally (do NOT name the technique explicitly): {hint_text}"

        # Cross-session reference note
        cross_ref_note = ""
        if cross_session_ref:
            cross_ref_note = "Note: The user appears to be referencing a previous session. Acknowledge continuity warmly."

        # Velocity warning for fast escalation
        velocity_note = ""
        if crisis_velocity > 0.25:
            velocity_note = (
                f"Note: The user's distress level has been escalating across recent turns (velocity={crisis_velocity:.2f}). "
                "Respond with extra steadiness and care."
            )

        # Trajectory note
        trajectory_note = ""
        if mhi_trajectory == "declining":
            trajectory_note = "Note: User's wellbeing trend has been declining across sessions. Extra gentle tone is important."
        elif mhi_trajectory == "volatile":
            trajectory_note = "Note: User's wellbeing has been volatile. Prioritize stability and predictability in your response."

        sections = [
            _SYSTEM_PROMPT.strip(),
            lang_instruction,
            "Background wellbeing knowledge (use naturally, never cite or name):",
            context_text,
            "Session context:",
            f"Emotion: {emotion_label} ({emotion_score:.2f})",
            f"Intent: {intent}",
            f"MHI: {mhi:.0f}/100",
            f"Crisis probability: {crisis_score:.2f}",
            f"Tier: {crisis_tier}",
            f"Category: {category}",
            cbt_section,
            cross_ref_note,
            velocity_note,
            trajectory_note,
            conversation_text,
            "Length instruction:",
            _LENGTH_INSTRUCTIONS.get(category, _LENGTH_DEFAULT),
            "The user just said:",
            f'"{user_message}"',
            "Respond now in natural prose only. End with exactly one question.",
        ]
        return "\n\n".join(section for section in sections if section)

    def _contains_banned_phrases(self, text: str) -> bool:
        """Check if the LLM response contains overused boilerplate phrases."""
        return bool(_BANNED_PHRASES.search(text))

    def generate_response(
        self,
        user_message: str,
        emotion_label: str,
        emotion_score: float,
        intent: str,
        mental_health_index: float,
        crisis_probability: float,
        crisis_tier: str = "none",
        category: str = "Stable",
        language_code: str = "en",
        conversation_pairs: list[dict[str, str]] | None = None,
        cbt_hint: str | None = None,
        cross_session_ref: bool = False,
        crisis_velocity: float = 0.0,
        mhi_trajectory: str = "stable",
    ) -> tuple[str, bool]:
        if crisis_tier in ("active", "passive"):
            logger.warning(
                "RAGService called for crisis_tier=%s; returning empty because safety handles it",
                crisis_tier,
            )
            return "", False

        try:
            chunks = self.retrieve_context(user_message)
            prompt = self._build_prompt(
                user_message=user_message,
                emotion_label=emotion_label,
                emotion_score=emotion_score,
                intent=intent,
                mhi=mental_health_index,
                crisis_score=crisis_probability,
                crisis_tier=crisis_tier,
                category=category,
                language_code=language_code,
                chunks=chunks,
                conversation_pairs=conversation_pairs,
                cbt_hint=cbt_hint,
                cross_session_ref=cross_session_ref,
                crisis_velocity=crisis_velocity,
                mhi_trajectory=mhi_trajectory,
            )
            result = generate_llm_response(prompt)
            if not result or not result.strip():
                logger.warning("RAGService | LLM returned empty")
                return "", True

            result = result.strip()

            # If response contains banned boilerplate, regenerate once
            if self._contains_banned_phrases(result):
                logger.info("RAGService | banned phrase detected, regenerating")
                anti_boilerplate = (
                    "\n\nIMPORTANT: Your previous response contained overused phrases. "
                    "Rewrite without any of: 'That must be hard', 'I understand exactly', "
                    "'I'm so sorry to hear', 'it's okay to not be okay', 'you're not alone', "
                    "'things will get better'. Be more specific and personal to the user's actual words."
                )
                result2 = generate_llm_response(prompt + anti_boilerplate)
                if result2 and result2.strip():
                    result = result2.strip()

            return result, False
        except Exception as exc:
            logger.error("RAGService.generate_response error: %s", exc)
            return "", True
