"""Deterministic project lifecycle transition contract."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ProjectState, ProjectStatus

_PERMITTED_TRANSITIONS = {
    ProjectStatus.NOT_STARTED: frozenset(
        {
            ProjectStatus.ACTIVE,
            ProjectStatus.CANCELLED,
        }
    ),
    ProjectStatus.ACTIVE: frozenset(
        {
            ProjectStatus.BLOCKED,
            ProjectStatus.COMPLETED,
            ProjectStatus.CANCELLED,
        }
    ),
    ProjectStatus.BLOCKED: frozenset(
        {
            ProjectStatus.ACTIVE,
            ProjectStatus.CANCELLED,
        }
    ),
    ProjectStatus.COMPLETED: frozenset(),
    ProjectStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class LifecycleTransitionResult:
    """Immutable structural result of one lifecycle transition request."""

    source_status: ProjectStatus
    target_status: ProjectStatus
    permitted: bool
    resulting_state: ProjectState | None

    def __post_init__(self) -> None:
        if not isinstance(self.source_status, ProjectStatus):
            raise TypeError("source_status must be a ProjectStatus")

        if not isinstance(self.target_status, ProjectStatus):
            raise TypeError("target_status must be a ProjectStatus")

        if not isinstance(self.permitted, bool):
            raise TypeError("permitted must be a bool")

        if self.permitted:
            if not isinstance(self.resulting_state, ProjectState):
                raise TypeError(
                    "permitted transition requires a resulting ProjectState"
                )

            if self.resulting_state.status is not self.target_status:
                raise ValueError("resulting_state status must match target_status")
        elif self.resulting_state is not None:
            raise ValueError("rejected transition cannot contain resulting_state")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization in the frozen field order."""
        return {
            "source_status": self.source_status.value,
            "target_status": self.target_status.value,
            "permitted": self.permitted,
            "resulting_state": (
                self.resulting_state.to_dict()
                if self.resulting_state is not None
                else None
            ),
        }


class ProjectLifecycleManager:
    """Apply the frozen project lifecycle graph without side effects."""

    def transition(
        self,
        project_state: ProjectState,
        target_status: ProjectStatus,
        *,
        current_state: str,
    ) -> LifecycleTransitionResult:
        """Return a deterministic transition result without mutating input."""
        if not isinstance(project_state, ProjectState):
            raise TypeError("project_state must be a ProjectState")

        if not isinstance(target_status, ProjectStatus):
            raise TypeError("target_status must be a ProjectStatus")

        if not isinstance(current_state, str) or not current_state.strip():
            raise TypeError("current_state must be a non-empty string")

        source_status = project_state.status
        permitted = target_status in _PERMITTED_TRANSITIONS[source_status]

        if not permitted:
            return LifecycleTransitionResult(
                source_status=source_status,
                target_status=target_status,
                permitted=False,
                resulting_state=None,
            )

        resulting_state = ProjectState(
            project_id=project_state.project_id,
            outcome_ref=project_state.outcome_ref,
            status=target_status,
            current_state=current_state,
            active_constraints=project_state.active_constraints,
            unresolved_issues=project_state.unresolved_issues,
        )

        return LifecycleTransitionResult(
            source_status=source_status,
            target_status=target_status,
            permitted=True,
            resulting_state=resulting_state,
        )
