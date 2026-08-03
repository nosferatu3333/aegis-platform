"""Authority gate for bounded Platform execution.

The gate evaluates every canonical plan step before any execution request is
created.  It never creates authority, infers approval, or mutates Core records.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Callable, Iterable

from aegis_core.contracts import (
    AuthorityAuditEvent,
    AuthorityDenial,
    AuthorityGrant,
    AuthorityRequirement,
    BoundedPlan,
    BoundedPlanStep,
    ConsequenceClass,
    RevocationRecord,
    RevocationState,
)


class AuthorityGateOutcome(StrEnum):
    ALLOW = "allow"
    PAUSE = "pause"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class AuthorityGateDecision:
    plan_id: str
    step_id: str
    sequence: int
    requested_scope: tuple[str, ...]
    outcome: AuthorityGateOutcome
    reason: str
    authority_requirement: AuthorityRequirement
    grant_id: str | None
    audit_event: AuthorityAuditEvent

    @property
    def authorizes_execution(self) -> bool:
        return self.outcome is AuthorityGateOutcome.ALLOW


_CONSEQUENCE_RANK = {
    ConsequenceClass.LOW: 0,
    ConsequenceClass.MODERATE: 1,
    ConsequenceClass.HIGH: 2,
    ConsequenceClass.CRITICAL: 3,
}


class AuthorityGate:
    """Evaluate immutable Core authority records against a bounded plan."""

    def __init__(
        self,
        *,
        actor_id: str = "svc_aegis_platform",
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.actor_id = actor_id
        self._clock = clock or (lambda: datetime.now(UTC))

    def evaluate_plan(
        self,
        plan: BoundedPlan,
        *,
        grants: Iterable[AuthorityGrant] = (),
        denials: Iterable[AuthorityDenial] = (),
        revocations: Iterable[RevocationRecord] = (),
    ) -> tuple[AuthorityGateDecision, ...]:
        observed_at = self._clock()
        grant_records = tuple(grants)
        denial_records = tuple(denials)
        revocation_records = tuple(revocations)
        return tuple(
            self.evaluate_step(
                plan,
                step,
                grants=grant_records,
                denials=denial_records,
                revocations=revocation_records,
                observed_at=observed_at,
            )
            for step in plan.steps
        )

    def evaluate_step(
        self,
        plan: BoundedPlan,
        step: BoundedPlanStep,
        *,
        grants: Iterable[AuthorityGrant] = (),
        denials: Iterable[AuthorityDenial] = (),
        revocations: Iterable[RevocationRecord] = (),
        observed_at: datetime | None = None,
    ) -> AuthorityGateDecision:
        now = observed_at or self._clock()
        scope = self.required_scope(plan, step)
        requirement = step.authority_requirement

        matching_denial = self._matching_denial(plan, step, scope, tuple(denials))
        if matching_denial is not None:
            return self._decision(
                plan,
                step,
                scope,
                AuthorityGateOutcome.DENY,
                f"Explicit authority denial {matching_denial.denial_id} covers this action.",
                authority_reference=matching_denial.denial_id,
            )

        if requirement is AuthorityRequirement.PROHIBITED:
            return self._decision(
                plan,
                step,
                scope,
                AuthorityGateOutcome.DENY,
                "The canonical plan marks this action as prohibited.",
                authority_reference="requirement:prohibited",
            )
        if requirement is AuthorityRequirement.UNKNOWN:
            return self._decision(
                plan,
                step,
                scope,
                AuthorityGateOutcome.PAUSE,
                "Authority is unknown and must be resolved before execution.",
                authority_reference="requirement:unknown",
            )
        if requirement is AuthorityRequirement.NONE:
            return self._decision(
                plan,
                step,
                scope,
                AuthorityGateOutcome.ALLOW,
                "The canonical plan requires no additional authority for this action.",
                authority_reference="requirement:none",
            )

        effective = [
            grant
            for grant in grants
            if self._grant_matches(plan, step, scope, grant, now)
            and not self._is_revoked(grant, scope, tuple(revocations))
        ]
        if not effective:
            return self._decision(
                plan,
                step,
                scope,
                AuthorityGateOutcome.PAUSE,
                "No effective authority grant covers the full action scope and consequence class.",
                authority_reference="grant:missing",
            )

        grant = sorted(effective, key=lambda item: item.grant_id)[0]
        return self._decision(
            plan,
            step,
            scope,
            AuthorityGateOutcome.ALLOW,
            f"Authority grant {grant.grant_id} covers the action.",
            grant_id=grant.grant_id,
            authority_reference=grant.grant_id,
        )

    @staticmethod
    def required_scope(plan: BoundedPlan, step: BoundedPlanStep) -> tuple[str, ...]:
        return (
            f"execute:plan:{plan.plan_id}",
            f"execute:step:{step.step_id}",
        )

    @staticmethod
    def _subject_matches(
        plan: BoundedPlan,
        step: BoundedPlanStep,
        subject_id: str,
    ) -> bool:
        return subject_id in {plan.plan_id, step.step_id, plan.request_id}

    def _matching_denial(
        self,
        plan: BoundedPlan,
        step: BoundedPlanStep,
        scope: tuple[str, ...],
        denials: tuple[AuthorityDenial, ...],
    ) -> AuthorityDenial | None:
        for denial in denials:
            overlaps_scope = bool(set(scope).intersection(denial.denied_scope))
            if self._subject_matches(plan, step, denial.subject_id) and overlaps_scope:
                return denial
        return None

    def _grant_matches(
        self,
        plan: BoundedPlan,
        step: BoundedPlanStep,
        scope: tuple[str, ...],
        grant: AuthorityGrant,
        observed_at: datetime,
    ) -> bool:
        return (
            self._subject_matches(plan, step, grant.subject_id)
            and grant.grantee_id == self.actor_id
            and grant.is_effective_at(observed_at)
            and set(scope).issubset(grant.granted_scope)
            and _CONSEQUENCE_RANK[grant.consequence_ceiling]
            >= _CONSEQUENCE_RANK[plan.consequence_class]
        )

    @staticmethod
    def _is_revoked(
        grant: AuthorityGrant,
        scope: tuple[str, ...],
        revocations: tuple[RevocationRecord, ...],
    ) -> bool:
        return any(
            record.grant_id == grant.grant_id
            and record.state is RevocationState.CONFIRMED
            and bool(set(scope).intersection(record.revoked_scope))
            for record in revocations
        )

    def _decision(
        self,
        plan: BoundedPlan,
        step: BoundedPlanStep,
        scope: tuple[str, ...],
        outcome: AuthorityGateOutcome,
        reason: str,
        *,
        authority_reference: str,
        grant_id: str | None = None,
    ) -> AuthorityGateDecision:
        audit = AuthorityAuditEvent(
            action="evaluate_execution_authority",
            actor_id=self.actor_id,
            subject_type="bounded_plan_step",
            subject_id=step.step_id,
            outcome=outcome.value,
            authority_reference=authority_reference,
            details={
                "plan_id": plan.plan_id,
                "request_id": plan.request_id,
                "sequence": step.sequence,
                "requested_scope": list(scope),
                "reason": reason,
            },
            occurred_at=self._clock(),
        )
        return AuthorityGateDecision(
            plan_id=plan.plan_id,
            step_id=step.step_id,
            sequence=step.sequence,
            requested_scope=scope,
            outcome=outcome,
            reason=reason,
            authority_requirement=step.authority_requirement,
            grant_id=grant_id,
            audit_event=audit,
        )
