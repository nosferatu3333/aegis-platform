"""End-to-end governed runtime pipeline for the AEGIS MVP.

This module composes the canonical selection, bounded planning, authority,
execution, conformance, and reconciliation boundaries without weakening any
individual contract.  It does not infer authority or claim real-world effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aegis_core.contracts import (
    AuthorityDenial,
    AuthorityGrant,
    CapabilitySelection,
    RevocationRecord,
)

from aegis_os.execution.authority_adapter import (
    AuthorityGatedExecution,
    AuthorityGatedExecutionAdapter,
)
from aegis_os.execution.conformance import (
    ConformanceStatus,
    ExecutionConformanceResult,
    ExecutionConformanceValidator,
)
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import ExecutionReceipt, ExecutionStatus
from aegis_os.execution.reconciliation import (
    ExecutionResultReconciler,
    ReconciledExecutionResult,
)
from aegis_os.pipeline.models import CognitiveRequestResult, PipelineStatus
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

GOVERNED_RUNTIME_SCHEMA_VERSION = "1.0"


class GovernedRuntimeStatus(StrEnum):
    ANALYZED = "analyzed"
    PAUSED = "paused"
    DENIED = "denied"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFORMANCE_FAILED = "conformance_failed"


@dataclass(frozen=True, slots=True)
class GovernedRuntimeRequest:
    task: str
    interpretation_id: str
    selection: CapabilitySelection
    selected_agent: str
    workflow_definition: Any = None
    execute: bool = False
    grants: tuple[AuthorityGrant, ...] = ()
    denials: tuple[AuthorityDenial, ...] = ()
    revocations: tuple[RevocationRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task must not be empty")
        if not self.interpretation_id.startswith("int_"):
            raise ValueError("interpretation_id must be canonical")
        if not self.selected_agent.strip():
            raise ValueError("selected_agent must not be empty")


@dataclass(frozen=True, slots=True)
class GovernedRuntimeResult:
    request_id: str
    status: GovernedRuntimeStatus
    analysis: CognitiveRequestResult
    authority: AuthorityGatedExecution | None = None
    execution: ExecutionReceipt | None = None
    validation: ExecutionConformanceResult | None = None
    reconciliation: ReconciledExecutionResult | None = None
    execution_requested: bool = False
    execution_performed: bool = False
    schema_version: str = GOVERNED_RUNTIME_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.analysis.status is not PipelineStatus.READY:
            raise ValueError("governed runtime requires READY analysis")
        plan = self.analysis.canonical_plan
        if plan is None:
            raise ValueError("governed runtime requires a canonical bounded plan")
        if self.request_id != plan.request_id:
            raise ValueError("request_id must match the canonical plan")
        if self.execution is not None and not self.execution_performed:
            raise ValueError("execution receipt requires execution_performed=True")
        if self.reconciliation is not None and self.execution is None:
            raise ValueError("reconciliation requires an execution receipt")
        if self.validation is not None and self.execution is None:
            raise ValueError("validation requires an execution receipt")
        if self.status in {GovernedRuntimeStatus.PAUSED, GovernedRuntimeStatus.DENIED}:
            if self.authority is None or self.authority.ready:
                raise ValueError("paused or denied results require a blocking authority result")
            if self.execution is not None:
                raise ValueError("blocked authority cannot include execution")
        if self.status is GovernedRuntimeStatus.COMPLETED:
            if self.execution is None or self.execution.status is not ExecutionStatus.COMPLETED:
                raise ValueError("completed status requires a completed execution receipt")
            if self.reconciliation is None:
                raise ValueError("completed status requires reconciliation")

    def to_dict(self) -> dict[str, Any]:
        authority_payload = None
        if self.authority is not None:
            authority_payload = {
                "plan_id": self.authority.plan_id,
                "request_id": self.authority.request_id,
                "ready": self.authority.ready,
                "paused": self.authority.paused,
                "denied": self.authority.denied,
                "decisions": [
                    {
                        "step_id": item.step_id,
                        "sequence": item.sequence,
                        "outcome": item.outcome.value,
                        "reason": item.reason,
                        "requested_scope": list(item.requested_scope),
                        "grant_id": item.grant_id,
                        "audit_event_id": item.audit_event.event_id,
                    }
                    for item in self.authority.decisions
                ],
            }
        reconciliation_payload = None
        if self.reconciliation is not None:
            reconciliation_payload = {
                "outcome": self.reconciliation.outcome.value,
                "result_id": self.reconciliation.result.result_id,
                "evidence_ids": [item.evidence_id for item in self.reconciliation.evidence],
                "trace_id": self.reconciliation.trace.trace_id,
            }
        payload = self.analysis.to_dict()
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "status": self.status.value,
            "analysis": payload,
            "authority": authority_payload,
            "execution": self.execution.to_dict() if self.execution else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "reconciliation": reconciliation_payload,
            "execution_requested": self.execution_requested,
            "execution_performed": self.execution_performed,
            "simulated": True,
        }


class GovernedRuntime:
    """Compose the canonical governed runtime without bypassing any gate."""

    def __init__(
        self,
        *,
        pipeline: CognitiveRequestPipeline,
        authority_adapter: AuthorityGatedExecutionAdapter | None = None,
        execution_engine: ExecutionEngine | None = None,
        conformance_validator: ExecutionConformanceValidator | None = None,
        reconciler: ExecutionResultReconciler | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.authority_adapter = authority_adapter or AuthorityGatedExecutionAdapter()
        self.execution_engine = execution_engine or ExecutionEngine()
        self.conformance_validator = conformance_validator or ExecutionConformanceValidator()
        self.reconciler = reconciler or ExecutionResultReconciler()

    def process(self, request: GovernedRuntimeRequest) -> GovernedRuntimeResult:
        analysis = self.pipeline.process_selection(
            task=request.task,
            interpretation_id=request.interpretation_id,
            selection=request.selection,
            workflow_definition=request.workflow_definition,
        )
        plan = analysis.canonical_plan
        if plan is None:
            raise RuntimeError("bounded planning did not produce a canonical plan")
        if not request.execute:
            return GovernedRuntimeResult(
                request_id=plan.request_id,
                status=GovernedRuntimeStatus.ANALYZED,
                analysis=analysis,
                execution_requested=False,
            )

        authority = self.authority_adapter.prepare(
            plan=plan,
            selected_agent=analysis.capability.name,
            grants=request.grants,
            denials=request.denials,
            revocations=request.revocations,
            capability_id=analysis.capability.capability_id,
        )
        if not authority.ready:
            status = (
                GovernedRuntimeStatus.DENIED
                if authority.denied
                else GovernedRuntimeStatus.PAUSED
            )
            return GovernedRuntimeResult(
                request_id=plan.request_id,
                status=status,
                analysis=analysis,
                authority=authority,
                execution_requested=True,
                execution_performed=False,
            )

        execution_request = authority.execution_request
        if execution_request is None:
            raise RuntimeError("ready authority result lacks execution request")
        receipt = self.execution_engine.execute(execution_request)
        validation = self.conformance_validator.validate(
            request_id=plan.request_id,
            analysis=analysis,
            execution_request=execution_request,
            receipt=receipt,
        )
        reconciliation = self.reconciler.reconcile(receipt)
        status = self._status(receipt, validation)
        return GovernedRuntimeResult(
            request_id=plan.request_id,
            status=status,
            analysis=analysis,
            authority=authority,
            execution=receipt,
            validation=validation,
            reconciliation=reconciliation,
            execution_requested=True,
            execution_performed=True,
        )

    @staticmethod
    def _status(
        receipt: ExecutionReceipt,
        validation: ExecutionConformanceResult,
    ) -> GovernedRuntimeStatus:
        if validation.status is ConformanceStatus.FAILED:
            return GovernedRuntimeStatus.CONFORMANCE_FAILED
        if receipt.status is ExecutionStatus.COMPLETED:
            return GovernedRuntimeStatus.COMPLETED
        return GovernedRuntimeStatus.FAILED
