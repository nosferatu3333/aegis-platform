from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from aegis_os.cognition.orchestrator import CognitiveOrchestrator
from aegis_os.core.runtime_errors import CanonicalRuntimeInvariantError
from aegis_os.execution.adapter import build_execution_request
from aegis_os.execution.conformance import (
    ConformanceContractError,
    ConformanceStatus,
    ExecutionConformanceResult,
    ExecutionConformanceValidator,
    terminal_execution_is_valid,
    workflow_completion_is_valid,
)
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import (
    ExecutionMode,
    ExecutionReceipt,
    ExecutionStatus,
)
from aegis_os.pipeline.models import CognitiveRequestResult, PipelineStatus
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

RUNTIME_SCHEMA_VERSION = "1.0"
TERMINAL_EXECUTION_STATUSES = frozenset(
    {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    }
)


class CanonicalRuntimeStatus(StrEnum):
    """Overall state of one canonical runtime operation."""

    ANALYZED = "analyzed"
    COMPLETED = "completed"
    CONFORMANCE_FAILED = "conformance_failed"
    FAILED = "failed"


class LifecycleStageStatus(StrEnum):
    """Availability state for a later canonical lifecycle stage."""

    NOT_IMPLEMENTED = "not_implemented"
    NOT_REQUESTED = "not_requested"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class LifecycleStageResult:
    """Explicit state for a lifecycle stage with no current implementation."""

    status: LifecycleStageStatus
    detail: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "status": self.status.value,
            "detail": self.detail,
        }


def _not_implemented(stage: str) -> LifecycleStageResult:
    return LifecycleStageResult(
        status=LifecycleStageStatus.NOT_IMPLEMENTED,
        detail=f"{stage} is not implemented in the canonical runtime.",
    )


def _not_requested(stage: str) -> LifecycleStageResult:
    return LifecycleStageResult(
        status=LifecycleStageStatus.NOT_REQUESTED,
        detail=f"{stage} was not requested for this runtime operation.",
    )


@dataclass(frozen=True)
class CanonicalRuntimeRequest:
    """Typed input accepted by the canonical runtime boundary."""

    task: str
    request_id: str
    execute: bool = False


@dataclass(frozen=True)
class CanonicalRuntimeResult:
    """Serializable envelope for the current canonical lifecycle."""

    request_id: str
    status: CanonicalRuntimeStatus
    analysis: CognitiveRequestResult
    execution: ExecutionReceipt | None
    execution_requested: bool
    execution_performed: bool
    simulated: bool = True
    validation: ExecutionConformanceResult | LifecycleStageResult = field(
        default_factory=lambda: _not_requested("Execution conformance validation")
    )
    governance: LifecycleStageResult = field(
        default_factory=lambda: _not_implemented("Governance")
    )
    evaluation: LifecycleStageResult = field(
        default_factory=lambda: _not_implemented("Evaluation")
    )
    learning: LifecycleStageResult = field(
        default_factory=lambda: _not_implemented("Learning")
    )
    schema_version: str = RUNTIME_SCHEMA_VERSION

    def __post_init__(self) -> None:
        receipt = self.execution

        if not self.request_id or not self.request_id.strip():
            raise CanonicalRuntimeInvariantError(
                "Canonical runtime result request_id cannot be empty."
            )
        if receipt is not None and not self.execution_requested:
            raise CanonicalRuntimeInvariantError(
                "Execution receipt requires execution_requested=True."
            )
        if receipt is not None and not self.execution_performed:
            raise CanonicalRuntimeInvariantError(
                "Execution receipt requires execution_performed=True."
            )
        if receipt is None and self.execution_performed:
            raise CanonicalRuntimeInvariantError(
                "execution_performed=True requires an execution receipt."
            )
        if receipt is not None and self.analysis.status is not PipelineStatus.READY:
            raise CanonicalRuntimeInvariantError(
                "Execution receipt requires READY analysis."
            )
        if receipt is not None and receipt.request_id != self.request_id:
            raise CanonicalRuntimeInvariantError(
                "Execution receipt request_id must match the runtime result."
            )
        if receipt is not None and receipt.status not in TERMINAL_EXECUTION_STATUSES:
            raise CanonicalRuntimeInvariantError(
                "Execution receipt must have a terminal status."
            )
        if receipt is not None and (
            not self.simulated
            or not receipt.simulated
            or receipt.execution_mode is not ExecutionMode.SIMULATED
        ):
            raise CanonicalRuntimeInvariantError(
                "Current execution receipts require typed simulation mode."
            )
        if receipt is not None and not terminal_execution_is_valid(receipt):
            raise CanonicalRuntimeInvariantError(
                "Execution receipt violates terminal timestamp invariants."
            )
        if receipt is not None and not workflow_completion_is_valid(receipt):
            raise CanonicalRuntimeInvariantError(
                "Execution receipt violates terminal workflow invariants."
            )
        if receipt is None:
            if (
                not isinstance(self.validation, LifecycleStageResult)
                or self.validation.status is not LifecycleStageStatus.NOT_REQUESTED
            ):
                raise CanonicalRuntimeInvariantError(
                    "Analysis-only results require validation not_requested."
                )
        else:
            if not isinstance(
                self.validation,
                ExecutionConformanceResult,
            ):
                raise CanonicalRuntimeInvariantError(
                    "Execution receipts require conformance validation."
                )
            if self.validation.request_id != self.request_id:
                raise CanonicalRuntimeInvariantError(
                    "Validation request_id must match the runtime result."
                )
            if self.validation.operation_outcome is not receipt.status:
                raise CanonicalRuntimeInvariantError(
                    "Validation outcome must match the execution receipt."
                )
        if self.status is CanonicalRuntimeStatus.ANALYZED:
            if receipt is not None:
                raise CanonicalRuntimeInvariantError(
                    "ANALYZED runtime results cannot contain execution receipts."
                )
            if self.execution_requested:
                raise CanonicalRuntimeInvariantError(
                    "ANALYZED runtime results cannot request execution."
                )
        if self.status is CanonicalRuntimeStatus.COMPLETED:
            if not self.execution_requested:
                raise CanonicalRuntimeInvariantError(
                    "COMPLETED runtime results require requested execution."
                )
            if receipt is None or receipt.status is not ExecutionStatus.COMPLETED:
                raise CanonicalRuntimeInvariantError(
                    "COMPLETED runtime results require a completed receipt."
                )
        if self.status is CanonicalRuntimeStatus.CONFORMANCE_FAILED:
            if (
                receipt is None
                or not isinstance(
                    self.validation,
                    ExecutionConformanceResult,
                )
                or self.validation.status is not ConformanceStatus.FAILED
            ):
                raise CanonicalRuntimeInvariantError(
                    "CONFORMANCE_FAILED runtime results require failed "
                    "execution conformance."
                )
        if (
            self.status is CanonicalRuntimeStatus.FAILED
            and receipt is not None
            and receipt.status is ExecutionStatus.COMPLETED
        ):
            raise CanonicalRuntimeInvariantError(
                "FAILED runtime results cannot contain a completed receipt."
            )

        expected_status = self._expected_status()
        if self.status is not expected_status:
            raise CanonicalRuntimeInvariantError(
                "Runtime status is inconsistent with analysis and execution."
            )

    def _expected_status(self) -> CanonicalRuntimeStatus:
        if self.analysis.status is not PipelineStatus.READY:
            return CanonicalRuntimeStatus.FAILED
        if self.execution is None:
            return CanonicalRuntimeStatus.ANALYZED
        if (
            isinstance(self.validation, ExecutionConformanceResult)
            and self.validation.status is ConformanceStatus.FAILED
        ):
            return CanonicalRuntimeStatus.CONFORMANCE_FAILED
        if self.execution.status is ExecutionStatus.COMPLETED:
            return CanonicalRuntimeStatus.COMPLETED
        return CanonicalRuntimeStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "status": self.status.value,
            "analysis": self.analysis.to_dict(),
            "execution": (self.execution.to_dict() if self.execution else None),
            "execution_requested": self.execution_requested,
            "execution_performed": self.execution_performed,
            "simulated": self.simulated,
            "validation": self.validation.to_dict(),
            "governance": self.governance.to_dict(),
            "evaluation": self.evaluation.to_dict(),
            "learning": self.learning.to_dict(),
        }


class CognitiveRuntime:
    """
    Connects the Aegis runtime
    with the cognitive architecture.
    """

    def __init__(
        self,
        pipeline: CognitiveRequestPipeline | None = None,
        execution_engine: ExecutionEngine | None = None,
        conformance_validator: ExecutionConformanceValidator | None = None,
        orchestrator: CognitiveOrchestrator | None = None,
    ):
        self.pipeline = pipeline
        self.execution_engine = execution_engine or ExecutionEngine()
        self.conformance_validator = (
            conformance_validator or ExecutionConformanceValidator()
        )
        self.orchestrator = orchestrator
        if self.orchestrator is None and pipeline is None:
            self.orchestrator = CognitiveOrchestrator()

        self.state = "initialized"

    def run(
        self,
        task: str,
        request_id: str,
        *,
        execute: bool = False,
    ) -> CanonicalRuntimeResult:
        """Run analysis once and optionally execute its ready workflow."""
        return self.process(
            CanonicalRuntimeRequest(
                task=task,
                request_id=request_id,
                execute=execute,
            )
        )

    def process(
        self,
        request: CanonicalRuntimeRequest,
    ) -> CanonicalRuntimeResult:
        if self.pipeline is None:
            raise RuntimeError("Canonical runtime pipeline is not configured.")
        if not request.request_id or not request.request_id.strip():
            raise ValueError("Runtime request_id cannot be empty.")

        analysis = self.pipeline.process_task(request.task)
        receipt = None
        validation: ExecutionConformanceResult | LifecycleStageResult = _not_requested(
            "Execution conformance validation"
        )

        if request.execute and analysis.status is PipelineStatus.READY:
            execution_request = build_execution_request(
                analysis,
                request.request_id,
                constraints=["Simulation only; no external actions are permitted."],
                permissions=["simulated_workflow_execution"],
            )
            receipt = self.execution_engine.execute(execution_request)
            try:
                validation = self.conformance_validator.validate(
                    request_id=request.request_id,
                    analysis=analysis,
                    execution_request=execution_request,
                    receipt=receipt,
                )
            except ConformanceContractError as error:
                raise CanonicalRuntimeInvariantError(
                    "Conformance validator produced an invalid result contract.",
                    request_id=request.request_id,
                ) from error
            if not isinstance(validation, ExecutionConformanceResult):
                raise CanonicalRuntimeInvariantError(
                    "Conformance validator returned an unsupported result.",
                    request_id=request.request_id,
                )
            if validation.request_id != request.request_id:
                raise CanonicalRuntimeInvariantError(
                    "Validation request_id must match the runtime request.",
                    request_id=request.request_id,
                )
            if validation.operation_outcome is not receipt.status:
                raise CanonicalRuntimeInvariantError(
                    "Validation outcome must match the execution receipt.",
                    request_id=request.request_id,
                )
        return CanonicalRuntimeResult(
            request_id=request.request_id,
            status=self._result_status(analysis, receipt, validation),
            analysis=analysis,
            execution=receipt,
            execution_requested=request.execute,
            execution_performed=receipt is not None,
            validation=validation,
        )

    @staticmethod
    def _result_status(
        analysis: CognitiveRequestResult,
        receipt: ExecutionReceipt | None,
        validation: ExecutionConformanceResult | LifecycleStageResult,
    ) -> CanonicalRuntimeStatus:
        if analysis.status is not PipelineStatus.READY:
            return CanonicalRuntimeStatus.FAILED
        if receipt is None:
            return CanonicalRuntimeStatus.ANALYZED
        if (
            isinstance(validation, ExecutionConformanceResult)
            and validation.status is ConformanceStatus.FAILED
        ):
            return CanonicalRuntimeStatus.CONFORMANCE_FAILED
        if receipt.status is ExecutionStatus.COMPLETED:
            return CanonicalRuntimeStatus.COMPLETED
        return CanonicalRuntimeStatus.FAILED

    def start(self):

        self.state = "running"

        print("Cognitive Runtime started.")

    def process_goal(self, goal):

        if self.state != "running":
            raise RuntimeError("Cognitive Runtime is not running")

        print(f"Cognitive goal received: {goal}")

        if self.orchestrator is None:
            raise RuntimeError("Legacy cognitive orchestrator is not configured")

        result = self.orchestrator.process(goal)

        print("Cognitive cycle completed.")

        return result
