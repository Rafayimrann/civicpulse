"""
Triage orchestration: calls the configured TriageProvider, measures latency,
and falls back to RuleBasedTriage on ANY TriageError so a citizen never sees
a 500 because Groq is rate-limited. Also maintains the in-process ring
buffer of recent outcomes surfaced by GET /api/meta/providers.

This is the one place business rules about "what happens when triage fails"
live - not in routes, not in the provider itself.
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from app.metrics import TRIAGE_FALLBACK_COUNT, TRIAGE_LATENCY
from app.providers.triage.base import TriageError, TriageProvider
from app.providers.triage.rules import RuleBasedTriage
from app.schemas import TriageOutcome, TriageResult

logger = logging.getLogger("app.triage")

_MAX_OUTCOMES = 20


class TriageOutcomeStore:
    """Process-local ring buffer of the last N triage outcomes. Not durable
    by design - it's an observability surface (GET /api/meta/providers), not
    an audit log; triaged_by/triage_latency_ms on the row is the durable copy."""

    def __init__(self, maxlen: int = _MAX_OUTCOMES) -> None:
        self._outcomes: deque[TriageOutcome] = deque(maxlen=maxlen)

    def record(self, outcome: TriageOutcome) -> None:
        self._outcomes.appendleft(outcome)

    def recent(self) -> list[TriageOutcome]:
        return list(self._outcomes)


class TriageService:
    def __init__(
        self,
        provider: TriageProvider,
        outcome_store: TriageOutcomeStore,
        fallback: TriageProvider | None = None,
    ) -> None:
        self._provider = provider
        self._fallback = fallback or RuleBasedTriage()
        self._outcomes = outcome_store

    @property
    def active_provider_name(self) -> str:
        return self._provider.name

    def recent_outcomes(self) -> list[TriageOutcome]:
        return self._outcomes.recent()

    async def triage(self, text: str, location: str, complaint_id: uuid.UUID) -> tuple[TriageResult, str, int]:
        """Returns (result, triaged_by, latency_ms)."""
        start = time.perf_counter()
        fallback_used = False
        triaged_by = self._provider.name

        try:
            result = await self._provider.triage(text, location)
        except TriageError as exc:
            logger.warning(
                "Triage provider failed, falling back to rules",
                extra={
                    "complaint_id": str(complaint_id),
                    "provider": self._provider.name,
                    "error_class": type(exc).__name__,
                },
            )
            result = await self._fallback.triage(text, location)
            triaged_by = "rules:fallback"
            fallback_used = True

        latency_ms = int((time.perf_counter() - start) * 1000)
        TRIAGE_LATENCY.labels(provider=triaged_by).observe(latency_ms / 1000)
        if fallback_used:
            TRIAGE_FALLBACK_COUNT.inc()

        self._outcomes.record(
            TriageOutcome(
                complaint_id=complaint_id,
                provider=triaged_by,
                latency_ms=latency_ms,
                fallback=fallback_used,
                timestamp=datetime.now(timezone.utc),
            )
        )

        return result, triaged_by, latency_ms
