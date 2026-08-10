from __future__ import annotations

from dataclasses import fields

import pytest

from aegis_os.intent import (
    IntentInterpretation,
    IntentInterpreter,
    IntentRequest,
    IntentType,
)


@pytest.mark.parametrize(
    ("raw_request", "expected"),
    (
        (
            "Explain how the runtime works.",
            IntentType.UNDERSTAND,
        ),
        (
            "Which option should I choose?",
            IntentType.DECIDE,
        ),
        (
            "Create a technical specification.",
            IntentType.CREATE,
        ),
        (
            "Update the architecture document.",
            IntentType.CHANGE,
        ),
        (
            "Review this design.",
            IntentType.EVALUATE,
        ),
        (
            "Plan the next implementation phase.",
            IntentType.PLAN,
        ),
        (
            "Deploy the accepted release.",
            IntentType.EXECUTE_REQUEST,
        ),
    ),
)
def test_initial_intent_taxonomy(
    raw_request: str,
    expected: IntentType,
) -> None:
    request = IntentRequest(
        raw_request=raw_request,
        context_refs=("current-artifact",),
    )

    result = IntentInterpreter().interpret(request)

    assert result.intent_type is expected


def test_interpretation_has_exact_frozen_dimensions() -> None:
    assert tuple(field.name for field in fields(IntentInterpretation)) == (
        "raw_request",
        "interpreted_intent",
        "intent_type",
        "explicit_constraints",
        "inferred_constraints",
        "ambiguities",
        "clarification_required",
        "clarification_questions",
    )


def test_raw_request_is_preserved() -> None:
    request = IntentRequest(
        raw_request="  Explain   this system.  ",
        context_refs=("system",),
    )

    result = IntentInterpreter().interpret(request)

    assert result.raw_request == request.raw_request
    assert result.interpreted_intent == "Explain this system."


def test_explicit_constraints_are_preserved() -> None:
    request = IntentRequest(
        raw_request="Create a proposal.",
        explicit_constraints=(
            "one page",
            "no external research",
        ),
    )

    result = IntentInterpreter().interpret(request)

    assert result.explicit_constraints == (
        "one page",
        "no external research",
    )


def test_inferred_constraints_are_not_fabricated() -> None:
    result = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a proposal.",
        )
    )

    assert result.inferred_constraints == ()


def test_unresolved_placeholder_blocks() -> None:
    result = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create the report for <target>.",
        )
    )

    assert result.clarification_required is True

    assert tuple(ambiguity.code for ambiguity in result.ambiguities) == (
        "UNRESOLVED_PLACEHOLDER",
    )

    assert result.clarification_questions


def test_unresolved_target_reference_blocks_change() -> None:
    result = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Update it.",
        )
    )

    assert result.intent_type is IntentType.CHANGE
    assert result.clarification_required is True

    assert "UNRESOLVED_TARGET_REFERENCE" in {
        ambiguity.code for ambiguity in result.ambiguities
    }


def test_context_reference_resolves_deictic_target_gate() -> None:
    result = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Update it.",
            context_refs=("document-123",),
        )
    )

    assert result.intent_type is IntentType.CHANGE
    assert result.clarification_required is False


def test_best_without_criteria_is_non_blocking() -> None:
    result = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Which is the best option?",
        )
    )

    assert result.intent_type is IntentType.DECIDE
    assert result.clarification_required is False

    assert tuple(ambiguity.code for ambiguity in result.ambiguities) == (
        "PREFERENCE_CRITERIA_UNSPECIFIED",
    )

    assert result.clarification_questions == ()


def test_best_with_explicit_constraint_has_no_preference_ambiguity() -> None:
    result = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Which is the best option?",
            explicit_constraints=("lowest implementation risk",),
        )
    )

    assert result.clarification_required is False

    assert "PREFERENCE_CRITERIA_UNSPECIFIED" not in {
        ambiguity.code for ambiguity in result.ambiguities
    }


def test_execute_request_does_not_expose_authority() -> None:
    result = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Deploy the accepted release.",
        )
    )

    serialized = result.to_dict()

    assert result.intent_type is IntentType.EXECUTE_REQUEST

    forbidden = {
        "authority",
        "approved",
        "approval",
        "execution_permission",
        "governed_verdict",
        "verdict",
        "execute",
        "tool",
        "confidence",
        "probability",
    }

    assert forbidden.isdisjoint(serialized)


def test_interpreter_is_deterministic() -> None:
    request = IntentRequest(
        raw_request="Plan the next implementation phase.",
        explicit_constraints=("preserve current reasoning contracts",),
    )

    interpreter = IntentInterpreter()

    first = interpreter.interpret(request)

    for _ in range(100):
        assert interpreter.interpret(request) == first
        assert interpreter.interpret(request).to_dict() == first.to_dict()


def test_interpreter_does_not_mutate_request() -> None:
    request = IntentRequest(
        raw_request="Review this design.",
        context_refs=("design-001",),
        explicit_constraints=("architecture only",),
    )

    before = request.to_dict()

    IntentInterpreter().interpret(request)

    assert request.to_dict() == before


def test_request_rejects_empty_raw_request() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        IntentRequest(
            raw_request="   ",
        )


def test_interpreter_requires_intent_request() -> None:
    with pytest.raises(TypeError, match="IntentRequest"):
        IntentInterpreter().interpret(
            "invalid",  # type: ignore[arg-type]
        )
