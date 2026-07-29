from __future__ import annotations

from typing import Any

from aegis_os.execution.conformance import (
    ConformanceStatus,
    ExecutionConformanceResult,
)
from aegis_os.execution.models import ExecutionReceipt
from aegis_os.pipeline.models import CognitiveRequestResult


class RuntimeIntegrityError(RuntimeError):
    """Base class for server-produced canonical runtime faults."""

    error_code = "runtime_integrity_failure"

    def __init__(
        self,
        message: str,
        *,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.request_id = request_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.error_code,
            "message": str(self),
        }


class CanonicalRuntimeInvariantError(RuntimeIntegrityError):
    """Raised when a canonical runtime envelope is internally contradictory."""

    error_code = "canonical_runtime_invariant_failure"


class RuntimeConformanceError(RuntimeIntegrityError):
    """Raised when execution produces a valid failed-conformance result."""

    error_code = "execution_conformance_failure"
    classification = "internal_runtime_integrity_failure"

    def __init__(
        self,
        *,
        request_id: str,
        analysis: CognitiveRequestResult,
        execution: ExecutionReceipt,
        validation: ExecutionConformanceResult,
    ) -> None:
        if not request_id or not request_id.strip():
            raise ValueError("Conformance failure request_id cannot be empty.")
        if not isinstance(analysis, CognitiveRequestResult):
            raise TypeError(
                "RuntimeConformanceError analysis must be CognitiveRequestResult."
            )
        if not isinstance(execution, ExecutionReceipt):
            raise TypeError(
                "RuntimeConformanceError execution must be ExecutionReceipt."
            )
        if not isinstance(validation, ExecutionConformanceResult):
            raise TypeError(
                "RuntimeConformanceError validation must be ExecutionConformanceResult."
            )
        if execution.request_id != request_id:
            raise ValueError(
                "Conformance failure execution request_id must match the failure."
            )
        if validation.request_id != request_id:
            raise ValueError(
                "Conformance failure validation request_id must match the failure."
            )
        if validation.operation_outcome is not execution.status:
            raise ValueError(
                "Conformance failure outcome must match the execution receipt."
            )
        if validation.status is not ConformanceStatus.FAILED:
            raise ValueError(
                "RuntimeConformanceError requires failed conformance validation."
            )

        self.analysis = analysis
        self.execution = execution
        self.validation = validation
        super().__init__(
            "Simulated execution failed runtime conformance validation.",
            request_id=request_id,
        )

    @property
    def receipt(self) -> ExecutionReceipt:
        """Compatibility alias naming the retained execution artifact."""
        return self.execution

    def to_dict(self) -> dict[str, Any]:
        analysis_payload = self.analysis.to_dict()
        analysis_payload["request_id"] = self.request_id
        return {
            **super().to_dict(),
            "type": type(self).__name__,
            "classification": self.classification,
            "request_id": self.request_id,
            "analysis": analysis_payload,
            "execution": self.execution.to_dict(),
            "validation": self.validation.to_dict(),
        }
