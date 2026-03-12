from __future__ import annotations

_PHQ2_MAX = 6
_GAD2_MAX = 6
_COMBINED_MAX = _PHQ2_MAX + _GAD2_MAX


def normalise_screening(phq2: int, gad2: int) -> float:
    """Normalise raw PHQ-2 + GAD-2 totals to [0, 1]."""
    combined = max(0, min(phq2, _PHQ2_MAX)) + max(0, min(gad2, _GAD2_MAX))
    return round(combined / _COMBINED_MAX, 4)
