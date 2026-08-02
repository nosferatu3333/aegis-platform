"""Reconcile Platform execution receipts into canonical Core evidence and results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Callable

from aegis_core.contracts import (
    CognitiveTrace,
    CompletionState,
    EvidenceAccessState,
    EvidenceFreshnessState,
    EvidenceRecord,
    EvidenceState,
    EvidenceType,
    EvidenceVerificationState,
    ExecutionResult,
    IntegrityState,
    ProvenanceReference,
    ResultRecord,
    TraceLink,
    TraceRelationship,
)
from aegis_core.contracts import ExecutionStatus as CoreExecutionStatus

from aegis_os.execution.models import (
    ExecutionReceipt,
    ExecutionStatus,
    ExecutionStepStatus,
)


class ReconciliationOutcome(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ReconciledExecutionResult:
    request_id: str
    plan_id: str
    outcome: ReconciliationOutcome
    step_results: tuple[ExecutionResult, ...]
    evidence: tuple[EvidenceRecord, ...]
    result: ResultRecord
    trace: CognitiveTrace


class ExecutionResultReconciler:
    """Create immutable evidence and result lineage from an execution receipt.

    Reconciliation records what Platform observed. It does not reinterpret a
    failed execution as success and does not claim that simulated execution
    proves real-world effects.
    """

    def __init__(
        self,
        *,
        actor_id: str = "svc_aegis_platform",
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.actor_id = actor_id
        self._clock = clock or (lambda: datetime.now(UTC))

    def reconcile(self, receipt: ExecutionReceipt) -> ReconciledExecutionResult:
        self._validate_receipt(receipt)
        plan_id = str(receipt.metadata["canonical_plan_id"])
        observed_at = self._clock()

        step_results = tuple(
            self._step_result(plan_id, receipt, step)
            for step in receipt.steps
        )
        evidence = tuple(
            self._evidence_for_step(receipt, step, observed_at)
            for step in receipt.steps
        ) + (self._receipt_evidence(receipt, observed_at),)

        outcome, completion_state, limitations = self._classify(receipt)
        result = ResultRecord(
            request_id=receipt.request_id,
            plan_id=plan_id,
            content={
                "mission": receipt.mission,
                "selected_agent": receipt.selected_agent,
                "execution_mode": receipt.execution_mode.value,
                "execution_status": receipt.status.value,
                "completed_steps": receipt.completed_steps,
                "failed_steps": receipt.failed_steps,
                "simulated": receipt.simulated,
                "step_result_ids": [item.result_id for item in step_results],
            },
            completion_state=completion_state,
            evidence_state=EvidenceState.VERIFIED,
            limitations=limitations,
            evidence_ids=tuple(item.evidence_id for item in evidence),
            created_at=observed_at,
        )
        trace = self._build_trace(
            request_id=receipt.request_id,
            plan_id=plan_id,
            result_id=result.result_id,
            evidence=evidence,
            created_at=observed_at,
        )
        return ReconciledExecutionResult(
            request_id=receipt.request_id,
            plan_id=plan_id,
            outcome=outcome,
            step_results=step_results,
            evidence=evidence,
            result=result,
            trace=trace,
        )

    @staticmethod
    def _validate_receipt(receipt: ExecutionReceipt) -> None:
        if not isinstance(receipt, ExecutionReceipt):
            raise TypeError("receipt must be an ExecutionReceipt")
        if receipt.status not in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        }:
            raise ValueError("only terminal execution receipts can be reconciled")
        if receipt.started_at is None or receipt.finished_at is None:
            raise ValueError("terminal execution receipts require start and finish times")
        if "canonical_plan_id" not in receipt.metadata:
            raise ValueError("execution receipt is missing canonical_plan_id lineage")
        if not str(receipt.metadata["canonical_plan_id"]).startswith("pln_"):
            raise ValueError("canonical_plan_id must be a canonical plan identifier")
        if not receipt.request_id.startswith("req_"):
            raise ValueError("request_id must be a canonical request identifier")

    @staticmethod
    def _step_result(plan_id, receipt, step) -> ExecutionResult:
        status = {
            ExecutionStepStatus.COMPLETED: CoreExecutionStatus.SUCCEEDED,
            ExecutionStepStatus.FAILED: CoreExecutionStatus.FAILED,
            ExecutionStepStatus.SKIPPED: CoreExecutionStatus.SKIPPED,
        }.get(step.status, CoreExecutionStatus.PARTIAL)
        failures = (step.error,) if step.error else ()
        return ExecutionResult(
            plan_id=plan_id,
            step_id=step.step_id,
            status=status,
            outputs=dict(step.outputs),
            failures=failures,
            source_references=(f"execution-receipt:{receipt.request_id}",),
            started_at=receipt.started_at,
            finished_at=receipt.finished_at,
        )

    def _evidence_for_step(self, receipt, step, observed_at) -> EvidenceRecord:
        payload = json.dumps(step.to_dict(), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        provenance = ProvenanceReference(
            source_type="platform_execution_step",
            source_id=step.step_id,
            locator=f"receipt:{receipt.request_id}/step:{step.step_id}",
            content_hash=digest,
            captured_at=observed_at,
        )
        summary = f"Platform observed step {step.step_id} as {step.status.value}."
        limitations = (
            "Evidence records simulated Platform execution, not external real-world effect.",
        ) if receipt.simulated else ()
        return EvidenceRecord(
            evidence_type=EvidenceType.RUNTIME_OBSERVATION,
            subject_type="execution_step",
            subject_id=step.step_id,
            summary=summary,
            integrity_state=IntegrityState.VERIFIED,
            verification_state=EvidenceVerificationState.VERIFIED,
            freshness_state=EvidenceFreshnessState.CURRENT,
            access_state=EvidenceAccessState.AVAILABLE,
            provenance=(provenance,),
            verified_by=self.actor_id,
            verified_at=observed_at,
            limitations=limitations,
            captured_at=observed_at,
        )

    def _receipt_evidence(self, receipt, observed_at) -> EvidenceRecord:
        payload = json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        provenance = ProvenanceReference(
            source_type="platform_execution_receipt",
            source_id=receipt.request_id,
            locator=f"receipt:{receipt.request_id}",
            content_hash=digest,
            captured_at=observed_at,
        )
        limitations = (
            "Receipt proves simulated Platform execution only; external effects are not claimed.",
        ) if receipt.simulated else ()
        return EvidenceRecord(
            evidence_type=EvidenceType.RUNTIME_OBSERVATION,
            subject_type="execution_receipt",
            subject_id=receipt.request_id,
            summary=f"Execution receipt reconciled with terminal status {receipt.status.value}.",
            integrity_state=IntegrityState.VERIFIED,
            verification_state=EvidenceVerificationState.VERIFIED,
            freshness_state=EvidenceFreshnessState.CURRENT,
            access_state=EvidenceAccessState.AVAILABLE,
            provenance=(provenance,),
            verified_by=self.actor_id,
            verified_at=observed_at,
            limitations=limitations,
            captured_at=observed_at,
        )

    @staticmethod
    def _classify(receipt):
        simulation = (
            "Execution was simulated; real-world completion and side effects remain unverified.",
        ) if receipt.simulated else ()
        if receipt.status is ExecutionStatus.COMPLETED:
            return ReconciliationOutcome.COMPLETE, CompletionState.COMPLETE, simulation
        if receipt.status is ExecutionStatus.FAILED:
            return (
                ReconciliationOutcome.FAILED,
                CompletionState.FAILED,
                simulation + ("Execution terminated with one or more failed steps.",),
            )
        if receipt.status is ExecutionStatus.CANCELLED:
            return (
                ReconciliationOutcome.PARTIAL,
                CompletionState.CANCELLED,
                simulation + ("Execution was cancelled before full completion.",),
            )
        return (
            ReconciliationOutcome.UNKNOWN,
            CompletionState.UNKNOWN,
            simulation + ("Execution outcome could not be classified.",),
        )

    @staticmethod
    def _build_trace(*, request_id, plan_id, result_id, evidence, created_at):
        links = [
            TraceLink(
                source_type="request",
                source_id=request_id,
                target_type="plan",
                target_id=plan_id,
                relationship=TraceRelationship.PLANNED_FROM,
                created_at=created_at,
            ),
            TraceLink(
                source_type="plan",
                source_id=plan_id,
                target_type="result",
                target_id=result_id,
                relationship=TraceRelationship.RESULTED_IN,
                created_at=created_at,
            ),
        ]
        links.extend(
            TraceLink(
                source_type="result",
                source_id=result_id,
                target_type="evidence",
                target_id=item.evidence_id,
                relationship=TraceRelationship.SUPPORTED_BY,
                created_at=created_at,
            )
            for item in evidence
        )
        return CognitiveTrace(
            request_id=request_id,
            plan_id=plan_id,
            result_id=result_id,
            evidence_ids=tuple(item.evidence_id for item in evidence),
            links=tuple(links),
            created_at=created_at,
        )
