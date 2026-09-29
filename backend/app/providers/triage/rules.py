"""
RuleBasedTriage: deterministic keyword classifier.

This is the provider of last resort. It must NEVER raise - every other
provider falls back to this one, so if this one can fail the whole
"a citizen never sees a 500 because a third party was rate-limited"
guarantee collapses. Every code path here returns a valid TriageResult.
"""
from __future__ import annotations

import time

from app.models import Category, Priority
from app.schemas import TriageResult

# Ordered so more specific / higher-urgency signals are checked first.
_KEYWORDS: list[tuple[Category, tuple[str, ...]]] = [
    (Category.water, ("burst", "flood", "water main", "leak", "pipe", "sewage overflow", "no water")),
    (Category.electricity, ("power outage", "electricity", "transformer", "sparking", "exposed wire", "power cut")),
    (Category.sanitation, ("garbage", "trash", "sewage", "drain", "waste", "sanitation", "smell")),
    (Category.roads, ("pothole", "road", "street collapse", "bridge", "traffic signal", "crack in road")),
    (Category.streetlights, ("streetlight", "street light", "lamp post", "dark street")),
]

_HIGH_URGENCY_WORDS = (
    "flooding", "flood", "fire", "collapse", "sparking", "exposed wire", "gas leak",
    "burst", "ground floor", "emergency", "injur", "danger",
)


class RuleBasedTriage:
    name = "rules"

    async def triage(self, text: str, location: str) -> TriageResult:
        start = time.perf_counter()
        lowered = text.lower()

        category = Category.other
        for cat, keywords in _KEYWORDS:
            if any(kw in lowered for kw in keywords):
                category = cat
                break

        priority = Priority.high if any(w in lowered for w in _HIGH_URGENCY_WORDS) else Priority.normal
        if category is Category.other and priority is Priority.normal:
            priority = Priority.low

        summary = text.strip().replace("\n", " ")
        if len(summary) > 137:
            summary = summary[:137] + "..."

        # Latency measurement kept for parity with the other providers, even
        # though this call is effectively instantaneous.
        _ = (time.perf_counter() - start) * 1000

        return TriageResult(category=category, priority=priority, summary=summary, confidence=0.55)
