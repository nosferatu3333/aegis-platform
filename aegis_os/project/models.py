"""Bounded project-state contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProjectStatus(str, Enum):
    """Bounded project-state classification."""

    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class ProjectState:
    """Current operational representation of a project."""

    project_id: str
    outcome_ref: str
    status: ProjectStatus
    current_state: str
    active_constraints: tuple[str, ...]
    unresolved_issues: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise TypeError("project_id must be a non-empty string")

        if not isinstance(self.outcome_ref, str) or not self.outcome_ref.strip():
            raise TypeError("outcome_ref must be a non-empty string")

        if not isinstance(self.status, ProjectStatus):
            raise TypeError("status must be a ProjectStatus")

        if not isinstance(self.current_state, str) or not self.current_state.strip():
            raise TypeError("current_state must be a non-empty string")

        for name, value in (
            ("active_constraints", self.active_constraints),
            ("unresolved_issues", self.unresolved_issues),
        ):
            if not isinstance(value, tuple):
                raise TypeError(f"{name} must be a tuple")

            if any(not isinstance(item, str) or not item.strip() for item in value):
                raise TypeError(f"{name} must contain non-empty strings")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "project_id": self.project_id,
            "outcome_ref": self.outcome_ref,
            "status": self.status.value,
            "current_state": self.current_state,
            "active_constraints": list(self.active_constraints),
            "unresolved_issues": list(self.unresolved_issues),
        }
