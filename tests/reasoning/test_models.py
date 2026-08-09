from __future__ import annotations

import json
from dataclasses import fields

import pytest

from aegis_os.reasoning import ReasoningMode, ReasoningRequest, ReasoningResult


def make_request(**overrides: object) -> ReasoningRequest:
    values: dict[str, object] = {
        "reasoning_request_id": "reason-001",
        "intent_ref": "intent-001",
        "outcome_ref": "outcome-001",
        "project_context_ref": "project-001",
        "uncertainty_signals": ("market uncertainty",),
        "risk_signals": ("reversible decision",),
        "constraints": ("bounded scope",),
        "requested_depth": 2,
        "budget": 3,
    }
    values.update(overrides)
    return ReasoningRequest(**values)  # type: ignore[arg-type]


def make_result(**overrides: object) -> ReasoningResult:
    values: dict[str, object] = {
        "reasoning_request_id": "reason-001",
        "mode": ReasoningMode.BRANCH,
        "summary": "Multiple viable approaches require bounded comparison.",
        "selection_reason": "Material uncertainty exists across alternatives.",
        "uncertainty_signals": ("approach fit",),
        "evidence_requirements": ("comparison evidence",),
        "alternatives_preserved": ("alternative-b",),
        "complete": False,
    }
    values.update(overrides)
    return ReasoningResult(**values)  # type: ignore[arg-type]


def test_reasoning_modes_are_exact_and_stable() -> None:
    assert [mode.value for mode in ReasoningMode] == [
        "DIRECT",
        "VERIFY",
        "BRANCH",
        "SEARCH",
    ]


def test_reasoning_request_serializes_deterministically() -> None:
    request = make_request()

    expected = {
        "schema_version": "1.0",
        "reasoning_request_id": "reason-001",
        "intent_ref": "intent-001",
        "outcome_ref": "outcome-001",
        "project_context_ref": "project-001",
        "uncertainty_signals": ["market uncertainty"],
        "risk_signals": ["reversible decision"],
        "constraints": ["bounded scope"],
        "requested_depth": 2,
        "budget": 3,
    }

    assert request.to_dict() == expected
    assert json.loads(json.dumps(request.to_dict(), sort_keys=True)) == expected


def test_reasoning_result_serializes_mode_as_public_value() -> None:
    result = make_result()

    serialized = result.to_dict()

    assert serialized["schema_version"] == "1.0"
    assert serialized["mode"] == "BRANCH"
    assert serialized["complete"] is False
    assert serialized["alternatives_preserved"] == ["alternative-b"]


def test_request_rejects_blank_identifiers() -> None:
    with pytest.raises(ValueError, match="reasoning_request_id"):
        make_request(reasoning_request_id="  ")


def test_request_rejects_invalid_depth_or_budget() -> None:
    with pytest.raises(ValueError, match="requested_depth"):
        make_request(requested_depth=-1)

    with pytest.raises(ValueError, match="budget"):
        make_request(budget=0)


def test_request_rejects_boolean_numeric_values() -> None:
    with pytest.raises(TypeError, match="requested_depth"):
        make_request(requested_depth=True)

    with pytest.raises(TypeError, match="budget"):
        make_request(budget=False)


def test_request_normalizes_signal_whitespace_without_reordering() -> None:
    request = make_request(
        uncertainty_signals=("  first  ", "second"),
        risk_signals=(" risk-a ", "risk-b"),
        constraints=(" constraint-a ",),
    )

    assert request.uncertainty_signals == ("first", "second")
    assert request.risk_signals == ("risk-a", "risk-b")
    assert request.constraints == ("constraint-a",)


def test_result_requires_reasoning_mode_contract() -> None:
    with pytest.raises(TypeError, match="ReasoningMode"):
        make_result(mode="BRANCH")


def test_result_normalizes_safe_summary_collections() -> None:
    result = make_result(
        uncertainty_signals=(" one ",),
        evidence_requirements=(" evidence-a ",),
        alternatives_preserved=(" alternative-a ",),
    )

    assert result.uncertainty_signals == ("one",)
    assert result.evidence_requirements == ("evidence-a",)
    assert result.alternatives_preserved == ("alternative-a",)


def test_contract_models_do_not_carry_authority_or_execution_fields() -> None:
    prohibited = {
        "authority",
        "authority_grant",
        "approval",
        "execution",
        "execution_permission",
        "execute",
        "tool_invocation",
    }

    request_fields = {item.name for item in fields(ReasoningRequest)}
    result_fields = {item.name for item in fields(ReasoningResult)}

    assert prohibited.isdisjoint(request_fields)
    assert prohibited.isdisjoint(result_fields)


def test_reasoning_result_cannot_imply_authority_through_serialization() -> None:
    serialized_keys = set(make_result().to_dict())

    assert "authority" not in serialized_keys
    assert "approval" not in serialized_keys
    assert "execution_permission" not in serialized_keys
    assert "execute" not in serialized_keys


def test_contracts_are_immutable() -> None:
    request = make_request()

    with pytest.raises((AttributeError, TypeError)):
        request.budget = 99  # type: ignore[misc]
