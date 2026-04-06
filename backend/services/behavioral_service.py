from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Behavioral pattern groups
# Each entry: (pattern, severity_weight 1-5)
# Severity: 1=mild signal, 2=moderate, 3=significant, 4=severe, 5=critical

# Category 1: Sleep disturbances
_SLEEP_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(can'?t\s+sleep|insomnia|sleepless(ness)?|awake\s+all\s+night)\b", re.I), 3.0),
    (re.compile(r"\b(nightmares?|night\s+terrors?|disturbed\s+sleep)\b", re.I), 3.0),
    (re.compile(r"\b(sleeping\s+(too\s+much|all\s+day|all\s+the\s+time)|oversleeping)\b", re.I), 2.0),
    (re.compile(r"\b(can'?t\s+get\s+out\s+of\s+bed|stuck\s+in\s+bed|bed\s+all\s+day)\b", re.I), 3.5),
    (re.compile(r"\b(exhausted\s+but\s+(can'?t|unable\s+to)\s+sleep|tired\s+but\s+awake)\b", re.I), 3.5),
    (re.compile(r"\b(waking\s+up\s+(at\s+)?(3|4)\s*(am|a\.?m\.?)|early\s+morning\s+waking)\b", re.I), 2.5),
]

# Category 2: Appetite / eating patterns
_APPETITE_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(not\s+eating|stopped\s+eating|skipping\s+meals?|no\s+appetite)\b", re.I), 3.0),
    (re.compile(r"\b(binge\s+eating|can'?t\s+stop\s+eating|eating\s+everything)\b", re.I), 2.5),
    (re.compile(r"\b(starving\s+myself|purging|throwing\s+up\s+after\s+eating)\b", re.I), 5.0),
    (re.compile(r"\b(lost\s+weight|losing\s+weight\s+(rapidly|fast|quickly))\b", re.I), 2.5),
    (re.compile(r"\b(no\s+hunger|food\s+makes\s+me\s+(sick|nauseous)|can'?t\s+eat)\b", re.I), 3.0),
    (re.compile(r"\b(comfort\s+eating|eating\s+my\s+feelings|stress\s+eating)\b", re.I), 2.0),
]

# Category 3: Social withdrawal / isolation
_SOCIAL_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(isolat(e|ed|ing|ion)|withdrawal|withdrawn|social\s+withdraw)\b", re.I), 3.5),
    (re.compile(r"\b(avoid(ing)?\s+(people|others|friends|family|everyone))\b", re.I), 3.5),
    (re.compile(r"\b(don'?t\s+want\s+to\s+(see|talk\s+to|meet|be\s+around)\s+(anyone|people|friends|family))\b", re.I), 3.0),
    (re.compile(r"\b(cancel(l?ed|ling)\s+(plans|everything|all\s+plans))\b", re.I), 2.5),
    (re.compile(r"\b(lock(ed|ing)?\s+myself\s+(in|away|up)|staying\s+(inside|home)\s+all\s+(day|week|time))\b", re.I), 3.5),
    (re.compile(r"\b(stopped\s+(going\s+out|socializing|talking\s+to\s+people))\b", re.I), 3.0),
    (re.compile(r"\b(nobody\s+(understands|gets\s+me|knows\s+what\s+i'?m\s+going\s+through))\b", re.I), 2.5),
]

# Category 4: Concentration / cognitive function
_CONCENTRATION_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(can'?t\s+(concentrate|focus|think|remember)\b)", re.I), 3.0),
    (re.compile(r"\b(brain\s+fog|memory\s+(problems?|issues?|loss)|forgetting\s+everything)\b", re.I), 3.0),
    (re.compile(r"\b(mind\s+going\s+blank|thoughts?\s+(all\s+over\s+the\s+place|racing|jumbled))\b", re.I), 2.5),
    (re.compile(r"\b(can'?t\s+(read|study|work|finish\s+anything)|losing\s+track)\b", re.I), 3.0),
    (re.compile(r"\b(decision\s+(paralysis|making\s+is\s+hard)|can'?t\s+decide\s+anything)\b", re.I), 2.0),
    (re.compile(r"\b(slow\s+thinking|sluggish\s+(mind|brain)|mentally\s+exhausted)\b", re.I), 2.5),
]

# Category 5: Energy / physical activity
_ENERGY_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(no\s+(energy|motivation|drive)|lost\s+(motivation|all\s+drive))\b", re.I), 3.0),
    (re.compile(r"\b(tired\s+all\s+(the\s+)?time|constantly\s+tired|always\s+exhausted)\b", re.I), 3.0),
    (re.compile(r"\b(stopped\s+(exercising|working\s+out|going\s+to\s+gym))\b", re.I), 2.0),
    (re.compile(r"\b(can'?t\s+(get\s+up|move|do\s+anything)|heavy\s+(limbs?|body))\b", re.I), 3.5),
    (re.compile(r"\b(everything\s+(feels\s+like\s+an\s+effort|is\s+too\s+much\s+effort))\b", re.I), 3.0),
    (re.compile(r"\b(drained|depleted|running\s+on\s+empty)\b", re.I), 2.5),
]

# Category 6: Physical symptoms
_PHYSICAL_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(chest\s+(pain|tightness|heaviness)|heart\s+(racing|pounding|palpitations?))\b", re.I), 3.5),
    (re.compile(r"\b(headache|migraine|head\s+pain)\b", re.I), 1.5),
    (re.compile(r"\b(nausea|stomach\s+(ache|pain|knot|churning)|gut\s+feeling)\b", re.I), 2.0),
    (re.compile(r"\b(shaking|trembling|shivering\s+(with\s+anxiety|from\s+stress))\b", re.I), 3.0),
    (re.compile(r"\b(shortness\s+of\s+breath|can'?t\s+breathe\s+(properly|normally|well))\b", re.I), 3.5),
    (re.compile(r"\b(body\s+(ache|pain|hurts\s+everywhere)|physical\s+symptoms?\s+of\s+stress)\b", re.I), 2.5),
]

# Category 7: Activity level / daily functioning
_ACTIVITY_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(stopped\s+(going\s+to\s+(work|school|college)|doing\s+(my\s+)?job))\b", re.I), 4.0),
    (re.compile(r"\b(missing\s+(work|school|class|deadlines?)\s+(again|frequently|always))\b", re.I), 3.5),
    (re.compile(r"\b(can'?t\s+function\s+(normally|properly|at\s+all))\b", re.I), 4.0),
    (re.compile(r"\b(stopped\s+(caring|trying|bothering)\s+about\s+(everything|anything|life))\b", re.I), 4.0),
    (re.compile(r"\b(lost\s+interest\s+in\s+(everything|hobbies|things\s+i\s+used\s+to\s+like))\b", re.I), 3.5),
    (re.compile(r"\b(don'?t\s+(shower|bathe|brush)\s+(anymore|regularly|at\s+all))\b", re.I), 4.0),
    (re.compile(r"\b(hygiene\s+(neglect|issues?)|self[\s\-]neglect)\b", re.I), 4.0),
    (re.compile(r"\b(can'?t\s+do\s+(basic|simple|everyday)\s+tasks?)\b", re.I), 3.5),
]

# Category 8: Negative coping mechanisms
_NEGATIVE_COPING_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(drinking\s+(more|heavily|every\s+day|to\s+cope)|alcohol\s+to\s+(cope|numb|escape))\b", re.I), 4.0),
    (re.compile(r"\b(using\s+drugs?|drug\s+use|taking\s+(pills|substances?)\s+to\s+cope)\b", re.I), 4.5),
    (re.compile(r"\b(smoking\s+more|chain\s+smoking|smok(e|ing)\s+to\s+calm\s+down)\b", re.I), 2.5),
    (re.compile(r"\b(self[\s\-](harm|injur(e|ing|y))|cutting\s+myself|hurt(ing)?\s+myself)\b", re.I), 5.0),
    (re.compile(r"\b(gambling|spending\s+compulsively|retail\s+therapy\s+out\s+of\s+control)\b", re.I), 3.0),
    (re.compile(r"\b(escaping\s+(into|through)\s+(games?|screens?|tv|social\s+media)\s+all\s+day)\b", re.I), 2.0),
    (re.compile(r"\b(anger\s+outbursts?|snapping\s+at\s+(everyone|people)|violent\s+thoughts?)\b", re.I), 3.5),
    (re.compile(r"\b(reckless\s+(behaviour|behavior|driving|choices?)|taking\s+dangerous\s+risks?)\b", re.I), 4.0),
]

# All categories with their names and max possible raw score
_CATEGORIES: dict[str, list[tuple[re.Pattern, float]]] = {
    "sleep":          _SLEEP_PATTERNS,
    "appetite":       _APPETITE_PATTERNS,
    "social":         _SOCIAL_PATTERNS,
    "concentration":  _CONCENTRATION_PATTERNS,
    "energy":         _ENERGY_PATTERNS,
    "physical":       _PHYSICAL_PATTERNS,
    "activity":       _ACTIVITY_PATTERNS,
    "negative_coping": _NEGATIVE_COPING_PATTERNS,
}

_CATEGORY_MAX: dict[str, float] = {
    cat: sum(w for _, w in patterns)
    for cat, patterns in _CATEGORIES.items()
}


@dataclass
class BehavioralProfile:
    """Detailed behavioral breakdown returned by predict_profile()."""
    overall_score: float                         # 0→1, composite behavioral risk
    category_scores: dict[str, float]           # per-category 0→1 scores
    flagged_categories: list[str]               # categories above threshold
    dominant_category: Optional[str]            # highest-scoring category (or None)
    pattern_count: int                          # total matched patterns


class BehavioralService:

    # Category threshold above which it counts as "flagged"
    FLAG_THRESHOLD = 0.25

    def predict(self, text: str) -> float:
        """
        Backward-compatible API.
        Returns a composite behavioral risk score in [0, 1].
        """
        return self.predict_profile(text).overall_score

    def predict_profile(self, text: str) -> BehavioralProfile:
        """
        Returns a full BehavioralProfile with per-category breakdown.
        """
        lowered = text.lower()
        category_raw: dict[str, float] = {}
        total_pattern_count = 0

        for cat_name, patterns in _CATEGORIES.items():
            cat_raw = 0.0
            for pattern, weight in patterns:
                if pattern.search(lowered):
                    cat_raw += weight
                    total_pattern_count += 1
            category_raw[cat_name] = cat_raw

        # Normalize each category to [0, 1]
        category_scores: dict[str, float] = {}
        for cat_name, raw in category_raw.items():
            max_possible = _CATEGORY_MAX.get(cat_name, 1.0) or 1.0
            category_scores[cat_name] = round(min(raw / max_possible, 1.0), 4)

        # Composite score: weighted average with emphasis on critical categories
        # negative_coping and activity get higher weight in composite
        weights = {
            "sleep":           1.0,
            "appetite":        1.0,
            "social":          1.2,
            "concentration":   0.8,
            "energy":          0.9,
            "physical":        0.7,
            "activity":        1.3,
            "negative_coping": 1.5,
        }
        total_weight = sum(weights.values())
        composite = sum(
            category_scores[cat] * weights.get(cat, 1.0)
            for cat in category_scores
        ) / total_weight

        overall_score = round(min(composite, 1.0), 4)

        # Flagged categories
        flagged = [
            cat for cat, score in category_scores.items()
            if score >= self.FLAG_THRESHOLD
        ]

        # Dominant category
        dominant = max(category_scores, key=category_scores.get) if category_scores else None
        if dominant and category_scores.get(dominant, 0.0) < 0.05:
            dominant = None

        return BehavioralProfile(
            overall_score=overall_score,
            category_scores=category_scores,
            flagged_categories=flagged,
            dominant_category=dominant,
            pattern_count=total_pattern_count,
        )
