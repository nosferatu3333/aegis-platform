from __future__ import annotations

import pytest

from aegis_os.intent import (
    ClarificationEngine,
    ClarificationState,
    IntentAmbiguity,
)


def test_no_ambiguity_is_sufficient() -> None:
    result = ClarificationEngine().assess(())

    assert result.state is ClarificationState.SUFFICIENT
    assert result.blocking_ambiguities == ()
    assert result.questions == ()


def test_non_blocking_ambiguity_is_sufficient() -> None:
    ambiguity = IntentAmbiguity(
        code="PREFERENCE_CRITERIA_UNSPECIFIED",
        description="Preference criteria were not stated.",
        blocking=False,
    )

    result = ClarificationEngine().assess((ambiguity,))

    assert result.state is ClarificationState.SUFFICIENT
    assert result.questions == ()


def test_blocking_ambiguity_requires_clarification() -> None:
    ambiguity = IntentAmbiguity(
        code="UNRESOLVED_TARGET_REFERENCE",
        description="Target is unresolved.",
        blocking=True,
        question="What target should be used?",
    )

    result = ClarificationEngine().assess((ambiguity,))

    assert result.state is ClarificationState.CLARIFICATION_REQUIRED

    assert result.blocking_ambiguities == (ambiguity,)

    assert result.questions == ("What target should be used?",)


def test_questions_derive_only_from_blocking_ambiguities() -> None:
    non_blocking = IntentAmbiguity(
        code="NON_BLOCKING",
        description="Minor ambiguity.",
        blocking=False,
    )

    blocking = IntentAmbiguity(
        code="BLOCKING",
        description="Material ambiguity.",
        blocking=True,
        question="Please clarify the material ambiguity.",
    )

    result = ClarificationEngine().assess(
        (
            non_blocking,
            blocking,
        )
    )

    assert result.questions == ("Please clarify the material ambiguity.",)


def test_clarification_is_deterministic() -> None:
    ambiguities = (
        IntentAmbiguity(
            code="A",
            description="A blocking ambiguity.",
            blocking=True,
            question="Clarify A?",
        ),
        IntentAmbiguity(
            code="B",
            description="A non-blocking ambiguity.",
            blocking=False,
        ),
    )

    engine = ClarificationEngine()

    assert engine.assess(ambiguities) == engine.assess(ambiguities)


def test_assess_requires_tuple() -> None:
    with pytest.raises(TypeError, match="tuple"):
        ClarificationEngine().assess(
            [],  # type: ignore[arg-type]
        )
