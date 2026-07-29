from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from aegis_os.execution.models import (
    ExecutionMode,
    ExecutionReceipt,
    ExecutionRequest,
    ExecutionStatus,
    ExecutionStep,
    ExecutionStepStatus,
)

logger = logging.getLogger("aegis.execution")
FAILURE_MARKER = "[simulate-failure]"


class ExecutionEngine:
    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self, request: ExecutionRequest) -> ExecutionReceipt:
        self._validate_request(request)
        steps = self._build_steps(request.workflow_steps)
        receipt = ExecutionReceipt(
            request_id=request.request_id,
            mission=request.mission,
            selected_agent=request.selected_agent,
            execution_mode=request.execution_mode,
            steps=steps,
        )

        self._transition(receipt, ExecutionStatus.READY)
        receipt.started_at = self._clock()
        self._transition(receipt, ExecutionStatus.RUNNING)
        logger.info(
            "event=execution_started request_id=%s selected_agent=%s simulated=true",
            request.request_id,
            request.selected_agent,
        )

        for index, step in enumerate(receipt.steps):
            self._step_transition(receipt, step, ExecutionStepStatus.RUNNING)

            if FAILURE_MARKER in step.description.lower():
                step.error = "Controlled simulated failure marker encountered."
                receipt.logs.append(
                    f"{step.step_id} failure: {step.error} simulated=true"
                )
                self._step_transition(
                    receipt,
                    step,
                    ExecutionStepStatus.FAILED,
                )
                for remaining in receipt.steps[index + 1 :]:
                    self._step_transition(
                        receipt,
                        remaining,
                        ExecutionStepStatus.SKIPPED,
                    )
                receipt.failed_steps = 1
                receipt.completed_steps = index
                receipt.finished_at = self._clock()
                self._transition(receipt, ExecutionStatus.FAILED)
                logger.info(
                    "event=execution_failed request_id=%s "
                    "selected_agent=%s simulated=true",
                    request.request_id,
                    request.selected_agent,
                )
                return receipt

            step.outputs = {
                "message": (
                    f"Simulated completion of step {step.order}: {step.description}"
                ),
                "simulated": True,
            }
            self._step_transition(
                receipt,
                step,
                ExecutionStepStatus.COMPLETED,
            )

        receipt.completed_steps = len(receipt.steps)
        receipt.finished_at = self._clock()
        self._transition(receipt, ExecutionStatus.COMPLETED)
        logger.info(
            "event=execution_completed request_id=%s selected_agent=%s simulated=true",
            request.request_id,
            request.selected_agent,
        )
        return receipt

    @staticmethod
    def _validate_request(request: ExecutionRequest) -> None:
        if not isinstance(request, ExecutionRequest):
            raise TypeError("request must be an ExecutionRequest.")
        if not request.request_id or not request.request_id.strip():
            raise ValueError("Execution request_id cannot be empty.")
        if not request.mission or not request.mission.strip():
            raise ValueError("Execution mission cannot be empty.")
        if not request.selected_agent or not request.selected_agent.strip():
            raise ValueError("Execution selected_agent cannot be empty.")
        if request.execution_mode is not ExecutionMode.SIMULATED:
            raise ValueError("Execution requires the typed simulated execution mode.")
        if not request.workflow_steps:
            raise ValueError("Execution workflow_steps cannot be empty.")

        orders = [
            ExecutionEngine._read_value(step, "order")
            for step in request.workflow_steps
        ]
        if any(not isinstance(order, int) or order < 1 for order in orders) or len(
            set(orders)
        ) != len(orders):
            raise ValueError(
                "Execution workflow step orders must be unique positive integers."
            )

    @classmethod
    def _build_steps(cls, workflow_steps: list[Any]) -> list[ExecutionStep]:
        result: list[ExecutionStep] = []
        for raw_step in sorted(
            workflow_steps,
            key=lambda step: cls._read_value(step, "order"),
        ):
            order = cls._read_value(raw_step, "order")
            title = str(cls._read_value(raw_step, "title", "")).strip()
            description = str(cls._read_value(raw_step, "description", "")).strip()
            if not description:
                raise ValueError(
                    f"Execution workflow step {order} needs a description."
                )
            display_description = f"{title}: {description}" if title else description
            result.append(
                ExecutionStep(
                    step_id=f"step-{order}",
                    order=order,
                    description=display_description,
                    inputs={"mission": "provided"},
                )
            )
        return result

    @staticmethod
    def _read_value(
        source: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    @staticmethod
    def _transition(
        receipt: ExecutionReceipt,
        status: ExecutionStatus,
    ) -> None:
        previous = receipt.status
        receipt.status = status
        entry = f"request status: {previous.value} -> {status.value}; simulated=true"
        receipt.logs.append(entry)
        logger.info(
            "event=request_transition request_id=%s from=%s to=%s simulated=true",
            receipt.request_id,
            previous.value,
            status.value,
        )

    @staticmethod
    def _step_transition(
        receipt: ExecutionReceipt,
        step: ExecutionStep,
        status: ExecutionStepStatus,
    ) -> None:
        previous = step.status
        step.status = status
        receipt.logs.append(
            f"{step.step_id} status: {previous.value} -> {status.value}; simulated=true"
        )
        logger.info(
            "event=step_transition request_id=%s step_id=%s "
            "from=%s to=%s simulated=true",
            receipt.request_id,
            step.step_id,
            previous.value,
            status.value,
        )
