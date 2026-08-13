"""Synchronous composition for one bounded SYSTEM cognitive cycle."""

from __future__ import annotations

from collections.abc import Iterable

from aegis_os.intent import (
    IntentInterpretation,
    IntentInterpreter,
    OutcomeModel,
    OutcomeModeler,
)
from aegis_os.project import ProjectState, ProjectStateManager
from aegis_os.reasoning import (
    AdaptiveCycleResult,
    AdaptiveReasoningCycle,
    ConvergenceStatus,
    ReasoningMode,
    ReasoningRequest,
)

from .models import (
    CognitiveCycleRequest,
    CognitiveCycleResult,
    CycleDisposition,
    NextInteraction,
    ProjectContextMode,
    ReasoningHandoffResult,
)


class CognitiveCycle:
    """Compose one explicit, synchronous, bounded cognitive cycle."""

    def __init__(
        self,
        *,
        intent_interpreter: IntentInterpreter | None = None,
        outcome_modeler: OutcomeModeler | None = None,
        project_state_manager: ProjectStateManager | None = None,
        reasoning_cycle: AdaptiveReasoningCycle | None = None,
    ) -> None:
        self._intent_interpreter = (
            intent_interpreter
            if intent_interpreter is not None
            else IntentInterpreter()
        )
        self._outcome_modeler = (
            outcome_modeler if outcome_modeler is not None else OutcomeModeler()
        )
        self._project_state_manager = (
            project_state_manager
            if project_state_manager is not None
            else ProjectStateManager()
        )
        self._reasoning_cycle = (
            reasoning_cycle if reasoning_cycle is not None else AdaptiveReasoningCycle()
        )

    def run(self, request: CognitiveCycleRequest) -> CognitiveCycleResult:
        """Run exactly one cycle without authority, execution, or persistence."""
        if not isinstance(request, CognitiveCycleRequest):
            raise TypeError("request must be a CognitiveCycleRequest")

        interpretation = self._intent_interpreter.interpret(request.intent_request)
        if not isinstance(interpretation, IntentInterpretation):
            raise TypeError("intent interpreter must return an IntentInterpretation")

        if interpretation.clarification_required:
            return CognitiveCycleResult(
                cycle_id=request.cycle_id,
                intent_ref=request.intent_ref,
                disposition=CycleDisposition.CLARIFICATION_REQUIRED,
                interpretation=interpretation,
                clarification_required=True,
                clarification_questions=interpretation.clarification_questions,
                outcome=None,
                project_context_mode=request.project_context.mode,
                current_project_state=None,
                reasoning_request=None,
                reasoning=None,
                next_interaction=NextInteraction.USER_CLARIFICATION,
            )

        outcome = self._outcome_modeler.model(
            interpretation,
            intent_ref=request.intent_ref,
            success_conditions=request.success_conditions,
            inferred_constraints=interpretation.inferred_constraints,
            outcome_uncertainties=request.outcome_uncertainties,
        )
        if not isinstance(outcome, OutcomeModel):
            raise TypeError("outcome modeler must return an OutcomeModel")

        project_state = self._route_project(request, outcome)
        project_context_ref = (
            request.cycle_id if project_state is None else project_state.project_id
        )

        reasoning_request = ReasoningRequest(
            reasoning_request_id=request.reasoning_request_id,
            intent_ref=request.intent_ref,
            outcome_ref=request.intent_ref,
            project_context_ref=project_context_ref,
            uncertainty_signals=_normalized_stable_unique(
                outcome.outcome_uncertainties,
                project_state.unresolved_issues if project_state else (),
            ),
            risk_signals=request.risk_signals,
            constraints=_normalized_stable_unique(
                outcome.explicit_constraints,
                outcome.inferred_constraints,
                project_state.active_constraints if project_state else (),
            ),
            requested_depth=request.requested_depth,
            budget=request.budget,
        )

        adaptive_result = self._reasoning_cycle.run(reasoning_request)
        if not isinstance(adaptive_result, AdaptiveCycleResult):
            raise TypeError("reasoning cycle must return an AdaptiveCycleResult")

        disposition, next_interaction = _map_reasoning_result(
            adaptive_result,
            project_state=project_state,
        )

        return CognitiveCycleResult(
            cycle_id=request.cycle_id,
            intent_ref=request.intent_ref,
            disposition=disposition,
            interpretation=interpretation,
            clarification_required=False,
            clarification_questions=interpretation.clarification_questions,
            outcome=outcome,
            project_context_mode=request.project_context.mode,
            current_project_state=project_state,
            reasoning_request=reasoning_request,
            reasoning=ReasoningHandoffResult(
                reasoning_request_id=reasoning_request.reasoning_request_id,
                adaptive_result=adaptive_result,
            ),
            next_interaction=next_interaction,
        )

    def _route_project(
        self,
        request: CognitiveCycleRequest,
        outcome: OutcomeModel,
    ) -> ProjectState | None:
        context = request.project_context

        if context.mode is ProjectContextMode.TRANSIENT:
            return None
        if context.mode is ProjectContextMode.CREATE_NEW:
            if context.new_project_id is None:
                raise ValueError("CREATE_NEW context is missing new_project_id")
            project_state = self._project_state_manager.create(
                outcome,
                project_id=context.new_project_id,
            )
            if not isinstance(project_state, ProjectState):
                raise TypeError("project state manager must return a ProjectState")
            return project_state
        if context.existing_state is None:
            raise ValueError("EXISTING context is missing existing_state")
        return context.existing_state


def _normalized_stable_unique(*groups: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip() for group in groups for item in group))


def _map_reasoning_result(
    result: AdaptiveCycleResult,
    *,
    project_state: ProjectState | None,
) -> tuple[CycleDisposition, NextInteraction]:
    if result.mode is ReasoningMode.DIRECT:
        disposition = (
            CycleDisposition.TRANSIENT_REASONING_RESULT
            if project_state is None
            else CycleDisposition.PROJECT_REASONING_RESULT
        )
        return disposition, NextInteraction.NONE

    if result.mode is ReasoningMode.VERIFY:
        return (
            CycleDisposition.VERIFY_REQUIRED_SIGNAL,
            NextInteraction.EVIDENCE_COORDINATION,
        )

    if result.mode is ReasoningMode.SEARCH:
        return (
            CycleDisposition.SEARCH_REQUIRED_SIGNAL,
            NextInteraction.SEARCH_COORDINATION,
        )

    if result.mode is not ReasoningMode.BRANCH or result.convergence is None:
        raise ValueError("unsupported adaptive reasoning result")

    if result.convergence.status is ConvergenceStatus.RESOLVED:
        disposition = (
            CycleDisposition.TRANSIENT_REASONING_RESULT
            if project_state is None
            else CycleDisposition.PROJECT_REASONING_RESULT
        )
        return disposition, NextInteraction.USER_DECISION

    if result.convergence.status is ConvergenceStatus.TIED:
        return CycleDisposition.REASONING_TIED, NextInteraction.USER_DECISION

    if result.convergence.status is ConvergenceStatus.INSUFFICIENT:
        return (
            CycleDisposition.REASONING_INSUFFICIENT,
            NextInteraction.EVIDENCE_COORDINATION,
        )

    raise ValueError("unsupported convergence status")
