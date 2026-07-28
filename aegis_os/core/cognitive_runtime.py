from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aegis_os.cognition.orchestrator import CognitiveOrchestrator
from aegis_os.execution.adapter import build_execution_request
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import ExecutionReceipt, ExecutionStatus
from aegis_os.pipeline.models import CognitiveRequestResult, PipelineStatus
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

RUNTIME_SCHEMA_VERSION = "1.0"


class CanonicalRuntimeStatus(StrEnum):
    """Overall state of one canonical runtime operation."""

    ANALYZED = "analyzed"
    COMPLETED = "completed"
    FAILED = "failed"


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
    governance: None = None
    evaluation: None = None
    learning: None = None
    schema_version: str = RUNTIME_SCHEMA_VERSION

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
            "governance": self.governance,
            "evaluation": self.evaluation,
            "learning": self.learning,
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
        orchestrator: CognitiveOrchestrator | None = None,
    ):
        self.pipeline = pipeline
        self.execution_engine = execution_engine or ExecutionEngine()
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

        if request.execute and analysis.status is PipelineStatus.READY:
            execution_request = build_execution_request(
                analysis,
                request.request_id,
                constraints=["Simulation only; no external actions are permitted."],
                permissions=["simulated_workflow_execution"],
            )
            receipt = self.execution_engine.execute(execution_request)

        return CanonicalRuntimeResult(
            request_id=request.request_id,
            status=self._result_status(analysis, receipt),
            analysis=analysis,
            execution=receipt,
            execution_requested=request.execute,
            execution_performed=receipt is not None,
        )

    @staticmethod
    def _result_status(
        analysis: CognitiveRequestResult,
        receipt: ExecutionReceipt | None,
    ) -> CanonicalRuntimeStatus:
        if analysis.status is not PipelineStatus.READY:
            return CanonicalRuntimeStatus.FAILED
        if receipt is None:
            return CanonicalRuntimeStatus.ANALYZED
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
