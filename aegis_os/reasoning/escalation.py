"""Deterministic escalation policy for bounded AEGIS reasoning.

WO-REASON-002 selects cognitive effort only.

It does not:
- grant authority,
- grant execution permission,
- perform verification,
- perform external search,
- generate candidate paths,
- evaluate candidates,
- perform convergence,
- mutate persistent memory.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import ReasoningMode, ReasoningRequest


@dataclass(frozen=True, slots=True)
class EscalationDecision:
    """Deterministic reasoning-mode selection result."""

    mode: ReasoningMode
    reason: str


class AdaptiveEscalationPolicy:
    """Select the minimum sufficient reasoning mode for one bounded request."""

    _SEARCH_MARKERS = (
        "external evidence",
        "external source",
        "current information",
        "current data",
        "web research",
        "research required",
        "source verification",
    )

    _BRANCH_MARKERS = (
        "multiple approaches",
        "multiple options",
        "competing approaches",
        "competing options",
        "tradeoff",
        "trade-off",
        "ambiguous objective",
        "cross-domain",
    )

    def select_mode(self, request: ReasoningRequest) -> EscalationDecision:
        """Return the minimum sufficient cognitive-effort mode.

        Selection order is SEARCH -> BRANCH -> VERIFY -> DIRECT because the
        stronger modes subsume the weaker policy conditions.

        This function selects reasoning effort only. It never performs the
        operation implied by the selected mode.
        """
        if not isinstance(request, ReasoningRequest):
            raise TypeError("request must be a ReasoningRequest")

        signals = self._normalized_signals(request)

        if self._requires_search(request, signals):
            return EscalationDecision(
                mode=ReasoningMode.SEARCH,
                reason=(
                    "Request signals require external evidence acquisition "
                    "and the reasoning budget permits search-level deliberation."
                ),
            )

        if self._requires_branch(request, signals):
            return EscalationDecision(
                mode=ReasoningMode.BRANCH,
                reason=(
                    "Request complexity or ambiguity warrants multiple "
                    "competing reasoning paths."
                ),
            )

        if self._requires_verify(request):
            return EscalationDecision(
                mode=ReasoningMode.VERIFY,
                reason=(
                    "Uncertainty or risk warrants verification before "
                    "forming a recommendation."
                ),
            )

        return EscalationDecision(
            mode=ReasoningMode.DIRECT,
            reason=(
                "No stronger escalation trigger is present; bounded direct "
                "reasoning is sufficient."
            ),
        )

    @staticmethod
    def _normalized_signals(request: ReasoningRequest) -> tuple[str, ...]:
        values = (
            *request.uncertainty_signals,
            *request.risk_signals,
            *request.constraints,
        )
        return tuple(value.strip().lower() for value in values)

    def _requires_search(
        self,
        request: ReasoningRequest,
        signals: tuple[str, ...],
    ) -> bool:
        if request.budget < 3:
            return False

        return any(
            marker in signal for signal in signals for marker in self._SEARCH_MARKERS
        )

    def _requires_branch(
        self,
        request: ReasoningRequest,
        signals: tuple[str, ...],
    ) -> bool:
        marker_trigger = any(
            marker in signal for signal in signals for marker in self._BRANCH_MARKERS
        )

        structural_trigger = (
            request.requested_depth >= 2
            and request.budget >= 2
            and (len(request.uncertainty_signals) >= 2 or len(request.constraints) >= 2)
        )

        return marker_trigger or structural_trigger

    @staticmethod
    def _requires_verify(request: ReasoningRequest) -> bool:
        return bool(request.uncertainty_signals or request.risk_signals)
