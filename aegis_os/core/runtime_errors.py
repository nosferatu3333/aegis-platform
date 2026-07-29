from __future__ import annotations

from typing import Any

from aegis_os.execution.conformance import ExecutionConformanceResult


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

    def __init__(
        self,
        validation: ExecutionConformanceResult,
    ) -> None:
        self.validation = validation
        super().__init__(
            "Simulated execution failed runtime conformance validation.",
            request_id=validation.request_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "validation": self.validation.to_dict(),
        }
