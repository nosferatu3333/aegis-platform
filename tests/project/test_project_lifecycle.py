"""Contract tests for the bounded project lifecycle manager."""

from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields
from itertools import product

import pytest

import aegis_os.project.lifecycle as lifecycle_module
from aegis_os.project import (
    LifecycleTransitionResult,
    ProjectLedger,
    ProjectLifecycleManager,
    ProjectState,
    ProjectStatus,
)

PERMITTED_TRANSITIONS = {
    (ProjectStatus.NOT_STARTED, ProjectStatus.ACTIVE),
    (ProjectStatus.NOT_STARTED, ProjectStatus.CANCELLED),
    (ProjectStatus.ACTIVE, ProjectStatus.BLOCKED),
    (ProjectStatus.ACTIVE, ProjectStatus.COMPLETED),
    (ProjectStatus.ACTIVE, ProjectStatus.CANCELLED),
    (ProjectStatus.BLOCKED, ProjectStatus.ACTIVE),
    (ProjectStatus.BLOCKED, ProjectStatus.CANCELLED),
}
ALL_TRANSITIONS = tuple(product(ProjectStatus, repeat=2))
REJECTED_TRANSITIONS = tuple(
    transition
    for transition in ALL_TRANSITIONS
    if transition not in PERMITTED_TRANSITIONS
)


def _state(status: ProjectStatus = ProjectStatus.NOT_STARTED) -> ProjectState:
    return ProjectState(
        project_id="project-lifecycle-001",
        outcome_ref="intent-lifecycle-001",
        status=status,
        current_state="Lifecycle contract established.",
        active_constraints=("preserve architecture", "simulation only"),
        unresolved_issues=("review pending",),
    )


def _transition(
    source_status: ProjectStatus,
    target_status: ProjectStatus,
) -> LifecycleTransitionResult:
    return ProjectLifecycleManager().transition(
        _state(source_status),
        target_status,
        current_state=f"Caller supplied {target_status.value} state.",
    )


def test_transition_result_has_exact_four_dimensions() -> None:
    assert tuple(field.name for field in fields(LifecycleTransitionResult)) == (
        "source_status",
        "target_status",
        "permitted",
        "resulting_state",
    )


def test_transition_result_is_immutable() -> None:
    result = _transition(ProjectStatus.NOT_STARTED, ProjectStatus.ACTIVE)

    with pytest.raises(FrozenInstanceError):
        result.permitted = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("source_status", "target_status"),
    sorted(PERMITTED_TRANSITIONS, key=lambda item: (item[0].value, item[1].value)),
)
def test_all_seven_permitted_transitions(
    source_status: ProjectStatus,
    target_status: ProjectStatus,
) -> None:
    result = _transition(source_status, target_status)

    assert result.source_status is source_status
    assert result.target_status is target_status
    assert result.permitted is True
    assert result.resulting_state is not None
    assert result.resulting_state.status is target_status


@pytest.mark.parametrize(
    ("source_status", "target_status"),
    REJECTED_TRANSITIONS,
)
def test_every_other_status_pair_is_rejected(
    source_status: ProjectStatus,
    target_status: ProjectStatus,
) -> None:
    result = _transition(source_status, target_status)

    assert result.source_status is source_status
    assert result.target_status is target_status
    assert result.permitted is False
    assert result.resulting_state is None


@pytest.mark.parametrize("status", tuple(ProjectStatus))
def test_all_self_transitions_are_rejected(status: ProjectStatus) -> None:
    result = _transition(status, status)

    assert result.permitted is False
    assert result.resulting_state is None


@pytest.mark.parametrize(
    "terminal_status",
    (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED),
)
@pytest.mark.parametrize("target_status", tuple(ProjectStatus))
def test_terminal_states_reject_every_target(
    terminal_status: ProjectStatus,
    target_status: ProjectStatus,
) -> None:
    assert _transition(terminal_status, target_status).permitted is False


def test_permitted_transition_returns_new_state_without_mutating_source() -> None:
    original = _state(ProjectStatus.ACTIVE)
    before = original.to_dict()

    result = ProjectLifecycleManager().transition(
        original,
        ProjectStatus.BLOCKED,
        current_state="Waiting for architecture review.",
    )

    transitioned = result.resulting_state
    assert transitioned is not None
    assert transitioned is not original
    assert original.to_dict() == before
    assert transitioned.project_id == original.project_id
    assert transitioned.outcome_ref == original.outcome_ref
    assert transitioned.active_constraints == original.active_constraints
    assert transitioned.unresolved_issues == original.unresolved_issues
    assert transitioned.status is ProjectStatus.BLOCKED
    assert transitioned.current_state == "Waiting for architecture review."


def test_rejected_transition_does_not_mutate_source() -> None:
    original = _state(ProjectStatus.NOT_STARTED)
    before = original.to_dict()

    result = ProjectLifecycleManager().transition(
        original,
        ProjectStatus.COMPLETED,
        current_state="Caller supplied rejected state.",
    )

    assert result.permitted is False
    assert result.resulting_state is None
    assert original.to_dict() == before


def test_transition_result_serializes_in_frozen_order() -> None:
    result = _transition(ProjectStatus.ACTIVE, ProjectStatus.COMPLETED)

    payload = result.to_dict()

    assert tuple(payload) == (
        "source_status",
        "target_status",
        "permitted",
        "resulting_state",
    )
    assert payload == {
        "source_status": "ACTIVE",
        "target_status": "COMPLETED",
        "permitted": True,
        "resulting_state": result.resulting_state.to_dict(),
    }


def test_rejected_transition_serializes_without_replacement_state() -> None:
    result = _transition(ProjectStatus.BLOCKED, ProjectStatus.COMPLETED)

    assert result.to_dict() == {
        "source_status": "BLOCKED",
        "target_status": "COMPLETED",
        "permitted": False,
        "resulting_state": None,
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        pytest.param(
            {
                "project_state": "ACTIVE",
                "target_status": ProjectStatus.BLOCKED,
                "current_state": "Blocked.",
            },
            "project_state must be a ProjectState",
            id="invalid-project-state",
        ),
        pytest.param(
            {
                "project_state": _state(ProjectStatus.ACTIVE),
                "target_status": "BLOCKED",
                "current_state": "Blocked.",
            },
            "target_status must be a ProjectStatus",
            id="invalid-target-status",
        ),
        pytest.param(
            {
                "project_state": _state(ProjectStatus.ACTIVE),
                "target_status": ProjectStatus.BLOCKED,
                "current_state": None,
            },
            "current_state must be a non-empty string",
            id="missing-current-state",
        ),
        pytest.param(
            {
                "project_state": _state(ProjectStatus.ACTIVE),
                "target_status": ProjectStatus.BLOCKED,
                "current_state": "   ",
            },
            "current_state must be a non-empty string",
            id="blank-current-state",
        ),
    ],
)
def test_invalid_transition_inputs_are_rejected(
    arguments: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        ProjectLifecycleManager().transition(**arguments)  # type: ignore[arg-type]


def test_current_state_is_required_and_keyword_only() -> None:
    manager = ProjectLifecycleManager()
    state = _state(ProjectStatus.ACTIVE)

    with pytest.raises(TypeError):
        manager.transition(state, ProjectStatus.BLOCKED)

    with pytest.raises(TypeError):
        manager.transition(  # type: ignore[misc]
            state,
            ProjectStatus.BLOCKED,
            "Blocked.",
        )


def test_completed_is_lifecycle_only() -> None:
    result = _transition(ProjectStatus.ACTIVE, ProjectStatus.COMPLETED)
    payload = result.to_dict()
    resulting_state = payload["resulting_state"]

    assert isinstance(resulting_state, dict)
    assert resulting_state["status"] == "COMPLETED"
    forbidden = {
        "outcome_satisfied",
        "success_conditions_met",
        "validation_result",
        "approval",
        "authority",
        "execution_permission",
        "execution_result",
        "governed_verdict",
        "real_world_completion",
    }
    assert forbidden.isdisjoint(payload)
    assert forbidden.isdisjoint(resulting_state)


def test_transition_does_not_append_to_project_ledger() -> None:
    state = _state(ProjectStatus.ACTIVE)
    ledger = ProjectLedger(state.project_id)

    result = ProjectLifecycleManager().transition(
        state,
        ProjectStatus.BLOCKED,
        current_state="Review pending.",
    )

    assert result.permitted is True
    assert ledger.records == ()


def test_lifecycle_module_has_no_forbidden_subsystem_dependencies() -> None:
    tree = ast.parse(inspect.getsource(lifecycle_module))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert imported_modules == {"__future__", "dataclasses", "models"}
    forbidden_names = {
        "ProjectLedger",
        "ReasoningRequest",
        "ReasoningController",
        "AdaptiveEscalationPolicy",
        "CandidatePathGenerator",
        "CandidateEvaluator",
        "ConvergenceController",
        "AdaptiveReasoningCycle",
        "authority",
        "approval",
        "execution",
        "memory",
        "network",
        "subprocess",
        "tool",
    }
    assert forbidden_names.isdisjoint(vars(lifecycle_module))


def test_identical_transition_is_deterministic_for_100_repetitions() -> None:
    state = _state(ProjectStatus.ACTIVE)
    manager = ProjectLifecycleManager()
    baseline = manager.transition(
        state,
        ProjectStatus.BLOCKED,
        current_state="Waiting for review.",
    )

    for _ in range(100):
        observed = manager.transition(
            state,
            ProjectStatus.BLOCKED,
            current_state="Waiting for review.",
        )
        assert observed == baseline
        assert observed.to_dict() == baseline.to_dict()


def test_identical_rejection_is_deterministic_for_100_repetitions() -> None:
    state = _state(ProjectStatus.NOT_STARTED)
    manager = ProjectLifecycleManager()
    baseline = manager.transition(
        state,
        ProjectStatus.COMPLETED,
        current_state="Rejected transition narrative.",
    )

    for _ in range(100):
        observed = manager.transition(
            state,
            ProjectStatus.COMPLETED,
            current_state="Rejected transition narrative.",
        )
        assert observed == baseline
        assert observed.to_dict() == baseline.to_dict()
