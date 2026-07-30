from datetime import UTC, datetime, timedelta

import pytest

from aegis_os.execution.adapter import build_execution_request
from aegis_os.execution.conformance import (
    ConformanceCheckName,
    ConformanceStatus,
    ExecutionConformanceValidator,
)
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import (
    ExecutionStatus,
    ExecutionStepStatus,
)
from aegis_os.pipeline.composition import create_default_pipeline

FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def make_cancelled_execution(*, completed_steps=1):
    analysis = create_default_pipeline().process_task(
        "Research autonomous intelligence systems"
    )
    execution_request = build_execution_request(
        analysis,
        "cancel-1",
    )
    receipt = ExecutionEngine(clock=lambda: FIXED_TIME).execute(execution_request)
    receipt.status = ExecutionStatus.CANCELLED
    receipt.completed_steps = completed_steps
    receipt.failed_steps = 0
    for index, step in enumerate(receipt.steps):
        step.status = (
            ExecutionStepStatus.COMPLETED
            if index < completed_steps
            else ExecutionStepStatus.SKIPPED
        )
    return analysis, execution_request, receipt


def validate_cancelled(analysis, execution_request, receipt):
    return ExecutionConformanceValidator().validate(
        request_id="cancel-1",
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    )


def test_cancelled_receipt_accepts_completed_prefix_and_skipped_suffix():
    analysis, execution_request, receipt = make_cancelled_execution(completed_steps=1)

    validation = validate_cancelled(
        analysis,
        execution_request,
        receipt,
    )

    assert validation.status is ConformanceStatus.PASSED
    assert validation.operation_outcome is ExecutionStatus.CANCELLED
    assert [step.status for step in receipt.steps] == [
        ExecutionStepStatus.COMPLETED,
        ExecutionStepStatus.SKIPPED,
        ExecutionStepStatus.SKIPPED,
        ExecutionStepStatus.SKIPPED,
        ExecutionStepStatus.SKIPPED,
    ]


@pytest.mark.parametrize(
    ("contradiction", "expected_check"),
    [
        pytest.param(
            "all-completed",
            ConformanceCheckName.WORKFLOW_COMPLETENESS,
            id="all-completed",
        ),
        pytest.param(
            "failed-step",
            ConformanceCheckName.WORKFLOW_COMPLETENESS,
            id="failed-step",
        ),
        pytest.param(
            "pending-step",
            ConformanceCheckName.WORKFLOW_COMPLETENESS,
            id="pending-step",
        ),
        pytest.param(
            "out-of-order",
            ConformanceCheckName.WORKFLOW_COMPLETENESS,
            id="out-of-order",
        ),
        pytest.param(
            "count-mismatch",
            ConformanceCheckName.WORKFLOW_COMPLETENESS,
            id="count-mismatch",
        ),
        pytest.param(
            "missing-start",
            ConformanceCheckName.TERMINAL_EXECUTION,
            id="missing-start",
        ),
        pytest.param(
            "reversed-time",
            ConformanceCheckName.TERMINAL_EXECUTION,
            id="reversed-time",
        ),
    ],
)
def test_contradictory_cancelled_receipts_fail_conformance(
    contradiction,
    expected_check,
):
    analysis, execution_request, receipt = make_cancelled_execution(completed_steps=1)

    if contradiction == "all-completed":
        receipt.completed_steps = len(receipt.steps)
        for step in receipt.steps:
            step.status = ExecutionStepStatus.COMPLETED
    elif contradiction == "failed-step":
        receipt.steps[1].status = ExecutionStepStatus.FAILED
        receipt.failed_steps = 1
    elif contradiction == "pending-step":
        receipt.steps[1].status = ExecutionStepStatus.PENDING
    elif contradiction == "out-of-order":
        receipt.steps[0].status = ExecutionStepStatus.SKIPPED
        receipt.steps[1].status = ExecutionStepStatus.COMPLETED
    elif contradiction == "count-mismatch":
        receipt.completed_steps = 0
    elif contradiction == "missing-start":
        receipt.started_at = None
    elif contradiction == "reversed-time":
        receipt.finished_at = receipt.started_at - timedelta(seconds=1)

    validation = validate_cancelled(
        analysis,
        execution_request,
        receipt,
    )
    failed_checks = {check.name for check in validation.checks if not check.passed}

    assert validation.status is ConformanceStatus.FAILED
    assert expected_check in failed_checks
