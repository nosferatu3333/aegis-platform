from __future__ import annotations

from dataclasses import fields

import pytest

from aegis_os.intent import IntentInterpreter, IntentRequest, OutcomeModeler
from aegis_os.project import ProjectState, ProjectStateManager, ProjectStatus


def _outcome():
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a one-page architecture proposal.",
            explicit_constraints=("one page",),
        )
    )

    return OutcomeModeler().model(
        interpretation,
        intent_ref="intent-project-001",
        inferred_constraints=("preserve architecture",),
        outcome_uncertainties=("audience unresolved",),
    )


def test_project_state_has_exact_six_dimensions() -> None:
    assert tuple(field.name for field in fields(ProjectState)) == (
        "project_id",
        "outcome_ref",
        "status",
        "current_state",
        "active_constraints",
        "unresolved_issues",
    )


def test_project_status_has_exact_five_values() -> None:
    assert tuple(status.value for status in ProjectStatus) == (
        "NOT_STARTED",
        "ACTIVE",
        "BLOCKED",
        "COMPLETED",
        "CANCELLED",
    )


def test_project_state_can_be_created_from_outcome() -> None:
    project = ProjectStateManager().create(
        _outcome(),
        project_id="project-001",
    )

    assert project.project_id == "project-001"
    assert project.outcome_ref == "intent-project-001"
    assert project.status is ProjectStatus.NOT_STARTED
    assert project.current_state == "Project established."


def test_default_constraints_preserve_outcome_constraints() -> None:
    project = ProjectStateManager().create(
        _outcome(),
        project_id="project-002",
    )

    assert project.active_constraints == (
        "one page",
        "preserve architecture",
    )


def test_explicit_active_constraints_can_be_supplied() -> None:
    project = ProjectStateManager().create(
        _outcome(),
        project_id="project-003",
        active_constraints=("one page",),
    )

    assert project.active_constraints == ("one page",)


def test_unresolved_issues_are_preserved() -> None:
    project = ProjectStateManager().create(
        _outcome(),
        project_id="project-004",
        unresolved_issues=("audience unresolved",),
    )

    assert project.unresolved_issues == ("audience unresolved",)


def test_status_does_not_create_authority_fields() -> None:
    project = ProjectStateManager().create(
        _outcome(),
        project_id="project-005",
        status=ProjectStatus.ACTIVE,
    )

    payload = project.to_dict()

    forbidden = {
        "authority",
        "approval",
        "execution_permission",
        "governed_verdict",
        "reasoning_mode",
        "candidate_paths",
        "plan",
        "plan_steps",
        "lifecycle_transition",
        "decision_history",
        "revision_history",
    }

    assert forbidden.isdisjoint(payload)


def test_completed_status_does_not_validate_outcome() -> None:
    project = ProjectStateManager().create(
        _outcome(),
        project_id="project-006",
        status=ProjectStatus.COMPLETED,
    )

    payload = project.to_dict()

    assert payload["status"] == "COMPLETED"
    assert "validation_result" not in payload
    assert "outcome_satisfied" not in payload


def test_project_state_does_not_mutate_outcome() -> None:
    outcome = _outcome()
    before = outcome.to_dict()

    ProjectStateManager().create(
        outcome,
        project_id="project-007",
    )

    assert outcome.to_dict() == before


def test_project_state_is_deterministic() -> None:
    outcome = _outcome()
    manager = ProjectStateManager()

    baseline = manager.create(
        outcome,
        project_id="project-008",
        status=ProjectStatus.BLOCKED,
        current_state="Waiting for audience clarification.",
        active_constraints=("one page",),
        unresolved_issues=("audience unresolved",),
    )

    for _ in range(100):
        observed = manager.create(
            outcome,
            project_id="project-008",
            status=ProjectStatus.BLOCKED,
            current_state="Waiting for audience clarification.",
            active_constraints=("one page",),
            unresolved_issues=("audience unresolved",),
        )

        assert observed == baseline
        assert observed.to_dict() == baseline.to_dict()


def test_invalid_status_type_is_rejected() -> None:
    with pytest.raises(TypeError, match="ProjectStatus"):
        ProjectStateManager().create(
            _outcome(),
            project_id="project-009",
            status="ACTIVE",  # type: ignore[arg-type]
        )
