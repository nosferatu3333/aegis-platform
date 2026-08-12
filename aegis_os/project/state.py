"""Bounded project-state construction."""

from __future__ import annotations

from aegis_os.intent import OutcomeModel

from .models import ProjectState, ProjectStatus


class ProjectStateManager:
    """Construct bounded project-state representations."""

    def create(
        self,
        outcome: OutcomeModel,
        *,
        project_id: str,
        status: ProjectStatus = ProjectStatus.NOT_STARTED,
        current_state: str = "Project established.",
        active_constraints: tuple[str, ...] | None = None,
        unresolved_issues: tuple[str, ...] = (),
    ) -> ProjectState:
        """Create project state without lifecycle or execution semantics."""
        if not isinstance(outcome, OutcomeModel):
            raise TypeError("outcome must be an OutcomeModel")

        if not isinstance(project_id, str) or not project_id.strip():
            raise TypeError("project_id must be a non-empty string")

        if not isinstance(status, ProjectStatus):
            raise TypeError("status must be a ProjectStatus")

        if not isinstance(current_state, str) or not current_state.strip():
            raise TypeError("current_state must be a non-empty string")

        if active_constraints is None:
            active_constraints = (
                outcome.explicit_constraints + outcome.inferred_constraints
            )

        if not isinstance(active_constraints, tuple):
            raise TypeError("active_constraints must be a tuple")

        if any(
            not isinstance(item, str) or not item.strip() for item in active_constraints
        ):
            raise TypeError("active_constraints must contain non-empty strings")

        if not isinstance(unresolved_issues, tuple):
            raise TypeError("unresolved_issues must be a tuple")

        if any(
            not isinstance(item, str) or not item.strip() for item in unresolved_issues
        ):
            raise TypeError("unresolved_issues must contain non-empty strings")

        return ProjectState(
            project_id=project_id,
            outcome_ref=outcome.intent_ref,
            status=status,
            current_state=current_state,
            active_constraints=active_constraints,
            unresolved_issues=unresolved_issues,
        )
