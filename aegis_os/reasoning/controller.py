"""Controller boundary for AEGIS adaptive reasoning.

WO-REASON-001 defines the interface only.

Adaptive mode-selection policy is intentionally deferred to WO-REASON-002.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ReasoningMode, ReasoningRequest, ReasoningResult


class ReasoningController(ABC):
    """Interface for bounded reasoning-control implementations."""

    @abstractmethod
    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        """Process one bounded reasoning request.

        Implementations must not grant authority, execute tools, or perform
        external side effects.
        """


class StaticReasoningController(ReasoningController):
    """Minimal deterministic controller used to prove the interface contract.

    This controller does not implement adaptive escalation.  The selected mode
    is supplied explicitly at construction time.
    """

    def __init__(
        self,
        *,
        mode: ReasoningMode = ReasoningMode.DIRECT,
        selection_reason: str = "Static contract controller.",
    ) -> None:
        if not isinstance(mode, ReasoningMode):
            raise TypeError("mode must be a ReasoningMode")

        if not isinstance(selection_reason, str) or not selection_reason.strip():
            raise ValueError("selection_reason must be a non-empty string")

        self._mode = mode
        self._selection_reason = selection_reason.strip()

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        return ReasoningResult(
            reasoning_request_id=request.reasoning_request_id,
            mode=self._mode,
            summary="Reasoning contract processed without adaptive escalation.",
            selection_reason=self._selection_reason,
            uncertainty_signals=request.uncertainty_signals,
            evidence_requirements=(),
            alternatives_preserved=(),
            complete=True,
        )
