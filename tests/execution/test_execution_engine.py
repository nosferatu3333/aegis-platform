from datetime import UTC, datetime

import pytest

from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import (
    ExecutionRequest,
    ExecutionStatus,
    ExecutionStepStatus,
)

FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def make_request(descriptions=None):
    descriptions = descriptions or ["First action", "Second action"]
    return ExecutionRequest(
        request_id="request-1",
        mission="Research a market",
        selected_agent="Research Agent",
        required_capabilities=["research"],
        workflow_steps=[
            {
                "order": index,
                "title": f"Step {index}",
                "description": description,
            }
            for index, description in enumerate(descriptions, start=1)
        ],
    )


def test_successful_execution_is_ordered_and_auditable():
    receipt = ExecutionEngine(clock=lambda: FIXED_TIME).execute(make_request())

    assert receipt.status is ExecutionStatus.COMPLETED
    assert [step.order for step in receipt.steps] == [1, 2]
    assert all(step.status is ExecutionStepStatus.COMPLETED for step in receipt.steps)
    assert receipt.completed_steps == 2
    assert receipt.failed_steps == 0
    assert receipt.started_at == FIXED_TIME
    assert receipt.finished_at == FIXED_TIME
    assert receipt.simulated is True
    assert receipt.logs[0].startswith("request status: pending -> ready")
    assert receipt.logs[1].startswith("request status: ready -> running")
    assert receipt.logs[-1].startswith("request status: running -> completed")


def test_simulated_outputs_are_deterministic():
    engine = ExecutionEngine(clock=lambda: FIXED_TIME)

    first = engine.execute(make_request()).to_dict()
    second = engine.execute(make_request()).to_dict()

    assert first == second
    assert first["steps"][0]["outputs"] == {
        "message": ("Simulated completion of step 1: Step 1: First action"),
        "simulated": True,
    }


def test_controlled_failure_skips_remaining_steps():
    receipt = ExecutionEngine(clock=lambda: FIXED_TIME).execute(
        make_request(["Complete normally", "[simulate-failure]", "Do not run"])
    )

    assert receipt.status is ExecutionStatus.FAILED
    assert [step.status for step in receipt.steps] == [
        ExecutionStepStatus.COMPLETED,
        ExecutionStepStatus.FAILED,
        ExecutionStepStatus.SKIPPED,
    ]
    assert receipt.completed_steps == 1
    assert receipt.failed_steps == 1
    assert receipt.finished_at == FIXED_TIME
    assert "Controlled simulated failure" in receipt.steps[1].error
    assert receipt.simulated is True


@pytest.mark.parametrize(
    ("execution_request", "message"),
    [
        (make_request(), "request_id"),
        (make_request(), "mission"),
        (make_request(), "selected_agent"),
        (make_request(), "workflow_steps"),
    ],
)
def test_malformed_requests_are_rejected(execution_request, message):
    if message == "request_id":
        execution_request.request_id = " "
    elif message == "mission":
        execution_request.mission = ""
    elif message == "selected_agent":
        execution_request.selected_agent = ""
    else:
        execution_request.workflow_steps = []

    with pytest.raises(ValueError, match=message):
        ExecutionEngine().execute(execution_request)


def test_non_execution_request_is_rejected():
    with pytest.raises(TypeError, match="ExecutionRequest"):
        ExecutionEngine().execute({})  # type: ignore[arg-type]
