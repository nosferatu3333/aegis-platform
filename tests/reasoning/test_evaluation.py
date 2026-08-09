from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from aegis_os.reasoning import (
    CandidateEvaluation,
    CandidateEvaluator,
    CandidatePath,
    CandidatePathGenerator,
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
        reasoning_request_id="reason-004",
        intent_ref="intent-004",
        outcome_ref="outcome-004",
        project_context_ref="project-004",
        uncertainty_signals=uncertainty_signals,
        risk_signals=risk_signals,
        constraints=constraints,
        requested_depth=2,
        budget=3,
    )


def make_candidates(
    request: ReasoningRequest,
    *,
    count: int = 5,
) -> tuple[CandidatePath, ...]:
    return CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
        candidate_count=count,
    )


def test_evaluator_rejects_non_reasoning_request() -> None:
    evaluator = CandidateEvaluator()
    request = make_request()

    with pytest.raises(TypeError, match="ReasoningRequest"):
        evaluator.evaluate(
            "invalid",  # type: ignore[arg-type]
            make_candidates(request),
        )


def test_evaluator_requires_candidate_tuple() -> None:
    evaluator = CandidateEvaluator()
    request = make_request()

    with pytest.raises(TypeError, match="tuple"):
        evaluator.evaluate(
            request,
            list(make_candidates(request)),  # type: ignore[arg-type]
        )


def test_evaluator_rejects_empty_candidates() -> None:
    with pytest.raises(ValueError, match="at least one"):
        CandidateEvaluator().evaluate(
            make_request(),
            (),
        )


def test_evaluator_rejects_non_candidate_member() -> None:
    with pytest.raises(TypeError, match="CandidatePath"):
        CandidateEvaluator().evaluate(
            make_request(),
            ("invalid",),  # type: ignore[arg-type]
        )


def test_evaluator_preserves_input_candidate_order() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    assert [item.candidate_id for item in evaluations] == [
        candidate.candidate_id for candidate in candidates
    ]


def test_evaluator_preserves_candidate_identity() -> None:
    request = make_request()
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    assert {item.candidate_id for item in evaluations} == {
        candidate.candidate_id for candidate in candidates
    }


def test_duplicate_candidate_ids_are_rejected() -> None:
    request = make_request()
    candidate = make_candidates(request, count=2)[0]

    with pytest.raises(ValueError, match="identifiers"):
        CandidateEvaluator().evaluate(
            request,
            (candidate, candidate),
        )


def test_mismatched_intent_is_rejected() -> None:
    request = make_request()
    candidate = make_candidates(request, count=2)[0]

    mismatched = CandidatePath(
        candidate_id=candidate.candidate_id,
        intent_ref="different-intent",
        outcome_ref=candidate.outcome_ref,
        label=candidate.label,
        summary=candidate.summary,
        primary_objective=candidate.primary_objective,
        assumptions=candidate.assumptions,
        constraints_acknowledged=candidate.constraints_acknowledged,
        evidence_needs=candidate.evidence_needs,
        known_uncertainty=candidate.known_uncertainty,
    )

    with pytest.raises(ValueError, match="intent_ref"):
        CandidateEvaluator().evaluate(
            request,
            (mismatched,),
        )


def test_mismatched_outcome_is_rejected() -> None:
    request = make_request()
    candidate = make_candidates(request, count=2)[0]

    mismatched = CandidatePath(
        candidate_id=candidate.candidate_id,
        intent_ref=candidate.intent_ref,
        outcome_ref="different-outcome",
        label=candidate.label,
        summary=candidate.summary,
        primary_objective=candidate.primary_objective,
        assumptions=candidate.assumptions,
        constraints_acknowledged=candidate.constraints_acknowledged,
        evidence_needs=candidate.evidence_needs,
        known_uncertainty=candidate.known_uncertainty,
    )

    with pytest.raises(ValueError, match="outcome_ref"):
        CandidateEvaluator().evaluate(
            request,
            (mismatched,),
        )


def test_unsupported_candidate_label_is_rejected() -> None:
    request = make_request()
    candidate = make_candidates(request, count=2)[0]

    unsupported = CandidatePath(
        candidate_id=candidate.candidate_id,
        intent_ref=candidate.intent_ref,
        outcome_ref=candidate.outcome_ref,
        label="Unknown-Approach",
        summary=candidate.summary,
        primary_objective=candidate.primary_objective,
        assumptions=candidate.assumptions,
        constraints_acknowledged=candidate.constraints_acknowledged,
        evidence_needs=candidate.evidence_needs,
        known_uncertainty=candidate.known_uncertainty,
    )

    with pytest.raises(ValueError, match="unsupported"):
        CandidateEvaluator().evaluate(
            request,
            (unsupported,),
        )


def test_all_dimension_scores_are_bounded_zero_through_four() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )

    evaluations = CandidateEvaluator().evaluate(
        request,
        make_candidates(request),
    )

    for evaluation in evaluations:
        scores = (
            evaluation.constraint_alignment,
            evaluation.evidence_readiness,
            evaluation.uncertainty_exposure,
            evaluation.risk_exposure,
            evaluation.dependency_burden,
            evaluation.directness,
        )

        assert all(0 <= score <= 4 for score in scores)


def test_aggregate_equals_sum_of_dimension_scores() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )

    evaluations = CandidateEvaluator().evaluate(
        request,
        make_candidates(request),
    )

    for evaluation in evaluations:
        assert evaluation.aggregate_score == sum(
            (
                evaluation.constraint_alignment,
                evaluation.evidence_readiness,
                evaluation.uncertainty_exposure,
                evaluation.risk_exposure,
                evaluation.dependency_burden,
                evaluation.directness,
            )
        )


def test_evaluation_record_rejects_out_of_range_score() -> None:
    with pytest.raises(ValueError, match="0..4"):
        CandidateEvaluation(
            candidate_id="candidate-1",
            constraint_alignment=5,
            evidence_readiness=4,
            uncertainty_exposure=4,
            risk_exposure=4,
            dependency_burden=4,
            directness=4,
            aggregate_score=25,
            strengths=(),
            limitations=(),
        )


def test_evaluation_record_rejects_boolean_score() -> None:
    with pytest.raises(TypeError, match="integers"):
        CandidateEvaluation(
            candidate_id="candidate-1",
            constraint_alignment=True,  # type: ignore[arg-type]
            evidence_readiness=4,
            uncertainty_exposure=4,
            risk_exposure=4,
            dependency_burden=4,
            directness=4,
            aggregate_score=24,
            strengths=(),
            limitations=(),
        )


def test_evaluation_record_rejects_incorrect_aggregate() -> None:
    with pytest.raises(ValueError, match="aggregate_score"):
        CandidateEvaluation(
            candidate_id="candidate-1",
            constraint_alignment=4,
            evidence_readiness=4,
            uncertainty_exposure=4,
            risk_exposure=4,
            dependency_burden=4,
            directness=4,
            aggregate_score=0,
            strengths=(),
            limitations=(),
        )


def test_evaluation_is_deterministic() -> None:
    evaluator = CandidateEvaluator()
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )
    candidates = make_candidates(request)

    first = evaluator.evaluate(request, candidates)
    second = evaluator.evaluate(request, candidates)

    assert first == second


def test_evaluator_does_not_mutate_request_or_candidates() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )
    candidates = make_candidates(request)

    request_before = request.to_dict()
    candidate_before = tuple(candidate.to_dict() for candidate in candidates)

    CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    assert request.to_dict() == request_before
    assert tuple(candidate.to_dict() for candidate in candidates) == candidate_before


def test_evaluation_record_is_immutable() -> None:
    request = make_request()
    evaluation = CandidateEvaluator().evaluate(
        request,
        make_candidates(request, count=2),
    )[0]

    with pytest.raises((FrozenInstanceError, AttributeError)):
        evaluation.aggregate_score = 0  # type: ignore[misc]


def test_serialization_is_deterministic() -> None:
    request = make_request()
    evaluation = CandidateEvaluator().evaluate(
        request,
        make_candidates(request, count=2),
    )[0]

    assert evaluation.to_dict() == evaluation.to_dict()


def test_no_pressure_gives_full_context_scores() -> None:
    request = make_request()
    evaluations = CandidateEvaluator().evaluate(
        request,
        make_candidates(request),
    )

    assert all(evaluation.constraint_alignment == 4 for evaluation in evaluations)
    assert all(evaluation.evidence_readiness == 4 for evaluation in evaluations)
    assert all(evaluation.uncertainty_exposure == 4 for evaluation in evaluations)
    assert all(evaluation.risk_exposure == 4 for evaluation in evaluations)


def test_constraint_first_has_strongest_constraint_alignment() -> None:
    request = make_request(
        constraints=("limited capacity",),
    )
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    by_label = {
        candidate.label: evaluation
        for candidate, evaluation in zip(
            candidates,
            evaluations,
            strict=True,
        )
    }

    assert by_label["Constraint-First"].constraint_alignment == 4


def test_evidence_first_has_strongest_uncertainty_handling() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
    )
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    by_label = {
        candidate.label: evaluation
        for candidate, evaluation in zip(
            candidates,
            evaluations,
            strict=True,
        )
    }

    assert by_label["Evidence-First"].evidence_readiness == 4
    assert by_label["Evidence-First"].uncertainty_exposure == 4


def test_risk_first_has_strongest_risk_handling() -> None:
    request = make_request(
        risk_signals=("reversal cost",),
    )
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    by_label = {
        candidate.label: evaluation
        for candidate, evaluation in zip(
            candidates,
            evaluations,
            strict=True,
        )
    }

    assert by_label["Risk-First"].risk_exposure == 4


def test_dependency_first_has_strongest_dependency_score() -> None:
    request = make_request()
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    by_label = {
        candidate.label: evaluation
        for candidate, evaluation in zip(
            candidates,
            evaluations,
            strict=True,
        )
    }

    assert by_label["Dependency-First"].dependency_burden == 4


def test_direct_outcome_has_strongest_directness() -> None:
    request = make_request()
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    by_label = {
        candidate.label: evaluation
        for candidate, evaluation in zip(
            candidates,
            evaluations,
            strict=True,
        )
    }

    assert by_label["Direct-Outcome"].directness == 4


def test_strengths_are_scores_three_or_four() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    dimension_map = {
        "constraint alignment": "constraint_alignment",
        "evidence readiness": "evidence_readiness",
        "uncertainty exposure": "uncertainty_exposure",
        "risk exposure": "risk_exposure",
        "dependency burden": "dependency_burden",
        "directness": "directness",
    }

    for evaluation in evaluations:
        for strength in evaluation.strengths:
            assert getattr(evaluation, dimension_map[strength]) >= 3


def test_limitations_are_scores_zero_or_one() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    dimension_map = {
        "constraint alignment": "constraint_alignment",
        "evidence readiness": "evidence_readiness",
        "uncertainty exposure": "uncertainty_exposure",
        "risk exposure": "risk_exposure",
        "dependency burden": "dependency_burden",
        "directness": "directness",
    }

    for evaluation in evaluations:
        for limitation in evaluation.limitations:
            assert getattr(evaluation, dimension_map[limitation]) <= 1


def test_ties_are_preserved_without_selection() -> None:
    request = make_request()
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    aggregate_scores = [evaluation.aggregate_score for evaluation in evaluations]

    assert len(evaluations) == len(candidates)
    assert isinstance(aggregate_scores, list)


def test_evaluator_does_not_sort_by_aggregate_score() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("reversal cost",),
        constraints=("limited capacity",),
    )
    candidates = make_candidates(request)

    evaluations = CandidateEvaluator().evaluate(
        request,
        candidates,
    )

    assert [evaluation.candidate_id for evaluation in evaluations] == [
        candidate.candidate_id for candidate in candidates
    ]


def test_evaluation_has_no_selection_fields() -> None:
    request = make_request()
    evaluation = CandidateEvaluator().evaluate(
        request,
        make_candidates(request, count=2),
    )[0]

    serialized = evaluation.to_dict()

    forbidden_fields = {
        "rank",
        "ranking",
        "winner",
        "selected",
        "recommended",
        "recommendation",
        "approved",
        "authority",
        "execution_permission",
        "verdict",
    }

    assert forbidden_fields.isdisjoint(serialized)
