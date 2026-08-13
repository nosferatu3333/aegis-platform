"""Immutable contracts for one bounded SYSTEM cognitive cycle."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aegis_os.intent import IntentInterpretation, IntentRequest, OutcomeModel
from aegis_os.project import ProjectState
from aegis_os.reasoning import AdaptiveCycleResult, ReasoningRequest


def _require_non_empty_string(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{name} must be a non-empty string")


def _require_string_tuple(value: object, name: str) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be a tuple")

    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise TypeError(f"{name} must contain non-empty strings")


class ProjectContextMode(str, Enum):
    """Explicit routing mode for project context."""

    TRANSIENT = "TRANSIENT"
    CREATE_NEW = "CREATE_NEW"
    EXISTING = "EXISTING"


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """Explicit project context supplied to a cognitive cycle."""

    mode: ProjectContextMode
    new_project_id: str | None = None
    existing_state: ProjectState | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ProjectContextMode):
            raise TypeError("mode must be a ProjectContextMode")

        if self.new_project_id is not None and not isinstance(self.new_project_id, str):
            raise TypeError("new_project_id must be a string or None")

        if self.existing_state is not None and not isinstance(
            self.existing_state, ProjectState
        ):
            raise TypeError("existing_state must be a ProjectState or None")

        if self.mode is ProjectContextMode.TRANSIENT:
            if self.new_project_id is not None or self.existing_state is not None:
                raise ValueError("TRANSIENT cannot contain project state inputs")
            return

        if self.mode is ProjectContextMode.CREATE_NEW:
            if self.new_project_id is None or not self.new_project_id.strip():
                raise ValueError("CREATE_NEW requires a non-empty new_project_id")
            if self.existing_state is not None:
                raise ValueError("CREATE_NEW cannot contain existing_state")
            return

        if self.new_project_id is not None:
            raise ValueError("EXISTING cannot contain new_project_id")
        if self.existing_state is None:
            raise ValueError("EXISTING requires existing_state")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "mode": self.mode.value,
            "new_project_id": self.new_project_id,
            "existing_state": (
                self.existing_state.to_dict()
                if self.existing_state is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class CognitiveCycleRequest:
    """Bounded input for one explicit synchronous cognitive cycle."""

    cycle_id: str
    reasoning_request_id: str
    intent_ref: str
    intent_request: IntentRequest
    project_context: ProjectContext
    success_conditions: tuple[str, ...] = ()
    outcome_uncertainties: tuple[str, ...] = ()
    risk_signals: tuple[str, ...] = ()
    requested_depth: int = 1
    budget: int = 1

    def __post_init__(self) -> None:
        for name, value in (
            ("cycle_id", self.cycle_id),
            ("reasoning_request_id", self.reasoning_request_id),
            ("intent_ref", self.intent_ref),
        ):
            _require_non_empty_string(value, name)

        if not isinstance(self.intent_request, IntentRequest):
            raise TypeError("intent_request must be an IntentRequest")
        if not isinstance(self.project_context, ProjectContext):
            raise TypeError("project_context must be a ProjectContext")

        for name, value in (
            ("success_conditions", self.success_conditions),
            ("outcome_uncertainties", self.outcome_uncertainties),
            ("risk_signals", self.risk_signals),
        ):
            _require_string_tuple(value, name)

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

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "cycle_id": self.cycle_id,
            "reasoning_request_id": self.reasoning_request_id,
            "intent_ref": self.intent_ref,
            "intent_request": self.intent_request.to_dict(),
            "project_context": self.project_context.to_dict(),
            "success_conditions": list(self.success_conditions),
            "outcome_uncertainties": list(self.outcome_uncertainties),
            "risk_signals": list(self.risk_signals),
            "requested_depth": self.requested_depth,
            "budget": self.budget,
        }


class CycleDisposition(str, Enum):
    """Structural disposition of one bounded cognitive cycle."""

    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    TRANSIENT_REASONING_RESULT = "TRANSIENT_REASONING_RESULT"
    PROJECT_REASONING_RESULT = "PROJECT_REASONING_RESULT"
    REASONING_TIED = "REASONING_TIED"
    REASONING_INSUFFICIENT = "REASONING_INSUFFICIENT"
    SEARCH_REQUIRED_SIGNAL = "SEARCH_REQUIRED_SIGNAL"
    VERIFY_REQUIRED_SIGNAL = "VERIFY_REQUIRED_SIGNAL"


class NextInteraction(str, Enum):
    """Bounded indicator for the next external interaction."""

    NONE = "NONE"
    USER_CLARIFICATION = "USER_CLARIFICATION"
    USER_DECISION = "USER_DECISION"
    EVIDENCE_COORDINATION = "EVIDENCE_COORDINATION"
    SEARCH_COORDINATION = "SEARCH_COORDINATION"


@dataclass(frozen=True, slots=True)
class ReasoningHandoffResult:
    """SYSTEM-safe correlation wrapper for a bounded reasoning result."""

    reasoning_request_id: str
    adaptive_result: AdaptiveCycleResult

    def __post_init__(self) -> None:
        _require_non_empty_string(self.reasoning_request_id, "reasoning_request_id")
        if not isinstance(self.adaptive_result, AdaptiveCycleResult):
            raise TypeError("adaptive_result must be an AdaptiveCycleResult")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization of public bounded data."""
        return {
            "reasoning_request_id": self.reasoning_request_id,
            "adaptive_result": self.adaptive_result.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class CognitiveCycleResult:
    """Immutable result of exactly one bounded synchronous cognitive cycle."""

    cycle_id: str
    intent_ref: str
    disposition: CycleDisposition
    interpretation: IntentInterpretation
    clarification_required: bool
    clarification_questions: tuple[str, ...]
    outcome: OutcomeModel | None
    project_context_mode: ProjectContextMode
    current_project_state: ProjectState | None
    reasoning_request: ReasoningRequest | None
    reasoning: ReasoningHandoffResult | None
    next_interaction: NextInteraction

    def __post_init__(self) -> None:
        _require_non_empty_string(self.cycle_id, "cycle_id")
        _require_non_empty_string(self.intent_ref, "intent_ref")

        if not isinstance(self.disposition, CycleDisposition):
            raise TypeError("disposition must be a CycleDisposition")
        if not isinstance(self.interpretation, IntentInterpretation):
            raise TypeError("interpretation must be an IntentInterpretation")
        if not isinstance(self.clarification_required, bool):
            raise TypeError("clarification_required must be a bool")
        _require_string_tuple(self.clarification_questions, "clarification_questions")
        if not isinstance(self.project_context_mode, ProjectContextMode):
            raise TypeError("project_context_mode must be a ProjectContextMode")
        if self.outcome is not None and not isinstance(self.outcome, OutcomeModel):
            raise TypeError("outcome must be an OutcomeModel or None")
        if self.current_project_state is not None and not isinstance(
            self.current_project_state, ProjectState
        ):
            raise TypeError("current_project_state must be a ProjectState or None")
        if self.reasoning_request is not None and not isinstance(
            self.reasoning_request, ReasoningRequest
        ):
            raise TypeError("reasoning_request must be a ReasoningRequest or None")
        if self.reasoning is not None and not isinstance(
            self.reasoning, ReasoningHandoffResult
        ):
            raise TypeError("reasoning must be a ReasoningHandoffResult or None")
        if not isinstance(self.next_interaction, NextInteraction):
            raise TypeError("next_interaction must be a NextInteraction")

        if self.clarification_required != self.interpretation.clarification_required:
            raise ValueError("clarification_required must match interpretation")
        if self.clarification_questions != self.interpretation.clarification_questions:
            raise ValueError("clarification_questions must match interpretation")

        if self.clarification_required:
            self._validate_clarification_result()
        else:
            self._validate_reasoning_result()

    def _validate_clarification_result(self) -> None:
        if self.disposition is not CycleDisposition.CLARIFICATION_REQUIRED:
            raise ValueError("clarification result requires clarification disposition")
        if self.next_interaction is not NextInteraction.USER_CLARIFICATION:
            raise ValueError("clarification result requires user clarification")
        if any(
            artifact is not None
            for artifact in (
                self.outcome,
                self.current_project_state,
                self.reasoning_request,
                self.reasoning,
            )
        ):
            raise ValueError("clarification result cannot contain downstream artifacts")

    def _validate_reasoning_result(self) -> None:
        if self.disposition is CycleDisposition.CLARIFICATION_REQUIRED:
            raise ValueError(
                "non-clarification result cannot use clarification disposition"
            )
        if self.outcome is None:
            raise ValueError("non-clarification result requires outcome")
        if self.reasoning_request is None or self.reasoning is None:
            raise ValueError("non-clarification result requires correlated reasoning")
        if self.outcome.intent_ref != self.intent_ref:
            raise ValueError("outcome intent_ref must match result intent_ref")
        if self.reasoning_request.intent_ref != self.intent_ref:
            raise ValueError(
                "reasoning request intent_ref must match result intent_ref"
            )
        if self.reasoning_request.outcome_ref != self.intent_ref:
            raise ValueError(
                "reasoning request outcome_ref must match result intent_ref"
            )
        if (
            self.reasoning.reasoning_request_id
            != self.reasoning_request.reasoning_request_id
        ):
            raise ValueError("reasoning result must correlate to reasoning request")

        if self.project_context_mode is ProjectContextMode.TRANSIENT:
            if self.current_project_state is not None:
                raise ValueError("TRANSIENT result cannot contain project state")
        elif self.current_project_state is None:
            raise ValueError("project-backed result requires current project state")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization of bounded public artifacts."""
        return {
            "cycle_id": self.cycle_id,
            "intent_ref": self.intent_ref,
            "disposition": self.disposition.value,
            "interpretation": self.interpretation.to_dict(),
            "clarification_required": self.clarification_required,
            "clarification_questions": list(self.clarification_questions),
            "outcome": self.outcome.to_dict() if self.outcome is not None else None,
            "project_context_mode": self.project_context_mode.value,
            "current_project_state": (
                self.current_project_state.to_dict()
                if self.current_project_state is not None
                else None
            ),
            "reasoning_request": (
                self.reasoning_request.to_dict()
                if self.reasoning_request is not None
                else None
            ),
            "reasoning": self.reasoning.to_dict() if self.reasoning else None,
            "next_interaction": self.next_interaction.value,
        }
