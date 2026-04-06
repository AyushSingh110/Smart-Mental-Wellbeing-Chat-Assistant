from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Any

from bson import ObjectId


# Number of recent sessions used for trend calculation
_HISTORY_WINDOW = 5

# Decay factor: more recent sessions have higher influence
_DECAY = 0.8

# Session frequency bonus: sessions within the last 7 days show engagement
_SESSION_FREQUENCY_WINDOW_DAYS = 7
_SESSION_FREQUENCY_BONUS = 0.08   # reduces risk score (better engagement)
_SESSION_FREQUENCY_MIN   = 3      # minimum sessions in window for bonus

# Cross-session reference patterns: user refers back to previous topics
_CROSS_SESSION_RE = re.compile(
    r"\b("
    r"last\s+time\s+(we\s+talked|i\s+was\s+here|i\s+mentioned)|"
    r"as\s+i\s+said\s+(before|last\s+time|earlier)|"
    r"remember\s+(when\s+i\s+told\s+you|i\s+mentioned)|"
    r"following\s+up\s+on|continuing\s+from\s+where|"
    r"since\s+(our\s+last\s+(chat|conversation|session)|we\s+last\s+talked)|"
    r"update\s+(you|on\s+what\s+happened)|still\s+(feel(ing)?|deal(ing)?)\s+the\s+same"
    r")\b",
    re.IGNORECASE,
)


class HistoryService:

    def __init__(self, conversations_col: Any):
        self.col = conversations_col

    async def compute(self, user_id: ObjectId) -> float:
        """
        Returns a history-based risk score in [0, 1].

        Fetches the last N MHI scores, inverts them to risk space,
        then applies exponential decay weighting so recent sessions
        matter more than older ones.

        Session frequency bonus: if user has been engaging regularly,
        slightly reduce their risk score (engagement = protective factor).

        Returns 0.5 (neutral) when no history exists.
        """
        cursor = (
            self.col.find(
                {"user_id": user_id},
                {"mhi": 1, "timestamp": 1, "_id": 0}
            )
            .sort("timestamp", -1)
            .limit(_HISTORY_WINDOW + 10)  # fetch extra for frequency calc
        )

        docs = await cursor.to_list(length=_HISTORY_WINDOW + 10)

        if not docs:
            return 0.5

        # Use first N for risk computation
        risk_docs = docs[:_HISTORY_WINDOW]

        # Convert MHI [0,100] → risk [0,1]: low MHI = high risk
        risk_scores = [(100 - d["mhi"]) / 100 for d in risk_docs if "mhi" in d]

        if not risk_scores:
            return 0.5

        # Exponential decay weights: index 0 = most recent
        weights = [_DECAY ** i for i in range(len(risk_scores))]
        total_weight = sum(weights)

        weighted_risk = sum(r * w for r, w in zip(risk_scores, weights)) / total_weight

        # Session frequency bonus
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=_SESSION_FREQUENCY_WINDOW_DAYS)
        recent_count = sum(
            1 for d in docs
            if d.get("timestamp") and self._parse_ts(d["timestamp"]) >= window_start
        )
        if recent_count >= _SESSION_FREQUENCY_MIN:
            weighted_risk = max(0.0, weighted_risk - _SESSION_FREQUENCY_BONUS)

        return round(weighted_risk, 4)

    async def get_trend(self, user_id: ObjectId) -> str:
        """
        Returns a human-readable trend label based on last 3 sessions.
        Used optionally by the report or dashboard.
        """
        cursor = (
            self.col.find(
                {"user_id": user_id},
                {"mhi": 1, "_id": 0}
            )
            .sort("timestamp", -1)
            .limit(3)
        )

        docs = await cursor.to_list(length=3)

        if len(docs) < 2:
            return "insufficient_data"

        scores = [d["mhi"] for d in docs]
        delta = scores[0] - scores[-1]

        if delta > 5:
            return "improving"
        if delta < -5:
            return "declining"
        return "stable"

    async def get_recent_snapshot(self, user_id: ObjectId, *, limit: int = 4) -> dict[str, Any]:
        cursor = (
            self.col.find(
                {"user_id": user_id},
                {"message": 1, "response": 1, "emotion_scores": 1, "mhi": 1, "timestamp": 1, "_id": 0},
            )
            .sort("timestamp", -1)
            .limit(limit)
        )

        docs = await cursor.to_list(length=limit)
        docs.reverse()

        recent_emotions: list[str] = []
        recent_mhi: list[float] = []
        conversation_pairs: list[dict[str, str]] = []

        for doc in docs:
            emotion_scores = doc.get("emotion_scores") or {}
            if emotion_scores:
                recent_emotions.append(max(emotion_scores, key=emotion_scores.get))
            if "mhi" in doc:
                recent_mhi.append(float(doc["mhi"]))
            conversation_pairs.append({
                "user": str(doc.get("message", "")),
                "assistant": str(doc.get("response", "")),
            })

        # Compute mhi_trajectory: "improving" | "declining" | "stable" | "volatile"
        mhi_trajectory = self._compute_trajectory(recent_mhi)

        return {
            "recent_emotions":     recent_emotions,
            "recent_mhi":          recent_mhi,
            "conversation_pairs":  conversation_pairs,
            "mhi_trajectory":      mhi_trajectory,
        }

    def detect_cross_session_reference(self, text: str) -> bool:
        """
        Returns True if the message appears to reference a previous session.
        This is a positive engagement signal used in the RAG prompt.
        """
        return bool(_CROSS_SESSION_RE.search(text))

    # ── Internals

    @staticmethod
    def _compute_trajectory(mhi_list: list[float]) -> str:
        """
        Analyses MHI history to label the trend.
        Returns: "improving" | "declining" | "stable" | "volatile" | "insufficient"
        """
        if len(mhi_list) < 2:
            return "insufficient"

        # Volatility: large swings (std-dev > 15) = volatile
        mean = sum(mhi_list) / len(mhi_list)
        variance = sum((x - mean) ** 2 for x in mhi_list) / len(mhi_list)
        std_dev = variance ** 0.5
        if std_dev > 15.0:
            return "volatile"

        # Overall direction: compare first half vs second half average
        mid = len(mhi_list) // 2
        first_half  = sum(mhi_list[:mid]) / max(mid, 1)
        second_half = sum(mhi_list[mid:]) / max(len(mhi_list) - mid, 1)
        delta = second_half - first_half

        if delta > 5.0:
            return "improving"
        if delta < -5.0:
            return "declining"
        return "stable"

    @staticmethod
    def _parse_ts(ts) -> datetime:
        """Safely parse a timestamp that may be a datetime or a string."""
        if isinstance(ts, datetime):
            return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
        try:
            return datetime.fromisoformat(str(ts)).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)
