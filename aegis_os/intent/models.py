"""Core contracts for deterministic intent interpretation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IntentType(str, Enum):
    """Bounded orientation of a user intent."""

    UNDERSTAND = "UNDERSTAND"
    DECIDE = "DECIDE"
    CREATE = "CREATE"
    CHANGE = "CHANGE"
    EVALUATE = "EVALUATE"
    PLAN = "PLAN"
    EXECUTE_REQUEST = "EXECUTE_REQUEST"


class ClarificationState(str, Enum):
    """Whether an interpretation may safely continue downstream."""

    SUFFICIENT = "SUFFICIENT"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class IntentRequest:
    """Input contract for intent interpretation."""

    raw_request: str
    context_refs: tuple[str, ...] = ()
    explicit_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.raw_request, str):
            raise TypeError("raw_request must be a string")

        if not self.raw_request.strip():
            raise ValueError("raw_request must not be empty")

        if not isinstance(self.context_refs, tuple):
            raise TypeError("context_refs must be a tuple")

        if not isinstance(self.explicit_constraints, tuple):
            raise TypeError("explicit_constraints must be a tuple")

        if any(
            not isinstance(value, str) or not value.strip()
            for value in self.context_refs
        ):
            raise TypeError("context_refs must contain non-empty strings")

        if any(
            not isinstance(value, str) or not value.strip()
            for value in self.explicit_constraints
        ):
            raise TypeError("explicit_constraints must contain non-empty strings")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "raw_request": self.raw_request,
            "context_refs": list(self.context_refs),
            "explicit_constraints": list(self.explicit_constraints),
        }


@dataclass(frozen=True, slots=True)
class IntentAmbiguity:
    """One bounded ambiguity discovered during interpretation."""

    code: str
    description: str
    blocking: bool
    question: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code.strip():
            raise TypeError("code must be a non-empty string")

        if not isinstance(self.description, str) or not self.description.strip():
            raise TypeError("description must be a non-empty string")

        if not isinstance(self.blocking, bool):
            raise TypeError("blocking must be a boolean")

        if self.question is not None and (
            not isinstance(self.question, str) or not self.question.strip()
        ):
            raise TypeError("question must be a non-empty string or None")

        if self.blocking and self.question is None:
            raise ValueError("blocking ambiguity requires a clarification question")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "code": self.code,
            "description": self.description,
            "blocking": self.blocking,
            "question": self.question,
        }


@dataclass(frozen=True, slots=True)
class ClarificationAssessment:
    """Deterministic clarification decision."""

    state: ClarificationState
    blocking_ambiguities: tuple[IntentAmbiguity, ...]
    questions: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, ClarificationState):
            raise TypeError("state must be a ClarificationState")

        if not isinstance(self.blocking_ambiguities, tuple):
            raise TypeError("blocking_ambiguities must be a tuple")

        if any(
            not isinstance(item, IntentAmbiguity) for item in self.blocking_ambiguities
        ):
            raise TypeError("blocking_ambiguities must contain IntentAmbiguity objects")

        if any(not item.blocking for item in self.blocking_ambiguities):
            raise ValueError("blocking_ambiguities cannot contain non-blocking items")

        if not isinstance(self.questions, tuple):
            raise TypeError("questions must be a tuple")

        if any(
            not isinstance(question, str) or not question.strip()
            for question in self.questions
        ):
            raise TypeError("questions must contain non-empty strings")

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise TypeError("reason must be a non-empty string")

        if self.state is ClarificationState.SUFFICIENT:
            if self.blocking_ambiguities:
                raise ValueError("SUFFICIENT cannot contain blocking ambiguities")

            if self.questions:
                raise ValueError("SUFFICIENT cannot contain clarification questions")

        if self.state is ClarificationState.CLARIFICATION_REQUIRED:
            if not self.blocking_ambiguities:
                raise ValueError("CLARIFICATION_REQUIRED needs blocking ambiguities")

            if not self.questions:
                raise ValueError("CLARIFICATION_REQUIRED needs questions")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "state": self.state.value,
            "blocking_ambiguities": [
                item.to_dict() for item in self.blocking_ambiguities
            ],
            "questions": list(self.questions),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class IntentInterpretation:
    """Structured result of deterministic intent interpretation."""

    raw_request: str
    interpreted_intent: str
    intent_type: IntentType
    explicit_constraints: tuple[str, ...]
    inferred_constraints: tuple[str, ...]
    ambiguities: tuple[IntentAmbiguity, ...]
    clarification_required: bool
    clarification_questions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.raw_request, str):
            raise TypeError("raw_request must be a string")

        if (
            not isinstance(self.interpreted_intent, str)
            or not self.interpreted_intent.strip()
        ):
            raise TypeError("interpreted_intent must be a non-empty string")

        if not isinstance(self.intent_type, IntentType):
            raise TypeError("intent_type must be an IntentType")

        if not isinstance(self.explicit_constraints, tuple):
            raise TypeError("explicit_constraints must be a tuple")

        if not isinstance(self.inferred_constraints, tuple):
            raise TypeError("inferred_constraints must be a tuple")

        if not isinstance(self.ambiguities, tuple):
            raise TypeError("ambiguities must be a tuple")

        if any(not isinstance(item, IntentAmbiguity) for item in self.ambiguities):
            raise TypeError("ambiguities must contain IntentAmbiguity objects")

        if not isinstance(self.clarification_required, bool):
            raise TypeError("clarification_required must be a boolean")

        if not isinstance(self.clarification_questions, tuple):
            raise TypeError("clarification_questions must be a tuple")

        blocking = tuple(
            ambiguity for ambiguity in self.ambiguities if ambiguity.blocking
        )

        expected_questions = tuple(
            ambiguity.question
            for ambiguity in blocking
            if ambiguity.question is not None
        )

        if self.clarification_required != bool(blocking):
            raise ValueError("clarification_required must match blocking ambiguities")

        if self.clarification_questions != expected_questions:
            raise ValueError(
                "clarification_questions must derive from blocking ambiguities"
            )

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "raw_request": self.raw_request,
            "interpreted_intent": self.interpreted_intent,
            "intent_type": self.intent_type.value,
            "explicit_constraints": list(self.explicit_constraints),
            "inferred_constraints": list(self.inferred_constraints),
            "ambiguities": [ambiguity.to_dict() for ambiguity in self.ambiguities],
            "clarification_required": self.clarification_required,
            "clarification_questions": list(self.clarification_questions),
        }
