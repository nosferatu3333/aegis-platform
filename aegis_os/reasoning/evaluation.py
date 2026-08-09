"""Deterministic candidate evaluation for AEGIS adaptive reasoning.

WO-REASON-004 evaluates already-generated candidate paths against an explicit,
inspectable structural rubric.

It does not:
- generate candidate paths,
- rank candidates,
- select a winner,
- recommend a candidate,
- converge,
- grant authority,
- grant execution permission,
- invoke tools,
- perform external search,
- create personas or simulated judges,
- mutate persistent memory.

Scores are bounded descriptive comparison signals only.
"""

from __future__ import annotations

from dataclasses import dataclass

from .candidates import CandidatePath
from .models import ReasoningRequest


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    """One immutable descriptive evaluation record."""

    candidate_id: str
    constraint_alignment: int
    evidence_readiness: int
    uncertainty_exposure: int
    risk_exposure: int
    dependency_burden: int
    directness: int
    aggregate_score: int
    strengths: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        dimension_scores = (
            self.constraint_alignment,
            self.evidence_readiness,
            self.uncertainty_exposure,
            self.risk_exposure,
            self.dependency_burden,
            self.directness,
        )

        if any(
            isinstance(score, bool) or not isinstance(score, int)
            for score in dimension_scores
        ):
            raise TypeError("evaluation dimension scores must be integers")

        if any(score < 0 or score > 4 for score in dimension_scores):
            raise ValueError("evaluation dimension scores must be within 0..4")

        expected_aggregate = sum(dimension_scores)

        if self.aggregate_score != expected_aggregate:
            raise ValueError("aggregate_score must equal the sum of dimension scores")

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic serialization."""
        return {
            "candidate_id": self.candidate_id,
            "constraint_alignment": self.constraint_alignment,
            "evidence_readiness": self.evidence_readiness,
            "uncertainty_exposure": self.uncertainty_exposure,
            "risk_exposure": self.risk_exposure,
            "dependency_burden": self.dependency_burden,
            "directness": self.directness,
            "aggregate_score": self.aggregate_score,
            "strengths": list(self.strengths),
            "limitations": list(self.limitations),
        }


class CandidateEvaluator:
    """Evaluate candidate paths without ranking, selection, or convergence."""

    SCORE_MIN = 0
    SCORE_MAX = 4
    DIMENSION_COUNT = 6

    _LABELS = {
        "Constraint-First",
        "Evidence-First",
        "Direct-Outcome",
        "Risk-First",
        "Dependency-First",
    }

    def evaluate(
        self,
        request: ReasoningRequest,
        candidates: tuple[CandidatePath, ...],
    ) -> tuple[CandidateEvaluation, ...]:
        """Evaluate candidates in input order using the explicit rubric."""
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        if not isinstance(candidates, tuple):
            raise TypeError("candidates must be a tuple of CandidatePath")

        if not candidates:
            raise ValueError("at least one candidate is required")

        if any(not isinstance(candidate, CandidatePath) for candidate in candidates):
            raise TypeError("every candidate must be a CandidatePath")

        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)

        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate identifiers must be unique")

        for candidate in candidates:
            self._validate_candidate_context(request, candidate)

        return tuple(
            self._evaluate_candidate(request, candidate) for candidate in candidates
        )

    @staticmethod
    def _validate_candidate_context(
        request: ReasoningRequest,
        candidate: CandidatePath,
    ) -> None:
        if candidate.intent_ref != request.intent_ref:
            raise ValueError("candidate intent_ref does not match request")

        if candidate.outcome_ref != request.outcome_ref:
            raise ValueError("candidate outcome_ref does not match request")

    def _evaluate_candidate(
        self,
        request: ReasoningRequest,
        candidate: CandidatePath,
    ) -> CandidateEvaluation:
        if candidate.label not in self._LABELS:
            raise ValueError(f"unsupported candidate approach label: {candidate.label}")

        scores = {
            "constraint alignment": self._score_constraint_alignment(
                request,
                candidate,
            ),
            "evidence readiness": self._score_evidence_readiness(
                request,
                candidate,
            ),
            "uncertainty exposure": self._score_uncertainty_exposure(
                request,
                candidate,
            ),
            "risk exposure": self._score_risk_exposure(
                request,
                candidate,
            ),
            "dependency burden": self._score_dependency_burden(
                candidate,
            ),
            "directness": self._score_directness(
                candidate,
            ),
        }

        aggregate = sum(scores.values())

        strengths = tuple(
            dimension for dimension, score in scores.items() if score >= 3
        )

        limitations = tuple(
            dimension for dimension, score in scores.items() if score <= 1
        )

        return CandidateEvaluation(
            candidate_id=candidate.candidate_id,
            constraint_alignment=scores["constraint alignment"],
            evidence_readiness=scores["evidence readiness"],
            uncertainty_exposure=scores["uncertainty exposure"],
            risk_exposure=scores["risk exposure"],
            dependency_burden=scores["dependency burden"],
            directness=scores["directness"],
            aggregate_score=aggregate,
            strengths=strengths,
            limitations=limitations,
        )

    @staticmethod
    def _score_constraint_alignment(
        request: ReasoningRequest,
        candidate: CandidatePath,
    ) -> int:
        """Score explicit constraint handling.

        4: no constraints exist, or Constraint-First preserves all constraints.
        3: another supported approach preserves all constraints.
        2: candidate preserves some but not all constraints.
        0: candidate preserves none of the explicit constraints.
        """
        if not request.constraints:
            return 4

        acknowledged = set(candidate.constraints_acknowledged)
        required = set(request.constraints)

        if required.issubset(acknowledged):
            if candidate.label == "Constraint-First":
                return 4
            return 3

        overlap = required.intersection(acknowledged)

        if overlap:
            return 2

        return 0

    @staticmethod
    def _score_evidence_readiness(
        request: ReasoningRequest,
        candidate: CandidatePath,
    ) -> int:
        """Score how explicitly the path prepares needed evidence."""
        evidence_pressure = bool(request.uncertainty_signals or request.risk_signals)

        if not evidence_pressure:
            return 4

        if candidate.label == "Evidence-First":
            return 4

        if candidate.evidence_needs:
            return 3

        if candidate.label in {"Risk-First", "Dependency-First"}:
            return 2

        return 1

    @staticmethod
    def _score_uncertainty_exposure(
        request: ReasoningRequest,
        candidate: CandidatePath,
    ) -> int:
        """Score structural protection against unresolved uncertainty.

        Higher scores mean lower unresolved uncertainty exposure.
        """
        if not request.uncertainty_signals:
            return 4

        rubric = {
            "Evidence-First": 4,
            "Constraint-First": 2,
            "Risk-First": 2,
            "Dependency-First": 2,
            "Direct-Outcome": 1,
        }

        return rubric[candidate.label]

    @staticmethod
    def _score_risk_exposure(
        request: ReasoningRequest,
        candidate: CandidatePath,
    ) -> int:
        """Score structural protection against stated risk.

        Higher scores mean lower unmanaged risk exposure.
        """
        if not request.risk_signals:
            return 4

        rubric = {
            "Risk-First": 4,
            "Dependency-First": 3,
            "Constraint-First": 2,
            "Evidence-First": 2,
            "Direct-Outcome": 1,
        }

        return rubric[candidate.label]

    @staticmethod
    def _score_dependency_burden(
        candidate: CandidatePath,
    ) -> int:
        """Score how directly the approach manages dependency burden.

        Higher scores mean lower unresolved dependency burden.
        """
        rubric = {
            "Dependency-First": 4,
            "Direct-Outcome": 3,
            "Constraint-First": 2,
            "Evidence-First": 2,
            "Risk-First": 2,
        }

        return rubric[candidate.label]

    @staticmethod
    def _score_directness(
        candidate: CandidatePath,
    ) -> int:
        """Score structural directness toward the shared outcome."""
        rubric = {
            "Direct-Outcome": 4,
            "Constraint-First": 3,
            "Evidence-First": 2,
            "Risk-First": 2,
            "Dependency-First": 2,
        }

        return rubric[candidate.label]
