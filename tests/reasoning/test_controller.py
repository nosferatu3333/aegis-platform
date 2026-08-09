from __future__ import annotations

from abc import ABC

import pytest

from aegis_os.reasoning import (
    ReasoningController,
    ReasoningMode,
    ReasoningRequest,
    StaticReasoningController,
)


def make_request() -> ReasoningRequest:
    return ReasoningRequest(
        reasoning_request_id="reason-001",
        intent_ref="intent-001",
        outcome_ref="outcome-001",
        project_context_ref="project-001",
        uncertainty_signals=("objective ambiguity",),
        risk_signals=("bounded risk",),
        constraints=("no execution",),
        requested_depth=1,
        budget=2,
    )


def test_reasoning_controller_is_abstract_contract() -> None:
    assert issubclass(ReasoningController, ABC)

    with pytest.raises(TypeError):
        ReasoningController()  # type: ignore[abstract]


def test_static_controller_defaults_to_direct() -> None:
    controller = StaticReasoningController()

    result = controller.reason(make_request())

    assert result.mode is ReasoningMode.DIRECT
    assert result.complete is True
    assert result.reasoning_request_id == "reason-001"


def test_static_controller_can_represent_any_contract_mode() -> None:
    for mode in ReasoningMode:
        controller = StaticReasoningController(
            mode=mode,
            selection_reason=f"Explicit {mode.value} test mode.",
        )

        result = controller.reason(make_request())

        assert result.mode is mode
        assert result.selection_reason == f"Explicit {mode.value} test mode."


def test_controller_preserves_request_uncertainty() -> None:
    request = make_request()

    result = StaticReasoningController().reason(request)

    assert result.uncertainty_signals == request.uncertainty_signals


def test_controller_does_not_invent_evidence_or_alternatives() -> None:
    result = StaticReasoningController().reason(make_request())

    assert result.evidence_requirements == ()
    assert result.alternatives_preserved == ()


def test_controller_rejects_non_request_input() -> None:
    controller = StaticReasoningController()

    with pytest.raises(TypeError, match="ReasoningRequest"):
        controller.reason("not-a-request")  # type: ignore[arg-type]


def test_controller_requires_reasoning_mode() -> None:
    with pytest.raises(TypeError, match="ReasoningMode"):
        StaticReasoningController(mode="DIRECT")  # type: ignore[arg-type]


def test_controller_requires_selection_reason() -> None:
    with pytest.raises(ValueError, match="selection_reason"):
        StaticReasoningController(selection_reason="   ")


def test_controller_result_contains_no_authority_or_execution_keys() -> None:
    serialized = StaticReasoningController().reason(make_request()).to_dict()

    prohibited = {
        "authority",
        "authority_grant",
        "approval",
        "execution",
        "execution_permission",
        "execute",
        "tool_invocation",
    }

    assert prohibited.isdisjoint(serialized)


def test_static_controller_is_not_adaptive_policy() -> None:
    request = ReasoningRequest(
        reasoning_request_id="reason-complex",
        intent_ref="intent-complex",
        outcome_ref="outcome-complex",
        project_context_ref="project-complex",
        uncertainty_signals=("high uncertainty", "conflicting evidence"),
        risk_signals=("high consequence",),
        constraints=("multiple domains",),
        requested_depth=10,
        budget=10,
    )

    controller = StaticReasoningController(mode=ReasoningMode.DIRECT)

    result = controller.reason(request)

    # WO-REASON-001 proves the interface only.
    # Adaptive selection belongs to WO-REASON-002.
    assert result.mode is ReasoningMode.DIRECT
