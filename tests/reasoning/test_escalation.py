from __future__ import annotations

import pytest

from aegis_os.reasoning import (
    AdaptiveEscalationPolicy,
    EscalationDecision,
    ReasoningMode,
    ReasoningRequest,
)


def make_request(
    *,
    uncertainty_signals: tuple[str, ...] = (),
    risk_signals: tuple[str, ...] = (),
    constraints: tuple[str, ...] = (),
    requested_depth: int = 1,
    budget: int = 1,
) -> ReasoningRequest:
    return ReasoningRequest(
        reasoning_request_id="reason-002",
        intent_ref="intent-002",
        outcome_ref="outcome-002",
        project_context_ref="project-002",
        uncertainty_signals=uncertainty_signals,
        risk_signals=risk_signals,
        constraints=constraints,
        requested_depth=requested_depth,
        budget=budget,
    )


def test_policy_rejects_non_reasoning_request() -> None:
    policy = AdaptiveEscalationPolicy()

    with pytest.raises(TypeError, match="ReasoningRequest"):
        policy.select_mode("invalid")  # type: ignore[arg-type]


def test_empty_bounded_request_selects_direct() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(make_request())

    assert decision.mode is ReasoningMode.DIRECT
    assert isinstance(decision, EscalationDecision)


def test_single_uncertainty_signal_selects_verify() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            uncertainty_signals=("source confidence unclear",),
        )
    )

    assert decision.mode is ReasoningMode.VERIFY


def test_single_risk_signal_selects_verify() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            risk_signals=("bounded operational risk",),
        )
    )

    assert decision.mode is ReasoningMode.VERIFY


def test_multiple_uncertainties_with_depth_and_budget_select_branch() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            uncertainty_signals=(
                "objective ambiguity",
                "implementation ambiguity",
            ),
            requested_depth=2,
            budget=2,
        )
    )

    assert decision.mode is ReasoningMode.BRANCH


def test_multiple_constraints_with_depth_and_budget_select_branch() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            constraints=(
                "limited time",
                "limited implementation capacity",
            ),
            requested_depth=2,
            budget=2,
        )
    )

    assert decision.mode is ReasoningMode.BRANCH


@pytest.mark.parametrize(
    "signal",
    (
        "multiple approaches should be considered",
        "competing options exist",
        "significant tradeoff between speed and quality",
        "ambiguous objective",
        "cross-domain coordination required",
    ),
)
def test_branch_markers_select_branch(signal: str) -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            uncertainty_signals=(signal,),
            budget=2,
        )
    )

    assert decision.mode is ReasoningMode.BRANCH


@pytest.mark.parametrize(
    "signal",
    (
        "external evidence required",
        "external source required",
        "current information required",
        "current data required",
        "web research required",
        "research required before recommendation",
        "source verification required",
    ),
)
def test_search_markers_with_budget_select_search(signal: str) -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            uncertainty_signals=(signal,),
            budget=3,
        )
    )

    assert decision.mode is ReasoningMode.SEARCH


def test_search_marker_without_search_budget_does_not_select_search() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            uncertainty_signals=("external evidence required",),
            budget=1,
        )
    )

    assert decision.mode is ReasoningMode.VERIFY


def test_search_has_precedence_over_branch() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            uncertainty_signals=(
                "external evidence required",
                "multiple approaches should be considered",
            ),
            requested_depth=2,
            budget=3,
        )
    )

    assert decision.mode is ReasoningMode.SEARCH


def test_branch_has_precedence_over_verify() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            uncertainty_signals=(
                "objective ambiguity",
                "implementation ambiguity",
            ),
            risk_signals=("bounded risk",),
            requested_depth=2,
            budget=2,
        )
    )

    assert decision.mode is ReasoningMode.BRANCH


def test_depth_alone_does_not_force_branch() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            requested_depth=4,
            budget=4,
        )
    )

    assert decision.mode is ReasoningMode.DIRECT


def test_budget_alone_does_not_force_escalation() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            budget=10,
        )
    )

    assert decision.mode is ReasoningMode.DIRECT


def test_constraint_alone_does_not_imply_risk() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(
        make_request(
            constraints=("must remain non-executing",),
        )
    )

    assert decision.mode is ReasoningMode.DIRECT


def test_policy_is_deterministic() -> None:
    policy = AdaptiveEscalationPolicy()
    request = make_request(
        uncertainty_signals=(
            "objective ambiguity",
            "implementation ambiguity",
        ),
        requested_depth=2,
        budget=2,
    )

    first = policy.select_mode(request)
    second = policy.select_mode(request)

    assert first == second


def test_decision_reason_is_non_empty() -> None:
    decision = AdaptiveEscalationPolicy().select_mode(make_request())

    assert decision.reason.strip()


def test_policy_does_not_mutate_request() -> None:
    request = make_request(
        uncertainty_signals=("uncertain source",),
        risk_signals=("bounded risk",),
        constraints=("no execution",),
        budget=2,
    )

    before = request.to_dict()

    AdaptiveEscalationPolicy().select_mode(request)

    assert request.to_dict() == before
