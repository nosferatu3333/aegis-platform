from __future__ import annotations

import pytest

from aegis_os.reasoning import (
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
        reasoning_request_id="reason-003",
        intent_ref="intent-003",
        outcome_ref="outcome-003",
        project_context_ref="project-003",
        uncertainty_signals=uncertainty_signals,
        risk_signals=risk_signals,
        constraints=constraints,
        requested_depth=2,
        budget=3,
    )


def test_generator_rejects_non_reasoning_request() -> None:
    generator = CandidatePathGenerator()

    with pytest.raises(TypeError, match="ReasoningRequest"):
        generator.generate(
            "invalid",  # type: ignore[arg-type]
            mode=ReasoningMode.BRANCH,
        )


def test_generator_requires_branch_mode() -> None:
    generator = CandidatePathGenerator()

    with pytest.raises(ValueError, match="BRANCH"):
        generator.generate(
            make_request(),
            mode=ReasoningMode.DIRECT,
        )


def test_default_candidate_count_is_three() -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(),
        mode=ReasoningMode.BRANCH,
    )

    assert len(candidates) == 3


@pytest.mark.parametrize("count", (2, 3, 4, 5))
def test_supported_candidate_counts(count: int) -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(),
        mode=ReasoningMode.BRANCH,
        candidate_count=count,
    )

    assert len(candidates) == count


@pytest.mark.parametrize("count", (0, 1, 6, 99))
def test_out_of_range_candidate_count_is_rejected(count: int) -> None:
    with pytest.raises(ValueError, match="candidate_count"):
        CandidatePathGenerator().generate(
            make_request(),
            mode=ReasoningMode.BRANCH,
            candidate_count=count,
        )


def test_boolean_candidate_count_is_rejected() -> None:
    with pytest.raises(TypeError, match="candidate_count"):
        CandidatePathGenerator().generate(
            make_request(),
            mode=ReasoningMode.BRANCH,
            candidate_count=True,
        )


def test_candidates_are_candidate_path_instances() -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(),
        mode=ReasoningMode.BRANCH,
    )

    assert all(isinstance(candidate, CandidatePath) for candidate in candidates)


def test_candidates_preserve_intent_and_outcome_refs() -> None:
    request = make_request()

    candidates = CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
    )

    assert {candidate.intent_ref for candidate in candidates} == {request.intent_ref}
    assert {candidate.outcome_ref for candidate in candidates} == {request.outcome_ref}


def test_candidate_ids_are_unique() -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(),
        mode=ReasoningMode.BRANCH,
        candidate_count=5,
    )

    candidate_ids = {candidate.candidate_id for candidate in candidates}

    assert len(candidate_ids) == 5


def test_candidate_paths_are_materially_distinct() -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(),
        mode=ReasoningMode.BRANCH,
        candidate_count=5,
    )

    signatures = {
        (
            candidate.label,
            candidate.summary,
            candidate.primary_objective,
        )
        for candidate in candidates
    }

    assert len(signatures) == 5


def test_constraints_are_preserved_on_all_candidates() -> None:
    request = make_request(
        constraints=(
            "limited time",
            "no execution authority",
        )
    )

    candidates = CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
    )

    assert all(
        candidate.constraints_acknowledged == request.constraints
        for candidate in candidates
    )


def test_uncertainty_is_preserved_on_all_candidates() -> None:
    request = make_request(
        uncertainty_signals=(
            "market demand unclear",
            "implementation cost unclear",
        )
    )

    candidates = CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
    )

    assert all(
        candidate.known_uncertainty == request.uncertainty_signals
        for candidate in candidates
    )


def test_constraint_first_path_is_prioritized_when_constraints_exist() -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(constraints=("limited capacity",)),
        mode=ReasoningMode.BRANCH,
    )

    assert candidates[0].label == "Constraint-First"


def test_evidence_first_path_is_prioritized_when_uncertainty_exists() -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(uncertainty_signals=("source unclear",)),
        mode=ReasoningMode.BRANCH,
    )

    assert candidates[0].label == "Evidence-First"


def test_risk_first_path_is_prioritized_when_risk_exists() -> None:
    candidates = CandidatePathGenerator().generate(
        make_request(risk_signals=("high reversal cost",)),
        mode=ReasoningMode.BRANCH,
    )

    assert candidates[0].label == "Risk-First"


def test_signal_priority_order_is_deterministic() -> None:
    request = make_request(
        uncertainty_signals=("source unclear",),
        risk_signals=("bounded risk",),
        constraints=("limited capacity",),
    )

    candidates = CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
        candidate_count=5,
    )

    assert [candidate.label for candidate in candidates] == [
        "Constraint-First",
        "Evidence-First",
        "Risk-First",
        "Direct-Outcome",
        "Dependency-First",
    ]


def test_evidence_first_path_surfaces_uncertainty_as_evidence_need() -> None:
    request = make_request(
        uncertainty_signals=("current source quality unclear",),
    )

    candidates = CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
    )

    evidence_candidate = next(
        candidate for candidate in candidates if candidate.label == "Evidence-First"
    )

    assert evidence_candidate.evidence_needs == request.uncertainty_signals


def test_risk_first_path_surfaces_risk_as_evidence_need() -> None:
    request = make_request(
        risk_signals=("reversal cost unknown",),
    )

    candidates = CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
    )

    risk_candidate = next(
        candidate for candidate in candidates if candidate.label == "Risk-First"
    )

    assert risk_candidate.evidence_needs == request.risk_signals


def test_generation_is_deterministic() -> None:
    generator = CandidatePathGenerator()
    request = make_request(
        uncertainty_signals=("uncertain source",),
        risk_signals=("bounded risk",),
        constraints=("limited capacity",),
    )

    first = generator.generate(
        request,
        mode=ReasoningMode.BRANCH,
        candidate_count=5,
    )
    second = generator.generate(
        request,
        mode=ReasoningMode.BRANCH,
        candidate_count=5,
    )

    assert first == second


def test_generator_does_not_mutate_request() -> None:
    request = make_request(
        uncertainty_signals=("uncertain source",),
        risk_signals=("bounded risk",),
        constraints=("limited capacity",),
    )

    before = request.to_dict()

    CandidatePathGenerator().generate(
        request,
        mode=ReasoningMode.BRANCH,
    )

    assert request.to_dict() == before


def test_candidate_serialization_is_deterministic() -> None:
    candidate = CandidatePathGenerator().generate(
        make_request(),
        mode=ReasoningMode.BRANCH,
        candidate_count=2,
    )[0]

    assert candidate.to_dict() == candidate.to_dict()


def test_candidate_is_immutable() -> None:
    candidate = CandidatePathGenerator().generate(
        make_request(),
        mode=ReasoningMode.BRANCH,
        candidate_count=2,
    )[0]

    with pytest.raises(AttributeError):
        candidate.label = "Changed"  # type: ignore[misc]
