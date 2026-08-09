"""Bounded candidate-path generation for AEGIS adaptive reasoning.

WO-REASON-003 generates materially distinct reasoning approaches only.

It does not:
- evaluate candidates,
- rank candidates,
- select a winner,
- converge,
- grant authority,
- grant execution permission,
- invoke tools,
- perform external search,
- create personas,
- mutate persistent memory.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import ReasoningMode, ReasoningRequest


@dataclass(frozen=True, slots=True)
class CandidatePath:
    """One bounded descriptive reasoning approach."""

    candidate_id: str
    intent_ref: str
    outcome_ref: str
    label: str
    summary: str
    primary_objective: str
    assumptions: tuple[str, ...]
    constraints_acknowledged: tuple[str, ...]
    evidence_needs: tuple[str, ...]
    known_uncertainty: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic serialization."""
        return {
            "candidate_id": self.candidate_id,
            "intent_ref": self.intent_ref,
            "outcome_ref": self.outcome_ref,
            "label": self.label,
            "summary": self.summary,
            "primary_objective": self.primary_objective,
            "assumptions": list(self.assumptions),
            "constraints_acknowledged": list(self.constraints_acknowledged),
            "evidence_needs": list(self.evidence_needs),
            "known_uncertainty": list(self.known_uncertainty),
        }


class CandidatePathGenerator:
    """Generate bounded, deterministic, materially distinct candidate paths."""

    MIN_CANDIDATES = 2
    DEFAULT_CANDIDATES = 3
    MAX_CANDIDATES = 5

    _APPROACHES = (
        (
            "constraint-first",
            "Constraint-First",
            "Prioritize explicit constraints and eliminate approaches that violate them.",
            "Satisfy the objective while preserving the strongest stated constraints.",
        ),
        (
            "evidence-first",
            "Evidence-First",
            "Reduce uncertainty by identifying the evidence needed before commitment.",
            "Improve decision quality by resolving the most material unknowns.",
        ),
        (
            "direct-outcome",
            "Direct-Outcome",
            "Pursue the shortest bounded path toward the intended outcome.",
            "Reach the intended outcome with the least unnecessary cognitive overhead.",
        ),
        (
            "risk-first",
            "Risk-First",
            "Structure the approach around the material risks and reversibility of decisions.",
            "Preserve optionality while reducing exposure to avoidable failure.",
        ),
        (
            "dependency-first",
            "Dependency-First",
            "Order reasoning around prerequisites, dependencies, and sequencing constraints.",
            "Resolve blocking dependencies before committing to downstream choices.",
        ),
    )

    def generate(
        self,
        request: ReasoningRequest,
        *,
        mode: ReasoningMode,
        candidate_count: int | None = None,
    ) -> tuple[CandidatePath, ...]:
        """Generate deterministic candidate paths for BRANCH reasoning only."""
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        if mode is not ReasoningMode.BRANCH:
            raise ValueError("candidate generation requires BRANCH reasoning mode")

        count = self._resolve_candidate_count(candidate_count)

        approaches = self._select_approaches(request, count)

        candidates = tuple(
            self._build_candidate(
                request=request,
                ordinal=index + 1,
                approach=approach,
            )
            for index, approach in enumerate(approaches)
        )

        self._assert_material_distinctness(candidates)

        return candidates

    def _resolve_candidate_count(self, candidate_count: int | None) -> int:
        if candidate_count is None:
            return self.DEFAULT_CANDIDATES

        if isinstance(candidate_count, bool) or not isinstance(candidate_count, int):
            raise TypeError("candidate_count must be an integer")

        if candidate_count < self.MIN_CANDIDATES:
            raise ValueError(f"candidate_count must be at least {self.MIN_CANDIDATES}")

        if candidate_count > self.MAX_CANDIDATES:
            raise ValueError(f"candidate_count must not exceed {self.MAX_CANDIDATES}")

        return candidate_count

    def _select_approaches(
        self,
        request: ReasoningRequest,
        count: int,
    ) -> tuple[tuple[str, str, str, str], ...]:
        selected: list[tuple[str, str, str, str]] = []

        if request.constraints:
            selected.append(self._approach("constraint-first"))

        if request.uncertainty_signals:
            selected.append(self._approach("evidence-first"))

        if request.risk_signals:
            selected.append(self._approach("risk-first"))

        selected.append(self._approach("direct-outcome"))
        selected.append(self._approach("dependency-first"))

        for approach in self._APPROACHES:
            if approach not in selected:
                selected.append(approach)

        return tuple(selected[:count])

    def _approach(
        self,
        approach_id: str,
    ) -> tuple[str, str, str, str]:
        for approach in self._APPROACHES:
            if approach[0] == approach_id:
                return approach

        raise RuntimeError(f"unknown internal approach: {approach_id}")

    def _build_candidate(
        self,
        *,
        request: ReasoningRequest,
        ordinal: int,
        approach: tuple[str, str, str, str],
    ) -> CandidatePath:
        approach_id, label, summary, objective = approach

        return CandidatePath(
            candidate_id=(
                f"{request.reasoning_request_id}:candidate:{ordinal}:{approach_id}"
            ),
            intent_ref=request.intent_ref,
            outcome_ref=request.outcome_ref,
            label=label,
            summary=summary,
            primary_objective=objective,
            assumptions=self._assumptions_for(approach_id),
            constraints_acknowledged=tuple(request.constraints),
            evidence_needs=self._evidence_needs_for(request, approach_id),
            known_uncertainty=tuple(request.uncertainty_signals),
        )

    @staticmethod
    def _assumptions_for(approach_id: str) -> tuple[str, ...]:
        assumptions = {
            "constraint-first": (
                "Explicit constraints are authoritative inputs to reasoning.",
            ),
            "evidence-first": (
                "Material uncertainty should be reduced before commitment.",
            ),
            "direct-outcome": (
                "A bounded direct path may exist without additional branching.",
            ),
            "risk-first": (
                "Material risks should influence sequencing and reversibility.",
            ),
            "dependency-first": (
                "Blocking dependencies should be resolved before downstream choices.",
            ),
        }

        return assumptions[approach_id]

    @staticmethod
    def _evidence_needs_for(
        request: ReasoningRequest,
        approach_id: str,
    ) -> tuple[str, ...]:
        needs: list[str] = []

        if approach_id == "evidence-first":
            needs.extend(request.uncertainty_signals)

        if approach_id == "risk-first":
            needs.extend(request.risk_signals)

        return tuple(needs)

    @staticmethod
    def _assert_material_distinctness(
        candidates: tuple[CandidatePath, ...],
    ) -> None:
        signatures = {
            (
                candidate.label,
                candidate.summary,
                candidate.primary_objective,
            )
            for candidate in candidates
        }

        if len(signatures) != len(candidates):
            raise RuntimeError(
                "candidate generation produced non-distinct candidate paths"
            )
