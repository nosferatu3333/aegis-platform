"""Bounded contracts for AEGIS adaptive reasoning.

This module defines data contracts only.

It deliberately does not implement:
- escalation policy,
- candidate generation,
- candidate evaluation,
- convergence,
- authority,
- execution,
- persistent memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar


class ReasoningMode(str, Enum):
    """Minimum sufficient cognitive-effort modes."""

    DIRECT = "DIRECT"
    VERIFY = "VERIFY"
    BRANCH = "BRANCH"
    SEARCH = "SEARCH"


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _normalize_strings(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized: list[str] = []

    for value in values:
        _require_non_empty(value, field_name)
        normalized.append(value.strip())

    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    """Bounded input presented to the reasoning-control layer.

    The request describes cognitive work only.  It carries no authority grant
    and conveys no execution permission.
    """

    schema_version: ClassVar[str] = "1.0"

    reasoning_request_id: str
    intent_ref: str
    outcome_ref: str
    project_context_ref: str
    uncertainty_signals: tuple[str, ...] = field(default_factory=tuple)
    risk_signals: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[str, ...] = field(default_factory=tuple)
    requested_depth: int = 1
    budget: int = 1

    def __post_init__(self) -> None:
        _require_non_empty(self.reasoning_request_id, "reasoning_request_id")
        _require_non_empty(self.intent_ref, "intent_ref")
        _require_non_empty(self.outcome_ref, "outcome_ref")
        _require_non_empty(self.project_context_ref, "project_context_ref")

        if isinstance(self.requested_depth, bool) or not isinstance(
            self.requested_depth, int
        ):
            raise TypeError("requested_depth must be an integer")

        if self.requested_depth < 0:
            raise ValueError("requested_depth must be greater than or equal to 0")

        if isinstance(self.budget, bool) or not isinstance(self.budget, int):
            raise TypeError("budget must be an integer")

        if self.budget < 1:
            raise ValueError("budget must be greater than or equal to 1")

        object.__setattr__(
            self,
            "uncertainty_signals",
            _normalize_strings(self.uncertainty_signals, "uncertainty_signals"),
        )
        object.__setattr__(
            self,
            "risk_signals",
            _normalize_strings(self.risk_signals, "risk_signals"),
        )
        object.__setattr__(
            self,
            "constraints",
            _normalize_strings(self.constraints, "constraints"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serialization-safe representation."""

        return {
            "schema_version": self.schema_version,
            "reasoning_request_id": self.reasoning_request_id,
            "intent_ref": self.intent_ref,
            "outcome_ref": self.outcome_ref,
            "project_context_ref": self.project_context_ref,
            "uncertainty_signals": list(self.uncertainty_signals),
            "risk_signals": list(self.risk_signals),
            "constraints": list(self.constraints),
            "requested_depth": self.requested_depth,
            "budget": self.budget,
        }


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    """Bounded result emitted by reasoning control.

    A result may describe cognitive mode, rationale, uncertainty, and evidence
    requirements.  It is not an authority decision and cannot authorize
    execution.
    """

    schema_version: ClassVar[str] = "1.0"

    reasoning_request_id: str
    mode: ReasoningMode
    summary: str
    selection_reason: str
    uncertainty_signals: tuple[str, ...] = field(default_factory=tuple)
    evidence_requirements: tuple[str, ...] = field(default_factory=tuple)
    alternatives_preserved: tuple[str, ...] = field(default_factory=tuple)
    complete: bool = False

    def __post_init__(self) -> None:
        _require_non_empty(self.reasoning_request_id, "reasoning_request_id")

        if not isinstance(self.mode, ReasoningMode):
            raise TypeError("mode must be a ReasoningMode")

        _require_non_empty(self.summary, "summary")
        _require_non_empty(self.selection_reason, "selection_reason")

        if not isinstance(self.complete, bool):
            raise TypeError("complete must be a bool")

        object.__setattr__(
            self,
            "uncertainty_signals",
            _normalize_strings(self.uncertainty_signals, "uncertainty_signals"),
        )
        object.__setattr__(
            self,
            "evidence_requirements",
            _normalize_strings(self.evidence_requirements, "evidence_requirements"),
        )
        object.__setattr__(
            self,
            "alternatives_preserved",
            _normalize_strings(self.alternatives_preserved, "alternatives_preserved"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serialization-safe representation."""

        return {
            "schema_version": self.schema_version,
            "reasoning_request_id": self.reasoning_request_id,
            "mode": self.mode.value,
            "summary": self.summary,
            "selection_reason": self.selection_reason,
            "uncertainty_signals": list(self.uncertainty_signals),
            "evidence_requirements": list(self.evidence_requirements),
            "alternatives_preserved": list(self.alternatives_preserved),
            "complete": self.complete,
        }
