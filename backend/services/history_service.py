from __future__ import annotations

from typing import Any

from bson import ObjectId


# Number of recent sessions used for trend calculation
_HISTORY_WINDOW = 5

# Decay factor: more recent sessions have higher influence
_DECAY = 0.8


class HistoryService:

    def __init__(self, conversations_col: Any):
        self.col = conversations_col

    async def compute(self, user_id: ObjectId) -> float:
        """
        Returns a history-based risk score in [0, 1].

        Fetches the last N MHI scores, inverts them to risk space,
        then applies exponential decay weighting so recent sessions
        matter more than older ones.

        Returns 0.5 (neutral) when no history exists.
        """
        cursor = (
            self.col.find(
                {"user_id": user_id},
                {"mhi": 1, "_id": 0}
            )
            .sort("timestamp", -1)
            .limit(_HISTORY_WINDOW)
        )

        docs = await cursor.to_list(length=_HISTORY_WINDOW)

        if not docs:
            return 0.5

        # Convert MHI [0,100] → risk [0,1]: low MHI = high risk
        risk_scores = [(100 - d["mhi"]) / 100 for d in docs]

        # Exponential decay weights: index 0 = most recent
        weights = [_DECAY ** i for i in range(len(risk_scores))]
        total_weight = sum(weights)

        weighted_risk = sum(r * w for r, w in zip(risk_scores, weights)) / total_weight

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

    async def get_recent_snapshot(self, user_id: ObjectId, *, limit: int = 4) -> dict[str, list]:
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

        return {
            "recent_emotions": recent_emotions,
            "recent_mhi": recent_mhi,
            "conversation_pairs": conversation_pairs,
        }
