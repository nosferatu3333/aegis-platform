from datetime import UTC, datetime, timedelta

from aegis_core.contracts import (
    AuthorityDenial,
    AuthorityGrant,
    AuthorityRequirement,
    AuthoritySource,
    CapabilitySelection,
    ConsequenceClass,
    EligibilityState,
    OperationalState,
)
from aegis_os.core.governed_runtime import (
    GovernedRuntime,
    GovernedRuntimeRequest,
    GovernedRuntimeStatus,
)
from aegis_os.execution.authority_adapter import AuthorityGatedExecutionAdapter
from aegis_os.execution.authority_gate import AuthorityGate
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.reconciliation import ExecutionResultReconciler
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

NOW = datetime(2026, 8, 2, 17, 0, tzinfo=UTC)
REQ = "req_1234567890abcdef"
INT = "int_1234567890abcdef"
SEL = "sel_1234567890abcdef"


class UnusedSelector:
    def select(self, task, **context):
        raise AssertionError("governed runtime must consume canonical selection")


def selection(authority=AuthorityRequirement.NONE):
    return CapabilitySelection(
        request_id=REQ,
        capability_id="cap_iterative_ai_development",
        capability_version="0.2.0",
        eligibility=EligibilityState.ELIGIBLE,
        rationale="Canonical capability selected by OPS.",
        health_state=OperationalState.HEALTHY,
        authority_requirement=authority,
        selection_id=SEL,
    )


def runtime():
    return GovernedRuntime(
        pipeline=CognitiveRequestPipeline(capability_selector=UnusedSelector()),
        authority_adapter=AuthorityGatedExecutionAdapter(
            gate=AuthorityGate(clock=lambda: NOW)
        ),
        execution_engine=ExecutionEngine(clock=lambda: NOW),
        reconciler=ExecutionResultReconciler(clock=lambda: NOW),
    )


def request(*, authority=AuthorityRequirement.NONE, execute=True, grants=(), denials=(), workflow=None):
    return GovernedRuntimeRequest(
        task="Perform bounded governed work",
        interpretation_id=INT,
        selection=selection(authority),
        selected_agent="Execution Agent",
        workflow_definition=workflow or ["Prepare bounded work", "Verify evidence"],
        execute=execute,
        grants=tuple(grants),
        denials=tuple(denials),
    )


def test_analysis_only_stops_before_authority_and_execution():
    result = runtime().process(request(execute=False))

    assert result.status is GovernedRuntimeStatus.ANALYZED
    assert result.analysis.canonical_plan is not None
    assert result.authority is None
    assert result.execution is None
    assert result.reconciliation is None


def test_no_authority_requirement_completes_full_governed_pipeline():
    result = runtime().process(request())

    assert result.status is GovernedRuntimeStatus.COMPLETED
    assert result.authority.ready is True
    assert result.execution is not None
    assert result.validation is not None
    assert result.reconciliation is not None
    assert result.reconciliation.trace.is_complete_result_trace is True
    assert result.reconciliation.result.request_id == REQ


def test_missing_required_grant_pauses_without_execution():
    result = runtime().process(
        request(authority=AuthorityRequirement.APPROVAL_REQUIRED)
    )

    assert result.status is GovernedRuntimeStatus.PAUSED
    assert result.authority.paused is True
    assert result.execution_performed is False
    assert result.execution is None
    assert result.reconciliation is None


def test_explicit_denial_stops_pipeline_before_execution():
    analyzed = runtime().process(request(execute=False))
    plan = analyzed.analysis.canonical_plan
    denial = AuthorityDenial(
        subject_type="bounded_plan",
        subject_id=plan.plan_id,
        denied_scope=(f"execute:step:{plan.steps[0].step_id}",),
        denied_by="usr_1234567890abcdef",
        reason="Execution is not approved.",
        denied_at=NOW,
    )
    rt = runtime()
    rt.pipeline.process_selection = lambda **kwargs: analyzed.analysis
    result = rt.process(request(denials=(denial,)))

    assert result.status is GovernedRuntimeStatus.DENIED
    assert result.authority.denied is True
    assert result.execution is None


def test_valid_grant_allows_required_authority_pipeline():
    analyzed = runtime().process(
        request(authority=AuthorityRequirement.APPROVAL_REQUIRED, execute=False)
    )
    plan = analyzed.analysis.canonical_plan
    scopes = tuple(
        scope
        for step in plan.steps
        for scope in (
            f"execute:plan:{plan.plan_id}",
            f"execute:step:{step.step_id}",
        )
    )
    grant = AuthorityGrant(
        subject_type="bounded_plan",
        subject_id=plan.plan_id,
        grantee_id="svc_aegis_platform",
        granted_scope=tuple(dict.fromkeys(scopes)),
        consequence_ceiling=ConsequenceClass.HIGH,
        issued_by="usr_1234567890abcdef",
        source=AuthoritySource.SYSTEM_POLICY,
        issued_at=NOW - timedelta(minutes=2),
        valid_from=NOW - timedelta(minutes=1),
    )
    # Reuse the exact canonical plan by forcing deterministic IDs is outside this
    # request contract, so exercise the gate through a runtime with a cached plan.
    cached = analyzed.analysis
    rt = runtime()
    rt.pipeline.process_selection = lambda **kwargs: cached
    result = rt.process(
        request(authority=AuthorityRequirement.APPROVAL_REQUIRED, grants=(grant,))
    )

    assert result.status is GovernedRuntimeStatus.COMPLETED
    assert result.authority.ready is True
    assert result.reconciliation is not None


def test_failed_execution_is_reconciled_and_never_reported_complete():
    result = runtime().process(
        request(workflow=["Prepare", "[simulate-failure]", "Never run"])
    )

    assert result.status is GovernedRuntimeStatus.FAILED
    assert result.reconciliation.outcome.value == "failed"
    assert result.reconciliation.result.completion_state.value == "failed"


def test_serialized_result_exposes_all_governance_stages():
    payload = runtime().process(request()).to_dict()

    assert payload["status"] == "completed"
    assert payload["analysis"]["canonical_plan"] is not None
    assert payload["authority"]["ready"] is True
    assert payload["execution"]["status"] == "completed"
    assert payload["validation"]["status"] == "passed"
    assert payload["reconciliation"]["result_id"].startswith("res_")
