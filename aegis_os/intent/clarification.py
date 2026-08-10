"""Bounded clarification assessment for interpreted intent."""

from __future__ import annotations

from .models import (
    ClarificationAssessment,
    ClarificationState,
    IntentAmbiguity,
)


class ClarificationEngine:
    """Determine whether recorded ambiguity blocks downstream processing."""

    def assess(
        self,
        ambiguities: tuple[IntentAmbiguity, ...],
    ) -> ClarificationAssessment:
        """Return a deterministic clarification assessment."""
        if not isinstance(ambiguities, tuple):
            raise TypeError("ambiguities must be a tuple")

        if any(not isinstance(item, IntentAmbiguity) for item in ambiguities):
            raise TypeError("ambiguities must contain IntentAmbiguity objects")

        blocking = tuple(item for item in ambiguities if item.blocking)

        if not blocking:
            return ClarificationAssessment(
                state=ClarificationState.SUFFICIENT,
                blocking_ambiguities=(),
                questions=(),
                reason=("No blocking ambiguity prevents downstream intent processing."),
            )

        questions = tuple(
            item.question for item in blocking if item.question is not None
        )

        return ClarificationAssessment(
            state=ClarificationState.CLARIFICATION_REQUIRED,
            blocking_ambiguities=blocking,
            questions=questions,
            reason=(
                "One or more unresolved ambiguities materially affect "
                "the interpretation or requested operation."
            ),
        )
