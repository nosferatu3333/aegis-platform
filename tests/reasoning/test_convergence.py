from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from aegis_os.reasoning import (
    CandidateEvaluation,
    CandidatePath,
    CandidatePathGenerator,
    ConvergenceController,
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
) -> ReasoningRequest:
    return ReasoningRequest(
        reasoning_request_id="reason-005",
        intent_ref="intent-005",
        outcome_ref="outcome-005",
        project_context_ref="project-005",
        uncertainty_signals=uncertainty_signals,
        risk_signals=risk_signals,
        constraints=constraints,
        requested_depth=2,
        budget=3,
    )


def make_candidates(
    request: ReasoningRequest,
    *,
    count: int = 3,
) -> tuple[CandidatePath, ...]:
    return CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
        candidate_count=count,
    )


def make_evaluation(
    candidate: CandidatePath,
    *,
    constraint_alignment: int = 3,
    evidence_readiness: int = 3,
    uncertainty_exposure: int = 3,
    risk_exposure: int = 3,
    dependency_burden: int = 3,
    directness: int = 3,
) -> CandidateEvaluation:
    aggregate = sum(
        (
            constraint_alignment,
            evidence_readiness,
            uncertainty_exposure,
            risk_exposure,
            dependency_burden,
            directness,
        )
    )

    return CandidateEvaluation(
        candidate_id=candidate.candidate_id,
        constraint_alignment=constraint_alignment,
        evidence_readiness=evidence_readiness,
        uncertainty_exposure=uncertainty_exposure,
        risk_exposure=risk_exposure,
        dependency_burden=dependency_burden,
        directness=directness,
        aggregate_score=aggregate,
        strengths=(),
        limitations=(),
    )


def test_status_values_are_frozen() -> None:
    assert ConvergenceStatus.RESOLVED.value == "RESOLVED"
    assert ConvergenceStatus.TIED.value == "TIED"
    assert ConvergenceStatus.INSUFFICIENT.value == "INSUFFICIENT"


def test_convergence_requires_reasoning_request() -> None:
    request = make_request()
    candidates = make_candidates(request, count=2)
    evaluations = tuple(make_evaluation(candidate) for candidate in candidates)

    with pytest.raises(TypeError, match="ReasoningRequest"):
        ConvergenceController().converge(
            "invalid",  # type: ignore[arg-type]
            candidates,
            evaluations,
        )


def test_convergence_requires_candidate_tuple() -> None:
    request = make_request()
    candidates = make_candidates(request, count=2)

    evaluations = tuple(make_evaluation(candidate) for candidate in candidates)

    with pytest.raises(TypeError, match="tuple"):
        ConvergenceController().converge(
            request,
            list(candidates),  # type: ignore[arg-type]
            evaluations,
        )


def test_convergence_requires_evaluation_tuple() -> None:
    request = make_request()
    candidates = make_candidates(request, count=2)

    evaluations = tuple(make_evaluation(candidate) for candidate in candidates)

    with pytest.raises(TypeError, match="tuple"):
        ConvergenceController().converge(
            request,
            candidates,
            list(evaluations),  # type: ignore[arg-type]
        )


def test_convergence_requires_at_least_two_candidates() -> None:
    request = make_request()
    candidate = make_candidates(request, count=2)[0]

    with pytest.raises(ValueError, match="at least 2"):
        ConvergenceController().converge(
            request,
            (candidate,),
            (make_evaluation(candidate),),
        )


def test_candidate_and_evaluation_counts_must_match() -> None:
    request = make_request()
    candidates = make_candidates(request, count=2)

    with pytest.raises(ValueError, match="counts must match"):
        ConvergenceController().converge(
            request,
            candidates,
            (make_evaluation(candidates[0]),),
        )


def test_candidate_and_evaluation_ids_must_match_exactly() -> None:
    request = make_request()
    candidates = make_candidates(request, count=2)

    wrong = CandidateEvaluation(
        candidate_id="not-a-candidate",
        constraint_alignment=3,
        evidence_readiness=3,
        uncertainty_exposure=3,
        risk_exposure=3,
        dependency_burden=3,
        directness=3,
        aggregate_score=18,
        strengths=(),
        limitations=(),
    )

    with pytest.raises(ValueError, match="identifier sets"):
        ConvergenceController().converge(
            request,
            candidates,
            (
                make_evaluation(candidates[0]),
                wrong,
            ),
        )


def test_duplicate_candidate_ids_are_rejected() -> None:
    request = make_request()
    candidate = make_candidates(request, count=2)[0]

    evaluations = (
        make_evaluation(candidate),
        CandidateEvaluation(
            candidate_id=candidate.candidate_id,
            constraint_alignment=2,
            evidence_readiness=2,
            uncertainty_exposure=2,
            risk_exposure=2,
            dependency_burden=2,
            directness=2,
            aggregate_score=12,
            strengths=(),
            limitations=(),
        ),
    )

    with pytest.raises(ValueError, match="candidate identifiers"):
        ConvergenceController().converge(
            request,
            (candidate, candidate),
            evaluations,
        )


def test_mismatched_intent_is_rejected() -> None:
    request = make_request()
    candidates = make_candidates(request, count=2)

    altered = CandidatePath(
        candidate_id=candidates[0].candidate_id,
        intent_ref="wrong-intent",
        outcome_ref=candidates[0].outcome_ref,
        label=candidates[0].label,
        summary=candidates[0].summary,
        primary_objective=candidates[0].primary_objective,
        assumptions=candidates[0].assumptions,
        constraints_acknowledged=candidates[0].constraints_acknowledged,
        evidence_needs=candidates[0].evidence_needs,
        known_uncertainty=candidates[0].known_uncertainty,
    )

    altered_candidates = (
        altered,
        candidates[1],
    )

    evaluations = tuple(make_evaluation(candidate) for candidate in altered_candidates)

    with pytest.raises(ValueError, match="intent_ref"):
        ConvergenceController().converge(
            request,
            altered_candidates,
            evaluations,
        )


def test_unique_highest_score_resolves() -> None:
    request = make_request()
    candidates = make_candidates(request, count=3)

    evaluations = (
        make_evaluation(
            candidates[0],
            directness=4,
        ),
        make_evaluation(
            candidates[1],
            directness=2,
        ),
        make_evaluation(
            candidates[2],
            directness=1,
        ),
    )

    result = ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    assert result.status is ConvergenceStatus.RESOLVED
    assert result.preferred_candidate_id == candidates[0].candidate_id
    assert result.eligible_candidate_ids == (candidates[0].candidate_id,)


def test_top_score_tie_remains_tied() -> None:
    request = make_request()
    candidates = make_candidates(request, count=3)

    evaluations = (
        make_evaluation(
            candidates[0],
            directness=4,
        ),
        make_evaluation(
            candidates[1],
            directness=4,
        ),
        make_evaluation(
            candidates[2],
            directness=1,
        ),
    )

    result = ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    assert result.status is ConvergenceStatus.TIED
    assert result.preferred_candidate_id is None
    assert result.eligible_candidate_ids == (
        candidates[0].candidate_id,
        candidates[1].candidate_id,
    )


def test_input_order_does_not_break_tie() -> None:
    request = make_request()
    candidates = make_candidates(request, count=3)

    evaluations = (
        make_evaluation(candidates[0], directness=4),
        make_evaluation(candidates[1], directness=4),
        make_evaluation(candidates[2], directness=1),
    )

    first = ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    reversed_candidates = tuple(reversed(candidates))
    reversed_evaluations = tuple(reversed(evaluations))

    second = ConvergenceController().converge(
        request,
        reversed_candidates,
        reversed_evaluations,
    )

    assert first.status is ConvergenceStatus.TIED
    assert second.status is ConvergenceStatus.TIED

    assert set(first.eligible_candidate_ids) == set(second.eligible_candidate_ids)

    assert first.preferred_candidate_id is None
    assert second.preferred_candidate_id is None


def test_insufficient_evidence_readiness_blocks_resolution() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
    )
    candidates = make_candidates(request, count=2)

    evaluations = (
        make_evaluation(
            candidates[0],
            evidence_readiness=1,
            directness=4,
        ),
        make_evaluation(
            candidates[1],
            evidence_readiness=2,
            directness=1,
        ),
    )

    result = ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    assert result.status is ConvergenceStatus.INSUFFICIENT
    assert result.preferred_candidate_id is None


def test_insufficient_uncertainty_handling_blocks_resolution() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
    )
    candidates = make_candidates(request, count=2)

    evaluations = (
        make_evaluation(
            candidates[0],
            uncertainty_exposure=1,
            directness=4,
        ),
        make_evaluation(
            candidates[1],
            uncertainty_exposure=2,
            directness=1,
        ),
    )

    result = ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    assert result.status is ConvergenceStatus.INSUFFICIENT


def test_insufficient_risk_handling_blocks_resolution() -> None:
    request = make_request(
        risk_signals=("reversal cost",),
    )
    candidates = make_candidates(request, count=2)

    evaluations = (
        make_evaluation(
            candidates[0],
            risk_exposure=1,
            directness=4,
        ),
        make_evaluation(
            candidates[1],
            risk_exposure=2,
            directness=1,
        ),
    )

    result = ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    assert result.status is ConvergenceStatus.INSUFFICIENT


def test_no_pressure_does_not_trigger_sufficiency_gate() -> None:
    request = make_request()
    candidates = make_candidates(request, count=2)

    evaluations = (
        make_evaluation(
            candidates[0],
            evidence_readiness=1,
            uncertainty_exposure=1,
            risk_exposure=1,
            directness=4,
        ),
        make_evaluation(
            candidates[1],
            evidence_readiness=1,
            uncertainty_exposure=1,
            risk_exposure=1,
            directness=1,
        ),
    )

    result = ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    assert result.status is ConvergenceStatus.RESOLVED


def test_convergence_is_deterministic() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
    )

    candidates = make_candidates(request, count=3)

    evaluations = (
        make_evaluation(candidates[0], directness=4),
        make_evaluation(candidates[1], directness=2),
        make_evaluation(candidates[2], directness=1),
    )

    controller = ConvergenceController()

    first = controller.converge(
        request,
        candidates,
        evaluations,
    )

    second = controller.converge(
        request,
        candidates,
        evaluations,
    )

    assert first == second


def test_convergence_does_not_mutate_inputs() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
    )

    candidates = make_candidates(request, count=2)

    evaluations = (
        make_evaluation(candidates[0], directness=4),
        make_evaluation(candidates[1], directness=1),
    )

    request_before = request.to_dict()
    candidates_before = tuple(candidate.to_dict() for candidate in candidates)
    evaluations_before = tuple(evaluation.to_dict() for evaluation in evaluations)

    ConvergenceController().converge(
        request,
        candidates,
        evaluations,
    )

    assert request.to_dict() == request_before

    assert tuple(candidate.to_dict() for candidate in candidates) == candidates_before

    assert (
        tuple(evaluation.to_dict() for evaluation in evaluations) == evaluations_before
    )


def test_result_serialization_is_deterministic() -> None:
    result = ConvergenceResult(
        status=ConvergenceStatus.TIED,
        preferred_candidate_id=None,
        eligible_candidate_ids=("candidate-a", "candidate-b"),
        reason="tie",
    )

    assert result.to_dict() == result.to_dict()


def test_result_is_immutable() -> None:
    result = ConvergenceResult(
        status=ConvergenceStatus.TIED,
        preferred_candidate_id=None,
        eligible_candidate_ids=("candidate-a", "candidate-b"),
        reason="tie",
    )

    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.reason = "changed"  # type: ignore[misc]


def test_unresolved_result_cannot_expose_preferred_candidate() -> None:
    with pytest.raises(ValueError, match="unresolved"):
        ConvergenceResult(
            status=ConvergenceStatus.TIED,
            preferred_candidate_id="candidate-a",
            eligible_candidate_ids=("candidate-a", "candidate-b"),
            reason="tie",
        )


def test_resolved_result_requires_preferred_candidate() -> None:
    with pytest.raises(ValueError, match="requires"):
        ConvergenceResult(
            status=ConvergenceStatus.RESOLVED,
            preferred_candidate_id=None,
            eligible_candidate_ids=("candidate-a",),
            reason="resolved",
        )


def test_result_exposes_no_authority_fields() -> None:
    result = ConvergenceResult(
        status=ConvergenceStatus.RESOLVED,
        preferred_candidate_id="candidate-a",
        eligible_candidate_ids=("candidate-a",),
        reason="resolved",
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
    }

    assert forbidden.isdisjoint(serialized)
