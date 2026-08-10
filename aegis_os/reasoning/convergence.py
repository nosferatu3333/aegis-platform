"""Bounded deterministic convergence for AEGIS adaptive reasoning.

WO-REASON-005 consumes existing candidate paths and existing candidate
evaluations.

It does not:
- generate candidates,
- reevaluate candidates,
- recurse,
- invoke tools,
- perform external search,
- grant authority,
- grant approval,
- grant execution permission,
- issue a governed verdict,
- create personas, judges, councils, or votes,
- persist cognitive memory.

A resolved candidate is a reasoning preference only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .candidates import CandidatePath
from .evaluation import CandidateEvaluation
from .models import ReasoningRequest


class ConvergenceStatus(str, Enum):
    """Bounded convergence outcome."""

    RESOLVED = "RESOLVED"
    TIED = "TIED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True, slots=True)
class ConvergenceResult:
    """Immutable convergence result."""

    status: ConvergenceStatus
    preferred_candidate_id: str | None
    eligible_candidate_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, ConvergenceStatus):
            raise TypeError("status must be a ConvergenceStatus")

        if self.preferred_candidate_id is not None and not isinstance(
            self.preferred_candidate_id,
            str,
        ):
            raise TypeError("preferred_candidate_id must be a string or None")

        if not isinstance(self.eligible_candidate_ids, tuple):
            raise TypeError("eligible_candidate_ids must be a tuple")

        if any(
            not isinstance(candidate_id, str)
            for candidate_id in self.eligible_candidate_ids
        ):
            raise TypeError("eligible_candidate_ids must contain strings")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")

        if self.status is ConvergenceStatus.RESOLVED:
            if self.preferred_candidate_id is None:
                raise ValueError("RESOLVED convergence requires preferred_candidate_id")

            if self.preferred_candidate_id not in self.eligible_candidate_ids:
                raise ValueError(
                    "preferred_candidate_id must be eligible when RESOLVED"
                )

        else:
            if self.preferred_candidate_id is not None:
                raise ValueError(
                    "unresolved convergence cannot expose a preferred candidate"
                )

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "status": self.status.value,
            "preferred_candidate_id": self.preferred_candidate_id,
            "eligible_candidate_ids": list(self.eligible_candidate_ids),
            "reason": self.reason,
        }


class ConvergenceController:
    """Resolve an evaluated candidate set using explicit stopping rules."""

    MIN_CANDIDATES = 2

    def converge(
        self,
        request: ReasoningRequest,
        candidates: tuple[CandidatePath, ...],
        evaluations: tuple[CandidateEvaluation, ...],
    ) -> ConvergenceResult:
        """Resolve, tie, or stop for insufficient support."""
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        if not isinstance(candidates, tuple):
            raise TypeError("candidates must be a tuple of CandidatePath")

        if not isinstance(evaluations, tuple):
            raise TypeError("evaluations must be a tuple of CandidateEvaluation")

        if len(candidates) < self.MIN_CANDIDATES:
            raise ValueError(
                f"convergence requires at least {self.MIN_CANDIDATES} candidates"
            )

        if len(candidates) != len(evaluations):
            raise ValueError("candidate and evaluation counts must match")

        if any(not isinstance(candidate, CandidatePath) for candidate in candidates):
            raise TypeError("every candidate must be a CandidatePath")

        if any(
            not isinstance(evaluation, CandidateEvaluation)
            for evaluation in evaluations
        ):
            raise TypeError("every evaluation must be a CandidateEvaluation")

        self._validate_candidate_context(request, candidates)
        self._validate_identifier_sets(candidates, evaluations)

        by_id = {evaluation.candidate_id: evaluation for evaluation in evaluations}

        top_score = max(evaluation.aggregate_score for evaluation in evaluations)

        top_candidate_ids = tuple(
            candidate.candidate_id
            for candidate in candidates
            if by_id[candidate.candidate_id].aggregate_score == top_score
        )

        if len(top_candidate_ids) > 1:
            return ConvergenceResult(
                status=ConvergenceStatus.TIED,
                preferred_candidate_id=None,
                eligible_candidate_ids=top_candidate_ids,
                reason=(
                    "Multiple candidates share the highest aggregate score; "
                    "no tie-breaker is authorized."
                ),
            )

        preferred_candidate_id = top_candidate_ids[0]
        preferred_evaluation = by_id[preferred_candidate_id]

        insufficiency_reason = self._insufficiency_reason(
            request,
            preferred_evaluation,
        )

        if insufficiency_reason is not None:
            return ConvergenceResult(
                status=ConvergenceStatus.INSUFFICIENT,
                preferred_candidate_id=None,
                eligible_candidate_ids=(preferred_candidate_id,),
                reason=insufficiency_reason,
            )

        return ConvergenceResult(
            status=ConvergenceStatus.RESOLVED,
            preferred_candidate_id=preferred_candidate_id,
            eligible_candidate_ids=(preferred_candidate_id,),
            reason=(
                "One candidate has a unique highest aggregate score and "
                "passes the active sufficiency gates."
            ),
        )

    @staticmethod
    def _validate_candidate_context(
        request: ReasoningRequest,
        candidates: tuple[CandidatePath, ...],
    ) -> None:
        for candidate in candidates:
            if candidate.intent_ref != request.intent_ref:
                raise ValueError("candidate intent_ref does not match request")

            if candidate.outcome_ref != request.outcome_ref:
                raise ValueError("candidate outcome_ref does not match request")

    @staticmethod
    def _validate_identifier_sets(
        candidates: tuple[CandidatePath, ...],
        evaluations: tuple[CandidateEvaluation, ...],
    ) -> None:
        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)

        evaluation_ids = tuple(evaluation.candidate_id for evaluation in evaluations)

        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate identifiers must be unique")

        if len(evaluation_ids) != len(set(evaluation_ids)):
            raise ValueError("evaluation identifiers must be unique")

        if set(candidate_ids) != set(evaluation_ids):
            raise ValueError(
                "candidate and evaluation identifier sets must match exactly"
            )

    @staticmethod
    def _insufficiency_reason(
        request: ReasoningRequest,
        evaluation: CandidateEvaluation,
    ) -> str | None:
        evidence_pressure = bool(request.uncertainty_signals or request.risk_signals)

        if evidence_pressure and evaluation.evidence_readiness <= 1:
            return (
                "The unique aggregate leader has materially insufficient "
                "evidence readiness under active evidence pressure."
            )

        if request.uncertainty_signals and evaluation.uncertainty_exposure <= 1:
            return (
                "The unique aggregate leader leaves material uncertainty "
                "insufficiently controlled."
            )

        if request.risk_signals and evaluation.risk_exposure <= 1:
            return (
                "The unique aggregate leader leaves material risk "
                "insufficiently controlled."
            )

        return None
