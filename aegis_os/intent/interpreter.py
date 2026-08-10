"""Deterministic minimum viable intent interpreter."""

from __future__ import annotations

import re

from .clarification import ClarificationEngine
from .models import (
    IntentAmbiguity,
    IntentInterpretation,
    IntentRequest,
    IntentType,
)


class IntentInterpreter:
    """Produce a bounded structured interpretation of one IntentRequest."""

    _EXECUTE_MARKERS = (
        "send ",
        "publish ",
        "deploy ",
        "delete ",
        "remove ",
        "book ",
        "buy ",
        "cancel ",
        "merge ",
        "push ",
        "approve ",
        "archive ",
    )

    _CHANGE_MARKERS = (
        "change ",
        "modify ",
        "edit ",
        "update ",
        "fix ",
        "replace ",
        "correct ",
    )

    _CREATE_MARKERS = (
        "create ",
        "write ",
        "draft ",
        "generate ",
        "build ",
        "design ",
        "make ",
    )

    _PLAN_MARKERS = (
        "plan ",
        "roadmap",
        "strategy",
        "schedule ",
        "organize ",
        "how should",
        "how can",
    )

    _EVALUATE_MARKERS = (
        "evaluate ",
        "review ",
        "assess ",
        "compare ",
        "audit ",
        "check ",
        "verify ",
        "analyze ",
    )

    _DECIDE_MARKERS = (
        "decide ",
        "choose ",
        "which ",
        "which one",
        "should i",
        "should we",
    )

    _UNDERSTAND_MARKERS = (
        "understand ",
        "explain ",
        "why ",
        "what is",
        "what are",
        "tell me",
        "describe ",
    )

    _PLACEHOLDER_PATTERNS = (
        r"<[^>]+>",
        r"\[[^\]]+\]",
        r"\bTBD\b",
        r"\?\?\?",
    )

    _DEICTIC_TOKENS = {
        "it",
        "this",
        "that",
        "them",
        "those",
    }

    _TARGET_SENSITIVE_TYPES = {
        IntentType.CHANGE,
        IntentType.EVALUATE,
        IntentType.EXECUTE_REQUEST,
    }

    def __init__(
        self,
        *,
        clarification_engine: ClarificationEngine | None = None,
    ) -> None:
        self._clarification_engine = (
            clarification_engine
            if clarification_engine is not None
            else ClarificationEngine()
        )

    def interpret(
        self,
        request: IntentRequest,
    ) -> IntentInterpretation:
        """Interpret one request without granting authority or executing."""
        if not isinstance(request, IntentRequest):
            raise TypeError("request must be an IntentRequest")

        normalized = " ".join(request.raw_request.split())

        intent_type = self._classify(normalized)
        ambiguities = self._detect_ambiguities(
            normalized,
            intent_type=intent_type,
            context_refs=request.context_refs,
            explicit_constraints=request.explicit_constraints,
        )

        clarification = self._clarification_engine.assess(ambiguities)

        return IntentInterpretation(
            raw_request=request.raw_request,
            interpreted_intent=normalized,
            intent_type=intent_type,
            explicit_constraints=request.explicit_constraints,
            inferred_constraints=(),
            ambiguities=ambiguities,
            clarification_required=bool(clarification.blocking_ambiguities),
            clarification_questions=clarification.questions,
        )

    def _classify(
        self,
        normalized_request: str,
    ) -> IntentType:
        lowered = normalized_request.lower()

        ordered_rules = (
            (
                IntentType.EXECUTE_REQUEST,
                self._EXECUTE_MARKERS,
            ),
            (
                IntentType.CHANGE,
                self._CHANGE_MARKERS,
            ),
            (
                IntentType.CREATE,
                self._CREATE_MARKERS,
            ),
            (
                IntentType.PLAN,
                self._PLAN_MARKERS,
            ),
            (
                IntentType.EVALUATE,
                self._EVALUATE_MARKERS,
            ),
            (
                IntentType.DECIDE,
                self._DECIDE_MARKERS,
            ),
            (
                IntentType.UNDERSTAND,
                self._UNDERSTAND_MARKERS,
            ),
        )

        for intent_type, markers in ordered_rules:
            if any(marker in lowered for marker in markers):
                return intent_type

        return IntentType.UNDERSTAND

    def _detect_ambiguities(
        self,
        normalized_request: str,
        *,
        intent_type: IntentType,
        context_refs: tuple[str, ...],
        explicit_constraints: tuple[str, ...],
    ) -> tuple[IntentAmbiguity, ...]:
        ambiguities: list[IntentAmbiguity] = []

        for pattern in self._PLACEHOLDER_PATTERNS:
            if re.search(
                pattern,
                normalized_request,
                flags=re.IGNORECASE,
            ):
                ambiguities.append(
                    IntentAmbiguity(
                        code="UNRESOLVED_PLACEHOLDER",
                        description=(
                            "The request contains an unresolved placeholder "
                            "whose value may materially change interpretation."
                        ),
                        blocking=True,
                        question=(
                            "What specific value or target should replace "
                            "the unresolved placeholder?"
                        ),
                    )
                )
                break

        tokens = {
            token.lower()
            for token in re.findall(
                r"[A-Za-z0-9_'-]+",
                normalized_request,
            )
        }

        has_deictic_reference = bool(tokens.intersection(self._DEICTIC_TOKENS))

        if (
            intent_type in self._TARGET_SENSITIVE_TYPES
            and has_deictic_reference
            and not context_refs
        ):
            ambiguities.append(
                IntentAmbiguity(
                    code="UNRESOLVED_TARGET_REFERENCE",
                    description=(
                        "The requested operation refers to a target that "
                        "is not identified by the available context."
                    ),
                    blocking=True,
                    question=("What specific target should this operation apply to?"),
                )
            )

        lowered = normalized_request.lower()

        if (
            "best" in tokens
            and not explicit_constraints
            and not any(
                marker in lowered
                for marker in (
                    "cheapest",
                    "fastest",
                    "safest",
                    "highest quality",
                    "lowest cost",
                )
            )
        ):
            ambiguities.append(
                IntentAmbiguity(
                    code="PREFERENCE_CRITERIA_UNSPECIFIED",
                    description=(
                        "The request uses a comparative preference without "
                        "stating selection criteria."
                    ),
                    blocking=False,
                    question=None,
                )
            )

        return tuple(ambiguities)
