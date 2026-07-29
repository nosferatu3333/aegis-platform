from datetime import UTC, datetime

import pytest

from aegis_os.execution.adapter import build_execution_request
from aegis_os.execution.conformance import (
    ConformanceCheckName,
    ConformanceStatus,
    ExecutionConformanceValidator,
)
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import ExecutionStatus
from aegis_os.pipeline.composition import create_default_pipeline
from aegis_os.pipeline.intent_analyzer import IntentAnalyzer
from aegis_os.pipeline.models import (
    CapabilityMatch,
    CognitiveRequestResult,
    WorkflowStep,
)

FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def make_analysis(*, controlled_failure=False):
    descriptions = [
        "Collect findings",
        ("[simulate-failure]" if controlled_failure else "Compare findings"),
    ]
    return CognitiveRequestResult(
        task="Research competitors",
        intent=IntentAnalyzer().analyze("Research competitors"),
        capability=CapabilityMatch(
            capability_id="research-agent",
            name="Research Agent",
            confidence=0.9,
            score=9,
        ),
        workflow=[
            WorkflowStep(
                order=index,
                title=f"Step {index}",
                description=description,
                capability_id="research-agent",
            )
            for index, description in enumerate(descriptions, start=1)
        ],
    )


def execute_analysis(analysis, request_id="conformance-1"):
    execution_request = build_execution_request(
        analysis,
        request_id,
        constraints=["Simulation only; no external actions are permitted."],
        permissions=["simulated_workflow_execution"],
    )
    receipt = ExecutionEngine(clock=lambda: FIXED_TIME).execute(execution_request)
    return execution_request, receipt


def test_successful_execution_passes_all_conformance_checks():
    analysis = create_default_pipeline().process_task(
        "Research autonomous intelligence systems"
    )
    execution_request, receipt = execute_analysis(analysis)

    validation = ExecutionConformanceValidator().validate(
        request_id="conformance-1",
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    )

    assert validation.status is ConformanceStatus.PASSED
    assert validation.operation_outcome is ExecutionStatus.COMPLETED
    assert {check.name for check in validation.checks} == set(ConformanceCheckName)
    assert all(check.passed for check in validation.checks)


def test_controlled_failed_execution_still_passes_conformance():
    analysis = make_analysis(controlled_failure=True)
    execution_request, receipt = execute_analysis(analysis)

    validation = ExecutionConformanceValidator().validate(
        request_id="conformance-1",
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    )

    assert receipt.status is ExecutionStatus.FAILED
    assert validation.status is ConformanceStatus.PASSED
    assert validation.operation_outcome is ExecutionStatus.FAILED
    assert all(check.passed for check in validation.checks)


def test_conformance_detects_request_and_workflow_mismatch():
    analysis = make_analysis()
    execution_request, receipt = execute_analysis(analysis)
    receipt.request_id = "different-request"
    receipt.steps[0].order = 2

    validation = ExecutionConformanceValidator().validate(
        request_id="conformance-1",
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    )
    failed_names = {check.name for check in validation.checks if not check.passed}

    assert validation.status is ConformanceStatus.FAILED
    assert ConformanceCheckName.REQUEST_IDENTITY in failed_names
    assert ConformanceCheckName.PLANNED_WORKFLOW in failed_names
    assert ConformanceCheckName.WORKFLOW_ORDERING in failed_names


@pytest.mark.parametrize(
    ("expected_check", "mutation"),
    [
        pytest.param(
            ConformanceCheckName.REQUEST_IDENTITY,
            "request_identity",
            id="request-identity",
        ),
        pytest.param(
            ConformanceCheckName.MISSION_PRESERVATION,
            "mission",
            id="mission-preservation",
        ),
        pytest.param(
            ConformanceCheckName.CAPABILITY_SELECTION,
            "capability",
            id="capability-selection",
        ),
        pytest.param(
            ConformanceCheckName.PLANNED_WORKFLOW,
            "planned_workflow",
            id="planned-workflow",
        ),
        pytest.param(
            ConformanceCheckName.WORKFLOW_ORDERING,
            "workflow_ordering",
            id="workflow-ordering",
        ),
        pytest.param(
            ConformanceCheckName.WORKFLOW_COMPLETENESS,
            "workflow_completeness",
            id="workflow-completeness",
        ),
        pytest.param(
            ConformanceCheckName.TERMINAL_EXECUTION,
            "terminal_execution",
            id="terminal-execution",
        ),
        pytest.param(
            ConformanceCheckName.SIMULATION_BOUNDARY,
            "simulation_boundary",
            id="simulation-boundary",
        ),
    ],
)
def test_conformance_detects_each_required_mismatch(
    expected_check,
    mutation,
):
    analysis = make_analysis()
    execution_request, receipt = execute_analysis(analysis)

    if mutation == "request_identity":
        receipt.request_id = "different-request"
    elif mutation == "mission":
        receipt.mission = "Different mission"
    elif mutation == "capability":
        receipt.selected_agent = "Different Agent"
    elif mutation == "planned_workflow":
        receipt.steps[0].description = "Different workflow step"
    elif mutation == "workflow_ordering":
        receipt.steps[0].order = 2
    elif mutation == "workflow_completeness":
        receipt.completed_steps = 0
    elif mutation == "terminal_execution":
        receipt.status = ExecutionStatus.RUNNING
        receipt.finished_at = None
    elif mutation == "simulation_boundary":
        receipt.simulated = False

    validation = ExecutionConformanceValidator().validate(
        request_id="conformance-1",
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    )
    failed_names = {check.name for check in validation.checks if not check.passed}

    assert validation.status is ConformanceStatus.FAILED
    assert expected_check in failed_names


def test_conformance_is_deterministic_and_does_not_mutate_inputs():
    analysis = make_analysis()
    execution_request, receipt = execute_analysis(analysis)
    analysis_before = analysis.to_dict()
    request_before = execution_request.to_dict()
    receipt_before = receipt.to_dict()
    validator = ExecutionConformanceValidator()

    first = validator.validate(
        request_id="conformance-1",
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    ).to_dict()
    second = validator.validate(
        request_id="conformance-1",
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    ).to_dict()

    assert first == second
    assert analysis.to_dict() == analysis_before
    assert execution_request.to_dict() == request_before
    assert receipt.to_dict() == receipt_before
