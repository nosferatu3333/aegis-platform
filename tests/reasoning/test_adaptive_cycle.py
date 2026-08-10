from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from aegis_os.reasoning import (
    AdaptiveCycleResult,
    AdaptiveReasoningCycle,
    ConvergenceResult,
    ConvergenceStatus,
    ReasoningMode,
    ReasoningRequest,
)


def make_request(
    *,
    uncertainty_signals: tuple[str, ...] = (),
    risk_signals: tuple[str, ...] = (),
    constraints: tuple[str, ...] = (),
    requested_depth: int = 0,
    budget: int = 3,
) -> ReasoningRequest:
    return ReasoningRequest(
        reasoning_request_id="reason-006",
        intent_ref="intent-006",
        outcome_ref="outcome-006",
        project_context_ref="project-006",
        uncertainty_signals=uncertainty_signals,
        risk_signals=risk_signals,
        constraints=constraints,
        requested_depth=requested_depth,
        budget=budget,
    )


def test_cycle_requires_reasoning_request() -> None:
    with pytest.raises(TypeError, match="ReasoningRequest"):
        AdaptiveReasoningCycle().run(
            "invalid",  # type: ignore[arg-type]
        )


def test_default_branch_candidate_count_is_three() -> None:
    cycle = AdaptiveReasoningCycle()

    assert cycle.DEFAULT_BRANCH_CANDIDATE_COUNT == 3


@pytest.mark.parametrize(
    "value",
    (
        True,
        2.5,
        "3",
    ),
)
def test_branch_candidate_count_requires_integer(value: object) -> None:
    with pytest.raises(TypeError, match="integer"):
        AdaptiveReasoningCycle(
            branch_candidate_count=value,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "value",
    (
        0,
        1,
        6,
        10,
    ),
)
def test_branch_candidate_count_respects_generator_bounds(
    value: int,
) -> None:
    with pytest.raises(ValueError, match="bounds"):
        AdaptiveReasoningCycle(
            branch_candidate_count=value,
        )


def test_direct_mode_stops_without_branching() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            requested_depth=0,
            budget=1,
        )
    )

    assert result.mode is ReasoningMode.DIRECT
    assert result.candidates == ()
    assert result.evaluations == ()
    assert result.convergence is None


def test_verify_mode_stops_without_external_verification() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            risk_signals=("possible mismatch",),
            requested_depth=0,
            budget=1,
        )
    )

    assert result.mode is ReasoningMode.VERIFY
    assert result.candidates == ()
    assert result.evaluations == ()
    assert result.convergence is None
    assert "verification" in result.reason.lower()


def test_search_mode_stops_without_external_search() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            uncertainty_signals=("external evidence required",),
            requested_depth=0,
            budget=3,
        )
    )

    assert result.mode is ReasoningMode.SEARCH
    assert result.candidates == ()
    assert result.evaluations == ()
    assert result.convergence is None
    assert "external" in result.reason.lower()


def test_branch_mode_executes_complete_bounded_pipeline() -> None:
    request = make_request(
        uncertainty_signals=("multiple approaches",),
        requested_depth=0,
        budget=3,
    )

    result = AdaptiveReasoningCycle().run(request)

    assert result.mode is ReasoningMode.BRANCH
    assert len(result.candidates) == 3
    assert len(result.evaluations) == 3
    assert result.convergence is not None

    assert result.convergence.status in {
        ConvergenceStatus.RESOLVED,
        ConvergenceStatus.TIED,
        ConvergenceStatus.INSUFFICIENT,
    }


def test_branch_candidate_identity_flows_into_evaluation() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            uncertainty_signals=("multiple approaches",),
            budget=3,
        )
    )

    candidate_ids = tuple(candidate.candidate_id for candidate in result.candidates)

    evaluation_ids = tuple(evaluation.candidate_id for evaluation in result.evaluations)

    assert candidate_ids == evaluation_ids


def test_branch_result_is_deterministic() -> None:
    request = make_request(
        uncertainty_signals=("multiple approaches",),
        constraints=("limited capacity",),
        budget=3,
    )

    cycle = AdaptiveReasoningCycle()

    first = cycle.run(request)
    second = cycle.run(request)

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_direct_result_is_deterministic() -> None:
    request = make_request(
        requested_depth=0,
        budget=1,
    )

    cycle = AdaptiveReasoningCycle()

    assert cycle.run(request) == cycle.run(request)


def test_verify_result_is_deterministic() -> None:
    request = make_request(
        risk_signals=("possible mismatch",),
        budget=1,
    )

    cycle = AdaptiveReasoningCycle()

    assert cycle.run(request) == cycle.run(request)


def test_search_result_is_deterministic() -> None:
    request = make_request(
        uncertainty_signals=("external evidence required",),
        budget=3,
    )

    cycle = AdaptiveReasoningCycle()

    assert cycle.run(request) == cycle.run(request)


def test_cycle_does_not_mutate_request() -> None:
    request = make_request(
        uncertainty_signals=("multiple approaches",),
        constraints=("limited capacity",),
        budget=3,
    )

    before = request.to_dict()

    AdaptiveReasoningCycle().run(request)

    assert request.to_dict() == before


def test_result_serialization_is_deterministic() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            requested_depth=0,
            budget=1,
        )
    )

    assert result.to_dict() == result.to_dict()


def test_result_is_immutable() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            requested_depth=0,
            budget=1,
        )
    )

    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.reason = "changed"  # type: ignore[misc]


def test_non_branch_result_cannot_contain_convergence() -> None:
    convergence = ConvergenceResult(
        status=ConvergenceStatus.TIED,
        preferred_candidate_id=None,
        eligible_candidate_ids=("candidate-a", "candidate-b"),
        reason="tie",
    )

    with pytest.raises(ValueError, match="non-BRANCH"):
        AdaptiveCycleResult(
            mode=ReasoningMode.DIRECT,
            candidates=(),
            evaluations=(),
            convergence=convergence,
            reason="invalid",
        )


def test_non_branch_result_contains_no_candidate_artifacts() -> None:
    for request in (
        make_request(
            budget=1,
        ),
        make_request(
            risk_signals=("possible mismatch",),
            budget=1,
        ),
        make_request(
            uncertainty_signals=("external evidence required",),
            budget=3,
        ),
    ):
        result = AdaptiveReasoningCycle().run(request)

        assert result.mode is not ReasoningMode.BRANCH
        assert result.candidates == ()
        assert result.evaluations == ()
        assert result.convergence is None


def test_cycle_result_exposes_no_authority_fields() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            uncertainty_signals=("multiple approaches",),
            budget=3,
        )
    )

    serialized = result.to_dict()

    forbidden = {
        "approval",
        "approved",
        "authority",
        "execution_permission",
        "governed_verdict",
        "verdict",
        "confidence",
        "probability",
        "tool",
        "execute",
        "retry",
    }

    assert forbidden.isdisjoint(serialized)


def test_resolved_convergence_does_not_become_authority() -> None:
    result = AdaptiveReasoningCycle().run(
        make_request(
            uncertainty_signals=("multiple approaches",),
            budget=3,
        )
    )

    serialized = result.to_dict()

    assert "authority" not in serialized
    assert "approval" not in serialized
    assert "execution_permission" not in serialized
    assert "governed_verdict" not in serialized
