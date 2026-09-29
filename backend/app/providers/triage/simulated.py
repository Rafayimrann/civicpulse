"""
SimulatedTriage: deterministic fake used to pin CI to a provider that never
talks to the network. Same input always produces the same output, so the
test suite is green on every run regardless of what a real LLM would say.

Also supports failure injection (raise / return malformed data) so the
fallback and validation paths can be exercised deterministically without
needing a real flaky dependency.
"""
from __future__ import annotations

import hashlib

from app.models import Category, Priority
from app.providers.triage.base import TriageError
from app.providers.triage.rules import RuleBasedTriage
from app.schemas import TriageResult

_CATEGORIES = list(Category)
_PRIORITIES = list(Priority)


class SimulatedTriage:
    """
    Deterministic fake for CI testing.

    force_failure=True makes every call raise TriageError, to exercise the
    fallback-to-rules path in tests without relying on a real provider.
    """

    name = "simulated"

    def __init__(self, force_failure: bool = False) -> None:
        self.force_failure = force_failure
        self._rules = RuleBasedTriage()

    async def triage(self, text: str, location: str) -> TriageResult:
        if self.force_failure:
            raise TriageError("SimulatedTriage: forced failure for testing")

        # Deterministic hash of the input picks category/priority/confidence,
        # so the exact same complaint text always classifies identically -
        # unlike a real LLM, which is probabilistic by nature.
        digest = hashlib.sha256(f"{text}|{location}".encode()).hexdigest()
        cat_idx = int(digest[:8], 16) % len(_CATEGORIES)
        pri_idx = int(digest[8:16], 16) % len(_PRIORITIES)
        confidence = 0.5 + (int(digest[16:18], 16) / 255) * 0.5  # 0.5-1.0

        # Reuse the rule-based summariser so the summary is still grounded in
        # the actual complaint text rather than being pure noise.
        base = await self._rules.triage(text, location)

        return TriageResult(
            category=_CATEGORIES[cat_idx],
            priority=_PRIORITIES[pri_idx],
            summary=base.summary,
            confidence=round(confidence, 3),
        )
