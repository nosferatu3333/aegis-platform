from __future__ import annotations

from dataclasses import fields

import pytest

from aegis_os.intent import (
    IntentInterpreter,
    IntentRequest,
    OutcomeModel,
    OutcomeModeler,
)


def test_outcome_model_has_exact_six_dimensions() -> None:
    assert tuple(field.name for field in fields(OutcomeModel)) == (
        "intent_ref",
        "desired_state",
        "success_conditions",
        "explicit_constraints",
        "inferred_constraints",
        "outcome_uncertainties",
    )


def test_sufficient_intent_can_produce_outcome() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a one-page architecture proposal.",
            explicit_constraints=("one page",),
        )
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-001",
        success_conditions=("A one-page architecture proposal exists.",),
    )

    assert outcome.intent_ref == "intent-001"
    assert outcome.desired_state == "Create a one-page architecture proposal."
    assert outcome.success_conditions == ("A one-page architecture proposal exists.",)
    assert outcome.explicit_constraints == ("one page",)
    assert outcome.inferred_constraints == ()
    assert outcome.outcome_uncertainties == ()


def test_blocked_intent_cannot_produce_outcome() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Update it.",
        )
    )

    assert interpretation.clarification_required is True

    with pytest.raises(
        ValueError,
        match="CLARIFICATION_REQUIRED",
    ):
        OutcomeModeler().model(
            interpretation,
            intent_ref="intent-blocked",
        )


def test_explicit_constraints_are_preserved() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a proposal.",
            explicit_constraints=(
                "one page",
                "no external research",
            ),
        )
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-002",
    )

    assert outcome.explicit_constraints == (
        "one page",
        "no external research",
    )


def test_inferred_constraints_remain_separate() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a proposal.",
            explicit_constraints=("one page",),
        )
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-003",
        inferred_constraints=("preserve current architecture",),
    )

    assert outcome.explicit_constraints == ("one page",)
    assert outcome.inferred_constraints == ("preserve current architecture",)


def test_outcome_uncertainty_is_preserved() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a proposal.",
        )
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-004",
        outcome_uncertainties=("final audience not yet specified",),
    )

    assert outcome.outcome_uncertainties == ("final audience not yet specified",)


def test_success_conditions_are_not_fabricated() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a proposal.",
        )
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-005",
    )

    assert outcome.success_conditions == ()


def test_outcome_model_is_deterministic() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a proposal.",
            explicit_constraints=("one page",),
        )
    )

    modeler = OutcomeModeler()

    baseline = modeler.model(
        interpretation,
        intent_ref="intent-006",
        success_conditions=("Proposal exists.",),
        inferred_constraints=("preserve current architecture",),
        outcome_uncertainties=("audience unresolved",),
    )

    for _ in range(100):
        observed = modeler.model(
            interpretation,
            intent_ref="intent-006",
            success_conditions=("Proposal exists.",),
            inferred_constraints=("preserve current architecture",),
            outcome_uncertainties=("audience unresolved",),
        )

        assert observed == baseline
        assert observed.to_dict() == baseline.to_dict()


def test_outcome_model_does_not_mutate_interpretation() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a proposal.",
            explicit_constraints=("one page",),
        )
    )

    before = interpretation.to_dict()

    OutcomeModeler().model(
        interpretation,
        intent_ref="intent-007",
    )

    assert interpretation.to_dict() == before


def test_outcome_serialization_exposes_no_downstream_authority() -> None:
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Deploy the accepted release.",
        )
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-008",
    )

    payload = outcome.to_dict()

    forbidden = {
        "plan",
        "plan_steps",
        "project_state",
        "reasoning_mode",
        "candidate_paths",
        "authority",
        "approval",
        "execution_permission",
        "governed_verdict",
        "tool",
        "confidence",
        "probability",
    }

    assert forbidden.isdisjoint(payload)
