"""Adapter from canonical capability selection to canonical bounded planning.

This module deliberately plans but never executes.  It converts a validated
``aegis-core`` capability selection plus Platform workflow hints into the
canonical ``BoundedPlan`` contract used by the MVP runtime boundary.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from aegis_core.contracts import (
    AuthorityRequirement,
    BoundedPlan,
    BoundedPlanStep,
    CapabilitySelection,
    ConsequenceClass,
)

from aegis_os.pipeline.models import IntentAnalysis, RiskLevel, WorkflowStep


class BoundedPlanningAdapterError(ValueError):
    """Raised when a bounded plan cannot be produced safely."""


@dataclass(frozen=True, slots=True)
class PlanningBounds:
    """Explicit limits applied while translating a workflow into a plan."""

    max_steps: int = 8
    require_completion_criteria: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.max_steps, bool) or self.max_steps < 1:
            raise BoundedPlanningAdapterError("max_steps must be a positive integer")


class BoundedPlanningAdapter:
    """Build a canonical, non-executing plan from a canonical selection."""

    def __init__(self, *, bounds: PlanningBounds | None = None) -> None:
        self.bounds = bounds or PlanningBounds()

    def build(
        self,
        *,
        selection: CapabilitySelection,
        interpretation_id: str,
        objective: str,
        workflow: Iterable[WorkflowStep | Mapping[str, Any] | str],
        intent: IntentAnalysis | None = None,
        expected_evidence: Iterable[str] | None = None,
        assumptions: Iterable[str] = (),
        limitations: Iterable[str] = (),
        stop_conditions: Iterable[str] | None = None,
    ) -> BoundedPlan:
        """Translate Platform workflow hints into a canonical ``BoundedPlan``.

        The adapter does not execute steps, create authority grants, or imply
        that approval has been obtained.  It only records the authority needed
        before each step may run.
        """

        clean_objective = objective.strip()
        if not clean_objective:
            raise BoundedPlanningAdapterError("objective must not be empty")

        raw_steps = list(workflow)
        if not raw_steps:
            raise BoundedPlanningAdapterError("workflow must contain at least one step")
        if len(raw_steps) > self.bounds.max_steps:
            raise BoundedPlanningAdapterError(
                f"workflow exceeds the configured maximum of {self.bounds.max_steps} steps"
            )

        consequence_class = self._consequence_class(intent)
        canonical_steps = tuple(
            self._build_step(
                raw_step,
                sequence=index,
                authority_requirement=selection.authority_requirement,
            )
            for index, raw_step in enumerate(raw_steps, start=1)
        )

        evidence = tuple(
            item.strip()
            for item in (expected_evidence or self._default_evidence(canonical_steps))
            if item.strip()
        )
        if not evidence:
            raise BoundedPlanningAdapterError("expected evidence must not be empty")

        stops = tuple(item.strip() for item in (stop_conditions or ()) if item.strip())
        if consequence_class is not ConsequenceClass.LOW and not stops:
            stops = self._default_stop_conditions(selection)

        normalized_limitations = tuple(
            item.strip() for item in limitations if item.strip()
        )
        boundary_statement = "Planning output only; no step has been executed."
        if boundary_statement not in normalized_limitations:
            normalized_limitations += (boundary_statement,)

        return BoundedPlan(
            request_id=selection.request_id,
            interpretation_id=interpretation_id,
            selection_id=selection.selection_id,
            objective=clean_objective,
            steps=canonical_steps,
            expected_evidence=evidence,
            stop_conditions=stops,
            assumptions=tuple(item.strip() for item in assumptions if item.strip()),
            limitations=normalized_limitations,
            consequence_class=consequence_class,
        )

    def _build_step(
        self,
        raw_step: WorkflowStep | Mapping[str, Any] | str,
        *,
        sequence: int,
        authority_requirement: AuthorityRequirement,
    ) -> BoundedPlanStep:
        summary, description = self._read_step(raw_step, sequence)
        completion_criteria = self._completion_criteria(
            raw_step,
            summary=summary,
            description=description,
        )

        return BoundedPlanStep(
            sequence=sequence,
            summary=summary,
            completion_criteria=completion_criteria,
            authority_requirement=authority_requirement,
        )

    def _completion_criteria(
        self,
        raw_step: WorkflowStep | Mapping[str, Any] | str,
        *,
        summary: str,
        description: str,
    ) -> tuple[str, ...]:
        explicit: Any = None
        if isinstance(raw_step, Mapping):
            explicit = raw_step.get("completion_criteria")
        else:
            explicit = getattr(raw_step, "completion_criteria", None)

        if isinstance(explicit, str):
            criteria = (explicit.strip(),) if explicit.strip() else ()
        elif explicit is None:
            criteria = ()
        else:
            criteria = tuple(str(item).strip() for item in explicit if str(item).strip())

        if criteria:
            return criteria
        if not self.bounds.require_completion_criteria:
            return (f"{summary} is recorded as complete.",)
        return (f"Evidence confirms: {description.rstrip('.') }.",)

    @staticmethod
    def _read_step(
        raw_step: WorkflowStep | Mapping[str, Any] | str,
        sequence: int,
    ) -> tuple[str, str]:
        if isinstance(raw_step, WorkflowStep):
            summary = raw_step.title.strip()
            description = raw_step.description.strip() or summary
        elif isinstance(raw_step, str):
            summary = raw_step.strip()
            description = summary
        elif isinstance(raw_step, Mapping):
            summary = str(
                raw_step.get("title")
                or raw_step.get("summary")
                or raw_step.get("name")
                or ""
            ).strip()
            description = str(
                raw_step.get("description")
                or raw_step.get("instruction")
                or summary
            ).strip()
        else:
            raise BoundedPlanningAdapterError(
                f"unsupported workflow step at sequence {sequence}"
            )

        if not summary:
            raise BoundedPlanningAdapterError(
                f"workflow step {sequence} requires a non-empty summary"
            )
        return summary, description or summary

    @staticmethod
    def _consequence_class(intent: IntentAnalysis | None) -> ConsequenceClass:
        if intent is None:
            return ConsequenceClass.LOW
        return {
            RiskLevel.LOW: ConsequenceClass.LOW,
            RiskLevel.MEDIUM: ConsequenceClass.MODERATE,
            RiskLevel.HIGH: ConsequenceClass.HIGH,
        }[intent.risk]

    @staticmethod
    def _default_evidence(steps: tuple[BoundedPlanStep, ...]) -> tuple[str, ...]:
        return tuple(
            f"Completion evidence for step {step.sequence}: {step.summary}"
            for step in steps
        )

    @staticmethod
    def _default_stop_conditions(
        selection: CapabilitySelection,
    ) -> tuple[str, ...]:
        conditions = [
            "Stop when required evidence is unavailable or contradictory.",
            "Stop when the requested scope changes beyond this plan.",
        ]
        if selection.authority_requirement is not AuthorityRequirement.NONE:
            conditions.append(
                "Stop before any authority-gated action until explicit approval is verified."
            )
        return tuple(conditions)
