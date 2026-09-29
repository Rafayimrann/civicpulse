"""
Complaint status state machine, expressed as an explicit transition table -
not a chain of if/elif - per the brief's explicit requirement. Adding a
transition means editing one dict entry, and the invalid case is a single
membership check, not a growing pile of conditionals.
"""
from __future__ import annotations

from app.models import Status


class InvalidTransitionError(Exception):
    def __init__(self, current: Status, attempted: Status) -> None:
        self.current = current
        self.attempted = attempted
        super().__init__(
            f"Invalid status transition: cannot move from '{current.value}' to '{attempted.value}'"
        )


# open -> in_progress -> resolved/rejected. open -> rejected also allowed.
# resolved and rejected are terminal (no outgoing transitions).
_TRANSITIONS: dict[Status, set[Status]] = {
    Status.open: {Status.in_progress, Status.rejected},
    Status.in_progress: {Status.resolved, Status.rejected},
    Status.resolved: set(),
    Status.rejected: set(),
}


def validate_transition(current: Status, target: Status) -> None:
    allowed = _TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(current, target)
