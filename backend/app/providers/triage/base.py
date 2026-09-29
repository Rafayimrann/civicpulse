"""
The TriageProvider interface. Every provider - LLM-backed, local, rule-based,
or simulated - implements this same async Protocol so the service layer
never knows or cares which one is behind it.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas import TriageResult


class TriageError(Exception):
    """Raised by a provider when it cannot produce a result. Callers decide fallback."""


class TriageTimeoutError(TriageError):
    pass


class TriageRetryableError(TriageError):
    """429 / 5xx / timeout - safe to retry once."""


@runtime_checkable
class TriageProvider(Protocol):
    name: str

    async def triage(self, text: str, location: str) -> TriageResult:
        """
        Classify a complaint. Implementations must treat `text` as untrusted
        data, never as instructions: it is content to be categorised, not a
        prompt to be obeyed. Must raise TriageError (or a subclass) on
        failure - never return a partially-valid result.
        """
        ...
