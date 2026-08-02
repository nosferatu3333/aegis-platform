from datetime import UTC, datetime, timedelta

from aegis_core.contracts import (
    AuthorityDenial,
    AuthorityGrant,
    AuthorityRequirement,
    AuthoritySource,
    BoundedPlan,
    BoundedPlanStep,
    ConsequenceClass,
    RevocationRecord,
    RevocationState,
)
from aegis_os.execution.authority_adapter import AuthorityGatedExecutionAdapter
from aegis_os.execution.authority_gate import AuthorityGate, AuthorityGateOutcome

NOW = datetime(2026, 8, 2, 15, 0, tzinfo=UTC)


def plan(requirement=AuthorityRequirement.APPROVAL_REQUIRED, consequence=ConsequenceClass.LOW):
    return BoundedPlan(
        plan_id="pln_1234567890abcdef",
        request_id="req_1234567890abcdef",
        interpretation_id="int_1234567890abcdef",
        selection_id="sel_1234567890abcdef",
        objective="Perform bounded work",
        consequence_class=consequence,
        steps=(
            BoundedPlanStep(
                step_id="stp_1234567890abcdef",
                sequence=1,
                summary="Apply bounded change",
                completion_criteria=("Evidence confirms the bounded change.",),
                authority_requirement=requirement,
            ),
        ),
        expected_evidence=("Completion evidence",),
        stop_conditions=("Stop on authority or scope change.",) if consequence is not ConsequenceClass.LOW else (),
    )


def gate():
    return AuthorityGate(clock=lambda: NOW)


def grant_for(target_plan, *, scope=None, ceiling=ConsequenceClass.HIGH, expires=None):
    required = gate().required_scope(target_plan, target_plan.steps[0])
    return AuthorityGrant(
        grant_id="grt_1234567890abcdef",
        subject_type="bounded_plan",
        subject_id=target_plan.plan_id,
        grantee_id="svc_aegis_platform",
        granted_scope=tuple(scope or required),
        consequence_ceiling=ceiling,
        issued_by="usr_1234567890abcdef",
        source=AuthoritySource.SYSTEM_POLICY,
        issued_at=NOW - timedelta(minutes=2),
        valid_from=NOW - timedelta(minutes=1),
        expires_at=expires,
    )


def test_none_requirement_allows_and_builds_execution_request():
    result = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=plan(AuthorityRequirement.NONE),
        selected_agent="Execution Agent",
    )

    assert result.ready is True
    assert result.decisions[0].outcome is AuthorityGateOutcome.ALLOW
    assert result.execution_request.metadata["canonical_plan_id"] == result.plan_id


def test_missing_grant_pauses_without_creating_execution_request():
    result = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=plan(), selected_agent="Execution Agent"
    )

    assert result.paused is True
    assert result.execution_request is None
    assert result.decisions[0].audit_event.outcome == "pause"


def test_valid_full_scope_grant_allows_execution():
    target = plan(consequence=ConsequenceClass.MODERATE)
    authority = grant_for(target)

    result = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=target,
        selected_agent="Execution Agent",
        grants=(authority,),
    )

    assert result.ready is True
    assert result.decisions[0].grant_id == authority.grant_id
    assert result.execution_request.metadata["authority_grant_ids"] == [authority.grant_id]


def test_expired_or_under_scoped_grants_do_not_authorize():
    target = plan()
    expired = grant_for(target, expires=NOW - timedelta(seconds=1))
    result = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=target, selected_agent="Execution Agent", grants=(expired,)
    )
    assert result.paused is True

    partial = grant_for(target, scope=(f"execute:plan:{target.plan_id}",))
    result = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=target, selected_agent="Execution Agent", grants=(partial,)
    )
    assert result.paused is True


def test_explicit_denial_overrides_valid_grant():
    target = plan()
    authority = grant_for(target)
    denial = AuthorityDenial(
        denial_id="dny_1234567890abcdef",
        subject_type="bounded_plan_step",
        subject_id=target.steps[0].step_id,
        denied_scope=(f"execute:step:{target.steps[0].step_id}",),
        denied_by="usr_1234567890abcdef",
        reason="Change window closed.",
        denied_at=NOW,
    )

    result = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=target,
        selected_agent="Execution Agent",
        grants=(authority,),
        denials=(denial,),
    )

    assert result.denied is True
    assert result.execution_request is None


def test_confirmed_revocation_blocks_grant():
    target = plan()
    authority = grant_for(target)
    revocation = RevocationRecord(
        record_id="rvr_1234567890abcdef",
        revocation_id="rvk_1234567890abcdef",
        grant_id=authority.grant_id,
        revoked_scope=(f"execute:step:{target.steps[0].step_id}",),
        state=RevocationState.CONFIRMED,
        reconciled_by="svc_aegis_platform",
        evidence_ids=("ev_1234567890abcdef",),
        affected_subjects=(target.steps[0].step_id,),
        reconciled_at=NOW,
    )

    result = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=target,
        selected_agent="Execution Agent",
        grants=(authority,),
        revocations=(revocation,),
    )

    assert result.paused is True
    assert result.execution_request is None


def test_prohibited_denies_and_unknown_pauses():
    prohibited = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=plan(AuthorityRequirement.PROHIBITED),
        selected_agent="Execution Agent",
    )
    unknown = AuthorityGatedExecutionAdapter(gate=gate()).prepare(
        plan=plan(AuthorityRequirement.UNKNOWN),
        selected_agent="Execution Agent",
    )

    assert prohibited.denied is True
    assert unknown.paused is True
