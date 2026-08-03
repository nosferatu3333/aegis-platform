"""Adapter from a canonical bounded plan to an authority-gated execution request."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from aegis_core.contracts import (
    AuthorityDenial,
    AuthorityGrant,
    BoundedPlan,
    RevocationRecord,
)

from aegis_os.execution.authority_gate import (
    AuthorityGate,
    AuthorityGateDecision,
    AuthorityGateOutcome,
)
from aegis_os.execution.models import ExecutionRequest


@dataclass(frozen=True, slots=True)
class AuthorityGatedExecution:
    plan_id: str
    request_id: str
    decisions: tuple[AuthorityGateDecision, ...]
    execution_request: ExecutionRequest | None

    @property
    def ready(self) -> bool:
        return self.execution_request is not None

    @property
    def denied(self) -> bool:
        return any(item.outcome is AuthorityGateOutcome.DENY for item in self.decisions)

    @property
    def paused(self) -> bool:
        return any(item.outcome is AuthorityGateOutcome.PAUSE for item in self.decisions)


class AuthorityGatedExecutionAdapter:
    """Prepare execution only when every bounded step is explicitly allowed."""

    def __init__(self, *, gate: AuthorityGate | None = None) -> None:
        self.gate = gate or AuthorityGate()

    def prepare(
        self,
        *,
        plan: BoundedPlan,
        selected_agent: str,
        grants: Iterable[AuthorityGrant] = (),
        denials: Iterable[AuthorityDenial] = (),
        revocations: Iterable[RevocationRecord] = (),
        capability_id: str | None = None,
        required_capabilities: Iterable[str] = (),
    ) -> AuthorityGatedExecution:
        clean_agent = selected_agent.strip()
        if not clean_agent:
            raise ValueError("selected_agent must not be empty")

        decisions = self.gate.evaluate_plan(
            plan,
            grants=grants,
            denials=denials,
            revocations=revocations,
        )
        if not all(item.authorizes_execution for item in decisions):
            return AuthorityGatedExecution(
                plan_id=plan.plan_id,
                request_id=plan.request_id,
                decisions=decisions,
                execution_request=None,
            )

        request = ExecutionRequest(
            request_id=plan.request_id,
            mission=plan.objective,
            selected_agent=clean_agent,
            required_capabilities=list(required_capabilities),
            workflow_steps=[
                {
                    "order": step.sequence,
                    "title": step.summary,
                    "description": step.summary,
                    "step_id": step.step_id,
                    "completion_criteria": list(step.completion_criteria),
                    "capability_id": capability_id,
                }
                for step in plan.steps
            ],
            constraints=list(plan.stop_conditions),
            permissions=[
                scope
                for decision in decisions
                for scope in decision.requested_scope
            ],
            metadata={
                "canonical_plan_id": plan.plan_id,
                "canonical_selection_id": plan.selection_id,
                "authority_gate": "all_steps_allowed",
                "canonical_expected_evidence": list(plan.expected_evidence),
                "authority_audit_event_ids": [
                    decision.audit_event.event_id for decision in decisions
                ],
                "authority_grant_ids": [
                    decision.grant_id
                    for decision in decisions
                    if decision.grant_id is not None
                ],
            },
        )
        return AuthorityGatedExecution(
            plan_id=plan.plan_id,
            request_id=plan.request_id,
            decisions=decisions,
            execution_request=request,
        )
