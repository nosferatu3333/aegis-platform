from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aegis_os.execution.models import (
    ExecutionMode,
    ExecutionReceipt,
    ExecutionRequest,
    ExecutionStatus,
    ExecutionStepStatus,
)
from aegis_os.pipeline.models import CognitiveRequestResult

CONFORMANCE_SCHEMA_VERSION = "1.0"
TERMINAL_EXECUTION_STATUSES = frozenset(
    {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    }
)
TERMINAL_STEP_STATUSES = frozenset(
    {
        ExecutionStepStatus.COMPLETED,
        ExecutionStepStatus.FAILED,
        ExecutionStepStatus.SKIPPED,
    }
)


class ConformanceStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class ConformanceContractError(ValueError):
    """Raised when a conformance result violates its typed contract."""


class ConformanceCheckName(StrEnum):
    REQUEST_IDENTITY = "request_identity"
    MISSION_PRESERVATION = "mission_preservation"
    CAPABILITY_SELECTION = "capability_selection"
    PLANNED_WORKFLOW = "planned_workflow"
    WORKFLOW_ORDERING = "workflow_ordering"
    WORKFLOW_COMPLETENESS = "workflow_completeness"
    TERMINAL_EXECUTION = "terminal_execution"
    SIMULATION_BOUNDARY = "simulation_boundary"


@dataclass(frozen=True)
class ConformanceCheck:
    name: ConformanceCheckName
    status: ConformanceStatus
    evidence: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, ConformanceCheckName):
            raise ConformanceContractError(
                "Conformance check name must use ConformanceCheckName."
            )
        if not isinstance(self.status, ConformanceStatus):
            raise ConformanceContractError(
                "Conformance check status must use ConformanceStatus."
            )
        if not self.evidence or not self.evidence.strip():
            raise ConformanceContractError(
                "Conformance check evidence cannot be empty."
            )

    @property
    def passed(self) -> bool:
        return self.status is ConformanceStatus.PASSED

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name.value,
            "status": self.status.value,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class ExecutionConformanceResult:
    request_id: str
    status: ConformanceStatus
    operation_outcome: ExecutionStatus
    checks: tuple[ConformanceCheck, ...]
    schema_version: str = CONFORMANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CONFORMANCE_SCHEMA_VERSION:
            raise ConformanceContractError("Unsupported conformance schema version.")
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ConformanceContractError("Conformance request_id cannot be empty.")
        if not isinstance(self.status, ConformanceStatus):
            raise ConformanceContractError(
                "Conformance status must use ConformanceStatus."
            )
        if (
            not isinstance(self.operation_outcome, ExecutionStatus)
            or self.operation_outcome not in TERMINAL_EXECUTION_STATUSES
        ):
            raise ConformanceContractError(
                "Conformance requires a terminal operation outcome."
            )
        if (
            not isinstance(self.checks, tuple)
            or not self.checks
            or any(not isinstance(check, ConformanceCheck) for check in self.checks)
        ):
            raise ConformanceContractError(
                "Conformance result requires a tuple of typed checks."
            )
        names = [check.name for check in self.checks]
        if names != list(ConformanceCheckName):
            raise ConformanceContractError(
                "Conformance result requires every defined check once "
                "in canonical order."
            )
        expected = (
            ConformanceStatus.PASSED
            if all(check.passed for check in self.checks)
            else ConformanceStatus.FAILED
        )
        if self.status is not expected:
            raise ConformanceContractError(
                "Conformance status must match its check outcomes."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "status": self.status.value,
            "operation_outcome": self.operation_outcome.value,
            "checks": [check.to_dict() for check in self.checks],
            "evidence": [check.evidence for check in self.checks],
        }


class ExecutionConformanceValidator:
    """Deterministically verifies execution against its source contracts."""

    def validate(
        self,
        *,
        request_id: str,
        analysis: CognitiveRequestResult,
        execution_request: ExecutionRequest,
        receipt: ExecutionReceipt,
    ) -> ExecutionConformanceResult:
        checks = (
            self._check(
                ConformanceCheckName.REQUEST_IDENTITY,
                request_id == execution_request.request_id == receipt.request_id,
                "Envelope, execution request, and receipt identities match.",
                "Runtime request identities do not match.",
            ),
            self._check(
                ConformanceCheckName.MISSION_PRESERVATION,
                analysis.task == execution_request.mission == receipt.mission,
                "The interpreted mission is preserved through execution.",
                "The execution mission differs from the interpreted task.",
            ),
            self._check(
                ConformanceCheckName.CAPABILITY_SELECTION,
                self._capability_matches(
                    analysis,
                    execution_request,
                    receipt,
                ),
                "Selected capability and required capabilities are preserved.",
                "Execution does not preserve the selected capabilities.",
            ),
            self._check(
                ConformanceCheckName.PLANNED_WORKFLOW,
                self._planned_workflow_matches(
                    analysis,
                    execution_request,
                    receipt,
                ),
                "Every executed step matches the generated workflow.",
                "Executed steps differ from the generated workflow.",
            ),
            self._check(
                ConformanceCheckName.WORKFLOW_ORDERING,
                self._workflow_order_is_valid(
                    analysis,
                    execution_request,
                    receipt,
                ),
                "Workflow order is contiguous and preserved.",
                "Workflow order is incomplete, duplicated, or reordered.",
            ),
            self._check(
                ConformanceCheckName.WORKFLOW_COMPLETENESS,
                workflow_completion_is_valid(receipt),
                "Receipt counts and terminal step states are complete.",
                "Receipt counts or terminal step states are incomplete.",
            ),
            self._check(
                ConformanceCheckName.TERMINAL_EXECUTION,
                terminal_execution_is_valid(receipt),
                "Execution reached a recorded terminal outcome.",
                "Execution did not reach a recorded terminal outcome.",
            ),
            self._check(
                ConformanceCheckName.SIMULATION_BOUNDARY,
                self._simulation_boundary_is_intact(
                    execution_request,
                    receipt,
                ),
                "Execution remained within the declared simulation boundary.",
                "Execution does not prove the declared simulation boundary.",
            ),
        )
        status = (
            ConformanceStatus.PASSED
            if all(check.passed for check in checks)
            else ConformanceStatus.FAILED
        )
        return ExecutionConformanceResult(
            request_id=request_id,
            status=status,
            operation_outcome=receipt.status,
            checks=checks,
        )

    @staticmethod
    def _check(
        name: ConformanceCheckName,
        passed: bool,
        passed_evidence: str,
        failed_evidence: str,
    ) -> ConformanceCheck:
        return ConformanceCheck(
            name=name,
            status=(ConformanceStatus.PASSED if passed else ConformanceStatus.FAILED),
            evidence=passed_evidence if passed else failed_evidence,
        )

    @staticmethod
    def _capability_matches(
        analysis: CognitiveRequestResult,
        execution_request: ExecutionRequest,
        receipt: ExecutionReceipt,
    ) -> bool:
        planned_capabilities = {step.capability_id for step in analysis.workflow}
        requested_capabilities = {
            ExecutionConformanceValidator._read_value(
                step,
                "capability_id",
            )
            for step in execution_request.workflow_steps
        }
        return (
            analysis.capability.name
            == execution_request.selected_agent
            == receipt.selected_agent
            and list(analysis.intent.required_capabilities)
            == execution_request.required_capabilities
            and planned_capabilities
            == requested_capabilities
            == {analysis.capability.capability_id}
        )

    @classmethod
    def _planned_workflow_matches(
        cls,
        analysis: CognitiveRequestResult,
        execution_request: ExecutionRequest,
        receipt: ExecutionReceipt,
    ) -> bool:
        planned_workflow = sorted(
            analysis.workflow,
            key=lambda step: step.order,
        )
        if not (
            len(planned_workflow)
            == len(execution_request.workflow_steps)
            == len(receipt.steps)
        ):
            return False

        for planned, requested, executed in zip(
            planned_workflow,
            execution_request.workflow_steps,
            receipt.steps,
            strict=True,
        ):
            order = cls._read_value(requested, "order")
            title = str(cls._read_value(requested, "title", "")).strip()
            description = str(cls._read_value(requested, "description", "")).strip()
            expected_description = f"{title}: {description}" if title else description
            if (
                planned.order != order
                or planned.title != title
                or planned.description != description
                or executed.order != order
                or executed.description != expected_description
            ):
                return False
        return True

    @classmethod
    def _workflow_order_is_valid(
        cls,
        analysis: CognitiveRequestResult,
        execution_request: ExecutionRequest,
        receipt: ExecutionReceipt,
    ) -> bool:
        planned_orders = sorted(step.order for step in analysis.workflow)
        requested_orders = [
            cls._read_value(step, "order") for step in execution_request.workflow_steps
        ]
        executed_orders = [step.order for step in receipt.steps]
        expected = list(range(1, len(planned_orders) + 1))
        return planned_orders == requested_orders == executed_orders == expected

    @staticmethod
    def _simulation_boundary_is_intact(
        execution_request: ExecutionRequest,
        receipt: ExecutionReceipt,
    ) -> bool:
        completed_outputs_are_simulated = all(
            step.outputs.get("simulated") is True
            for step in receipt.steps
            if step.status is ExecutionStepStatus.COMPLETED
        )
        return (
            execution_request.execution_mode is ExecutionMode.SIMULATED
            and receipt.execution_mode is ExecutionMode.SIMULATED
            and receipt.simulated is True
            and completed_outputs_are_simulated
        )

    @staticmethod
    def _read_value(
        source: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)


def terminal_execution_is_valid(receipt: ExecutionReceipt) -> bool:
    if (
        receipt.status not in TERMINAL_EXECUTION_STATUSES
        or receipt.started_at is None
        or receipt.finished_at is None
    ):
        return False
    try:
        return receipt.finished_at >= receipt.started_at
    except TypeError:
        return False


def workflow_completion_is_valid(receipt: ExecutionReceipt) -> bool:
    if not receipt.steps:
        return False

    completed = sum(
        step.status is ExecutionStepStatus.COMPLETED for step in receipt.steps
    )
    failed = sum(step.status is ExecutionStepStatus.FAILED for step in receipt.steps)
    if (
        completed != receipt.completed_steps
        or failed != receipt.failed_steps
        or any(step.status not in TERMINAL_STEP_STATUSES for step in receipt.steps)
    ):
        return False

    if receipt.status is ExecutionStatus.COMPLETED:
        return completed == len(receipt.steps) and failed == 0

    if receipt.status is ExecutionStatus.FAILED:
        failed_indexes = [
            index
            for index, step in enumerate(receipt.steps)
            if step.status is ExecutionStepStatus.FAILED
        ]
        if len(failed_indexes) != 1:
            return False
        failed_index = failed_indexes[0]
        return (
            receipt.completed_steps == failed_index
            and receipt.failed_steps == 1
            and all(
                step.status is ExecutionStepStatus.COMPLETED
                for step in receipt.steps[:failed_index]
            )
            and all(
                step.status is ExecutionStepStatus.SKIPPED
                for step in receipt.steps[failed_index + 1 :]
            )
        )

    if receipt.status is ExecutionStatus.CANCELLED:
        expected = [ExecutionStepStatus.COMPLETED] * receipt.completed_steps + [
            ExecutionStepStatus.SKIPPED
        ] * (len(receipt.steps) - receipt.completed_steps)
        return (
            receipt.failed_steps == 0
            and 0 <= receipt.completed_steps < len(receipt.steps)
            and [step.status for step in receipt.steps] == expected
        )

    return False
