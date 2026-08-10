"""Outcome and constraint modeling for sufficient interpreted intent."""

from __future__ import annotations

from dataclasses import dataclass

from .models import IntentInterpretation


@dataclass(frozen=True, slots=True)
class OutcomeModel:
    """Structured desired state derived from a sufficient interpretation."""

    intent_ref: str
    desired_state: str
    success_conditions: tuple[str, ...]
    explicit_constraints: tuple[str, ...]
    inferred_constraints: tuple[str, ...]
    outcome_uncertainties: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.intent_ref, str) or not self.intent_ref.strip():
            raise TypeError("intent_ref must be a non-empty string")

        if not isinstance(self.desired_state, str) or not self.desired_state.strip():
            raise TypeError("desired_state must be a non-empty string")

        for name, value in (
            ("success_conditions", self.success_conditions),
            ("explicit_constraints", self.explicit_constraints),
            ("inferred_constraints", self.inferred_constraints),
            ("outcome_uncertainties", self.outcome_uncertainties),
        ):
            if not isinstance(value, tuple):
                raise TypeError(f"{name} must be a tuple")

            if any(not isinstance(item, str) or not item.strip() for item in value):
                raise TypeError(f"{name} must contain non-empty strings")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "intent_ref": self.intent_ref,
            "desired_state": self.desired_state,
            "success_conditions": list(self.success_conditions),
            "explicit_constraints": list(self.explicit_constraints),
            "inferred_constraints": list(self.inferred_constraints),
            "outcome_uncertainties": list(self.outcome_uncertainties),
        }


class OutcomeModeler:
    """Create a bounded outcome model from sufficient intent."""

    def model(
        self,
        interpretation: IntentInterpretation,
        *,
        intent_ref: str,
        success_conditions: tuple[str, ...] = (),
        inferred_constraints: tuple[str, ...] = (),
        outcome_uncertainties: tuple[str, ...] = (),
    ) -> OutcomeModel:
        """Build an outcome without planning, reasoning, or authority."""
        if not isinstance(interpretation, IntentInterpretation):
            raise TypeError("interpretation must be an IntentInterpretation")

        if interpretation.clarification_required:
            raise ValueError(
                "CLARIFICATION_REQUIRED interpretation is not eligible "
                "for outcome modeling"
            )

        if not isinstance(intent_ref, str) or not intent_ref.strip():
            raise TypeError("intent_ref must be a non-empty string")

        for name, value in (
            ("success_conditions", success_conditions),
            ("inferred_constraints", inferred_constraints),
            ("outcome_uncertainties", outcome_uncertainties),
        ):
            if not isinstance(value, tuple):
                raise TypeError(f"{name} must be a tuple")

            if any(not isinstance(item, str) or not item.strip() for item in value):
                raise TypeError(f"{name} must contain non-empty strings")

        return OutcomeModel(
            intent_ref=intent_ref,
            desired_state=interpretation.interpreted_intent,
            success_conditions=success_conditions,
            explicit_constraints=interpretation.explicit_constraints,
            inferred_constraints=inferred_constraints,
            outcome_uncertainties=outcome_uncertainties,
        )
