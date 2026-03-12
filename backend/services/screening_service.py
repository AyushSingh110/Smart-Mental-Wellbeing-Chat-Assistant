from __future__ import annotations

from backend.config import settings


# PHQ-2: 2 items, each 0–3 → max 6
# GAD-2: 2 items, each 0–3 → max 6
# Combined max = 12

_PHQ2_MAX = 6
_GAD2_MAX = 6
_COMBINED_MAX = _PHQ2_MAX + _GAD2_MAX

# Clinical thresholds (for reference in categorization):
# PHQ-2 >= 3 → positive depression screen
# GAD-2 >= 3 → positive anxiety screen


class ScreeningService:

    def compute(self, phq2_total: int = 0, gad2_total: int = 0) -> float:
        """
        Converts raw PHQ-2 + GAD-2 totals into a normalized risk score in [0, 1].
        Both inputs should be the summed score (0–6 each).
        Returns 0.0 if no assessment data provided.
        """
        phq2_total = max(0, min(phq2_total, _PHQ2_MAX))
        gad2_total = max(0, min(gad2_total, _GAD2_MAX))

        combined = phq2_total + gad2_total
        return round(combined / _COMBINED_MAX, 4)

    def get_flags(self, phq2_total: int, gad2_total: int) -> dict:
        """Returns clinical flag booleans for downstream use."""
        return {
            "depression_screen_positive": phq2_total >= 3,
            "anxiety_screen_positive": gad2_total >= 3,
        }
