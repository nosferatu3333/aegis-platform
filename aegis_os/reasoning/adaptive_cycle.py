"""Bounded integrated adaptive reasoning cycle.

WO-REASON-006 composes the existing adaptive-reasoning components without
expanding authority, execution, tool use, external search, persistent memory,
or recursive reasoning.

Mode behavior:

DIRECT
    Return immediately without manufacturing candidate competition.

VERIFY
    Return immediately and expose that verification is required. This module
    does not perform external verification.

BRANCH
    Execute the bounded pipeline:
    candidate generation -> candidate evaluation -> convergence.

SEARCH
    Return immediately and expose that external search/research is required.
    This module does not perform network search or invoke tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from .candidates import CandidatePath, CandidatePathGenerator
from .convergence import ConvergenceController, ConvergenceResult
from .escalation import AdaptiveEscalationPolicy
from .evaluation import CandidateEvaluation, CandidateEvaluator
from .models import ReasoningMode, ReasoningRequest


@dataclass(frozen=True, slots=True)
class AdaptiveCycleResult:
    """Immutable result of one bounded adaptive reasoning cycle."""

    mode: ReasoningMode
    candidates: tuple[CandidatePath, ...]
    evaluations: tuple[CandidateEvaluation, ...]
    convergence: ConvergenceResult | None
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ReasoningMode):
            raise TypeError("mode must be a ReasoningMode")

        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates must be a tuple")

        if not isinstance(self.evaluations, tuple):
            raise TypeError("evaluations must be a tuple")

        if any(
            not isinstance(candidate, CandidatePath) for candidate in self.candidates
        ):
            raise TypeError("candidates must contain CandidatePath objects")

        if any(
            not isinstance(evaluation, CandidateEvaluation)
            for evaluation in self.evaluations
        ):
            raise TypeError("evaluations must contain CandidateEvaluation objects")

        if self.convergence is not None and not isinstance(
            self.convergence, ConvergenceResult
        ):
            raise TypeError("convergence must be a ConvergenceResult or None")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")

        if self.mode is ReasoningMode.BRANCH:
            if not self.candidates:
                raise ValueError("BRANCH result requires generated candidates")

            if not self.evaluations:
                raise ValueError("BRANCH result requires candidate evaluations")

            if self.convergence is None:
                raise ValueError("BRANCH result requires convergence")

            if len(self.candidates) != len(self.evaluations):
                raise ValueError("BRANCH candidates and evaluations must align")

        else:
            if self.candidates:
                raise ValueError("non-BRANCH result cannot expose candidate paths")

            if self.evaluations:
                raise ValueError("non-BRANCH result cannot expose evaluations")

            if self.convergence is not None:
                raise ValueError("non-BRANCH result cannot expose convergence")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "mode": self.mode.value,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "evaluations": [evaluation.to_dict() for evaluation in self.evaluations],
            "convergence": (
                self.convergence.to_dict() if self.convergence is not None else None
            ),
            "reason": self.reason,
        }


class AdaptiveReasoningCycle:
    """Coordinate one bounded pass through the adaptive reasoning stack."""

    DEFAULT_BRANCH_CANDIDATE_COUNT = 3

    def __init__(
        self,
        *,
        escalation_policy: AdaptiveEscalationPolicy | None = None,
        candidate_generator: CandidatePathGenerator | None = None,
        candidate_evaluator: CandidateEvaluator | None = None,
        convergence_controller: ConvergenceController | None = None,
        branch_candidate_count: int = DEFAULT_BRANCH_CANDIDATE_COUNT,
    ) -> None:
        if not isinstance(branch_candidate_count, int) or isinstance(
            branch_candidate_count, bool
        ):
            raise TypeError("branch_candidate_count must be an integer")

        if not (
            CandidatePathGenerator.MIN_CANDIDATES
            <= branch_candidate_count
            <= CandidatePathGenerator.MAX_CANDIDATES
        ):
            raise ValueError(
                "branch_candidate_count must remain inside "
                "CandidatePathGenerator bounds"
            )

        self._escalation_policy = (
            escalation_policy
            if escalation_policy is not None
            else AdaptiveEscalationPolicy()
        )

        self._candidate_generator = (
            candidate_generator
            if candidate_generator is not None
            else CandidatePathGenerator()
        )

        self._candidate_evaluator = (
            candidate_evaluator
            if candidate_evaluator is not None
            else CandidateEvaluator()
        )

        self._convergence_controller = (
            convergence_controller
            if convergence_controller is not None
            else ConvergenceController()
        )

        self._branch_candidate_count = branch_candidate_count

    def run(
        self,
        request: ReasoningRequest,
    ) -> AdaptiveCycleResult:
        """Run exactly one bounded adaptive reasoning cycle."""
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        decision = self._escalation_policy.select_mode(request)
        mode = decision.mode

        if mode is ReasoningMode.DIRECT:
            return AdaptiveCycleResult(
                mode=mode,
                candidates=(),
                evaluations=(),
                convergence=None,
                reason=(
                    "DIRECT selected; no branching, verification, "
                    "or external search is required by the escalation policy."
                ),
            )

        if mode is ReasoningMode.VERIFY:
            return AdaptiveCycleResult(
                mode=mode,
                candidates=(),
                evaluations=(),
                convergence=None,
                reason=(
                    "VERIFY selected; additional verification is required "
                    "outside this bounded reasoning cycle."
                ),
            )

        if mode is ReasoningMode.SEARCH:
            return AdaptiveCycleResult(
                mode=mode,
                candidates=(),
                evaluations=(),
                convergence=None,
                reason=(
                    "SEARCH selected; external research/search is required "
                    "outside this bounded reasoning cycle."
                ),
            )

        if mode is not ReasoningMode.BRANCH:
            raise ValueError(f"unsupported reasoning mode: {mode!r}")

        candidates = self._candidate_generator.generate(
            request,
            mode=mode,
            candidate_count=self._branch_candidate_count,
        )

        evaluations = self._candidate_evaluator.evaluate(
            request,
            candidates,
        )

        convergence = self._convergence_controller.converge(
            request,
            candidates,
            evaluations,
        )

        return AdaptiveCycleResult(
            mode=mode,
            candidates=candidates,
            evaluations=evaluations,
            convergence=convergence,
            reason=(
                "BRANCH selected; bounded candidate generation, "
                "evaluation, and convergence completed."
            ),
        )
