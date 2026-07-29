import json
from datetime import UTC, datetime

import pytest

import aegis_os.core.cognitive_runtime as runtime_module
from aegis_os.core.cognitive_runtime import (
    RUNTIME_SCHEMA_VERSION,
    CanonicalRuntimeResult,
    CanonicalRuntimeStatus,
    CognitiveRuntime,
    LifecycleStageStatus,
)
from aegis_os.core.runtime_errors import (
    CanonicalRuntimeInvariantError,
    RuntimeConformanceError,
)
from aegis_os.execution.conformance import (
    ConformanceCheck,
    ConformanceCheckName,
    ConformanceStatus,
    ExecutionConformanceResult,
    ExecutionConformanceValidator,
)
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import (
    ExecutionReceipt,
    ExecutionStatus,
    ExecutionStep,
    ExecutionStepStatus,
)
from aegis_os.pipeline.composition import create_default_pipeline
from aegis_os.pipeline.intent_analyzer import IntentAnalyzer
from aegis_os.pipeline.models import (
    CapabilityMatch,
    CognitiveRequestResult,
    PipelineStatus,
    WorkflowStep,
)

FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)


class CountingPipeline:
    def __init__(self, result=None):
        self.delegate = create_default_pipeline()
        self.result = result
        self.calls = 0

    def process_task(self, task):
        self.calls += 1
        return self.result or self.delegate.process_task(task)


class CountingExecutionEngine:
    def __init__(self, events=None):
        self.delegate = ExecutionEngine(clock=lambda: FIXED_TIME)
        self.requests = []
        self.events = events

    def execute(self, request):
        self.requests.append(request)
        if self.events is not None:
            self.events.append("execution")
        return self.delegate.execute(request)


class CountingConformanceValidator:
    def __init__(self, events=None):
        self.delegate = ExecutionConformanceValidator()
        self.calls = []
        self.events = events

    def validate(self, **arguments):
        self.calls.append(arguments)
        if self.events is not None:
            self.events.append("validation")
        return self.delegate.validate(**arguments)


class FailedConformanceValidator:
    def validate(self, **arguments):
        validation = ExecutionConformanceValidator().validate(**arguments)
        checks = tuple(
            ConformanceCheck(
                name=check.name,
                status=(
                    ConformanceStatus.FAILED
                    if check.name is ConformanceCheckName.MISSION_PRESERVATION
                    else check.status
                ),
                evidence=(
                    "Injected deterministic mission-preservation mismatch."
                    if check.name is ConformanceCheckName.MISSION_PRESERVATION
                    else check.evidence
                ),
            )
            for check in validation.checks
        )
        return ExecutionConformanceResult(
            request_id=validation.request_id,
            status=ConformanceStatus.FAILED,
            operation_outcome=validation.operation_outcome,
            checks=checks,
        )


class MismatchedConformanceValidator:
    def validate(self, **arguments):
        return make_validation(
            request_id="different-request",
            operation_outcome=arguments["receipt"].status,
        )


class StubLegacyOrchestrator:
    def __init__(self):
        self.goals = []

    def process(self, goal):
        self.goals.append(goal)
        return {"goal": goal, "simulation": True}


def make_result(*, ready=True, failure=False):
    return CognitiveRequestResult(
        task="Research competitors",
        intent=IntentAnalyzer().analyze("Research competitors"),
        capability=CapabilityMatch(
            capability_id="research-agent",
            name="Research Agent",
            confidence=0.9,
            score=9,
        ),
        workflow=(
            [
                WorkflowStep(
                    2,
                    "Compare",
                    ("[simulate-failure]" if failure else "Compare findings"),
                    "research-agent",
                ),
                WorkflowStep(
                    1,
                    "Collect",
                    "Collect findings",
                    "research-agent",
                ),
            ]
            if ready
            else []
        ),
        status=PipelineStatus.READY if ready else PipelineStatus.FAILED,
        metadata=({} if ready else {"failure_code": "no_capability_match"}),
    )


def make_receipt(
    *,
    request_id="runtime-result-1",
    status=ExecutionStatus.COMPLETED,
    simulated=True,
    execution_mode=None,
):
    step_status = ExecutionStepStatus.PENDING
    completed_steps = 0
    failed_steps = 0
    if status is ExecutionStatus.COMPLETED:
        step_status = ExecutionStepStatus.COMPLETED
        completed_steps = 1
    elif status is ExecutionStatus.FAILED:
        step_status = ExecutionStepStatus.FAILED
        failed_steps = 1
    elif status is ExecutionStatus.CANCELLED:
        step_status = ExecutionStepStatus.SKIPPED
    terminal = status in {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    }
    receipt = ExecutionReceipt(
        request_id=request_id,
        mission="Research competitors",
        selected_agent="Research Agent",
        status=status,
        steps=[
            ExecutionStep(
                step_id="step-1",
                order=1,
                description="Collect: Collect findings",
                status=step_status,
            )
        ],
        started_at=FIXED_TIME if terminal else None,
        finished_at=FIXED_TIME if terminal else None,
        completed_steps=completed_steps,
        failed_steps=failed_steps,
        simulated=simulated,
    )
    if execution_mode is not None:
        receipt.execution_mode = execution_mode
    return receipt


def make_validation(
    *,
    request_id="runtime-result-1",
    operation_outcome=ExecutionStatus.COMPLETED,
    status=ConformanceStatus.PASSED,
):
    return ExecutionConformanceResult(
        request_id=request_id,
        status=status,
        operation_outcome=operation_outcome,
        checks=tuple(
            ConformanceCheck(
                name=name,
                status=status,
                evidence=f"{name.value} test evidence.",
            )
            for name in ConformanceCheckName
        ),
    )


@pytest.mark.parametrize(
    ("missing_artifact", "message"),
    [
        pytest.param(
            "analysis",
            "analysis must be CognitiveRequestResult",
            id="analysis-none",
        ),
        pytest.param(
            "execution",
            "execution must be ExecutionReceipt",
            id="execution-none",
        ),
        pytest.param(
            "validation",
            "validation must be ExecutionConformanceResult",
            id="validation-none",
        ),
    ],
)
def test_runtime_conformance_error_rejects_missing_evidence(
    missing_artifact,
    message,
):
    arguments = {
        "request_id": "runtime-result-1",
        "analysis": make_result(),
        "execution": make_receipt(),
        "validation": make_validation(status=ConformanceStatus.FAILED),
    }
    arguments[missing_artifact] = None

    with pytest.raises(TypeError, match=message):
        RuntimeConformanceError(**arguments)


@pytest.mark.parametrize(
    "values",
    [
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": make_receipt(),
                "execution_requested": False,
                "execution_performed": True,
            },
            id="receipt-without-execution-request",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": make_receipt(),
                "execution_requested": True,
                "execution_performed": False,
            },
            id="receipt-without-performed-state",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.ANALYZED,
                "execution": None,
                "execution_requested": False,
                "execution_performed": True,
            },
            id="performed-without-receipt",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.FAILED,
                "analysis": make_result(ready=False),
                "execution": make_receipt(),
                "execution_requested": True,
                "execution_performed": True,
            },
            id="receipt-with-non-ready-analysis",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": None,
                "execution_requested": True,
                "execution_performed": False,
            },
            id="completed-without-receipt",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": None,
                "execution_requested": False,
                "execution_performed": False,
            },
            id="completed-without-request",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.ANALYZED,
                "execution": make_receipt(),
                "execution_requested": True,
                "execution_performed": True,
            },
            id="analyzed-with-receipt",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.FAILED,
                "execution": make_receipt(),
                "execution_requested": True,
                "execution_performed": True,
            },
            id="failed-with-completed-receipt",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": make_receipt(status=ExecutionStatus.FAILED),
                "execution_requested": True,
                "execution_performed": True,
            },
            id="completed-with-failed-receipt",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": make_receipt(request_id="different-request"),
                "execution_requested": True,
                "execution_performed": True,
            },
            id="receipt-request-id-mismatch",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": make_receipt(),
                "execution_requested": True,
                "execution_performed": True,
                "simulated": False,
            },
            id="non-simulated-runtime-with-receipt",
        ),
        pytest.param(
            {
                "status": CanonicalRuntimeStatus.COMPLETED,
                "execution": make_receipt(execution_mode="simulated"),
                "execution_requested": True,
                "execution_performed": True,
            },
            id="untyped-simulation-mode",
        ),
    ],
)
def test_canonical_result_rejects_contradictory_states(values):
    arguments = {
        "request_id": "runtime-result-1",
        "status": CanonicalRuntimeStatus.ANALYZED,
        "analysis": make_result(),
        "execution": None,
        "execution_requested": False,
        "execution_performed": False,
        **values,
    }

    with pytest.raises(CanonicalRuntimeInvariantError):
        CanonicalRuntimeResult(**arguments)


@pytest.mark.parametrize("request_id", ["", " ", "   ", "\t", "\n"])
def test_canonical_result_rejects_blank_request_id(request_id):
    with pytest.raises(
        CanonicalRuntimeInvariantError,
        match="request_id cannot be empty",
    ):
        CanonicalRuntimeResult(
            request_id=request_id,
            status=CanonicalRuntimeStatus.ANALYZED,
            analysis=make_result(),
            execution=None,
            execution_requested=False,
            execution_performed=False,
        )


@pytest.mark.parametrize(
    "receipt_status",
    [
        ExecutionStatus.PENDING,
        ExecutionStatus.READY,
        ExecutionStatus.RUNNING,
        ExecutionStatus.WAITING,
    ],
)
def test_canonical_result_rejects_nonterminal_execution_receipt(
    receipt_status,
):
    with pytest.raises(
        CanonicalRuntimeInvariantError,
        match="terminal status",
    ):
        CanonicalRuntimeResult(
            request_id="runtime-result-1",
            status=CanonicalRuntimeStatus.FAILED,
            analysis=make_result(),
            execution=make_receipt(status=receipt_status),
            execution_requested=True,
            execution_performed=True,
        )


def test_cancelled_receipt_is_terminal_and_maps_to_failed():
    result = CanonicalRuntimeResult(
        request_id="runtime-result-1",
        status=CanonicalRuntimeStatus.FAILED,
        analysis=make_result(),
        execution=make_receipt(status=ExecutionStatus.CANCELLED),
        execution_requested=True,
        execution_performed=True,
        validation=make_validation(
            operation_outcome=ExecutionStatus.CANCELLED,
        ),
    )

    assert result.execution.status is ExecutionStatus.CANCELLED
    assert result.status is CanonicalRuntimeStatus.FAILED


def test_analysis_only_runs_once_and_never_constructs_execution(
    monkeypatch,
):
    pipeline = CountingPipeline()
    engine = CountingExecutionEngine()
    validator = CountingConformanceValidator()
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=engine,
        conformance_validator=validator,
    )

    def fail_if_adapted(*args, **kwargs):
        raise AssertionError("execution request must not be constructed")

    monkeypatch.setattr(
        runtime_module,
        "build_execution_request",
        fail_if_adapted,
    )

    result = runtime.run(
        "Research competitors",
        "runtime-analysis-1",
        execute=False,
    )

    assert isinstance(result, CanonicalRuntimeResult)
    assert result.status is CanonicalRuntimeStatus.ANALYZED
    assert result.execution_requested is False
    assert result.execution_performed is False
    assert result.execution is None
    assert result.validation.status is LifecycleStageStatus.NOT_REQUESTED
    assert pipeline.calls == 1
    assert engine.requests == []
    assert validator.calls == []


def test_execution_uses_same_result_type_and_propagates_request():
    pipeline = CountingPipeline(result=make_result())
    events = []
    engine = CountingExecutionEngine(events)
    validator = CountingConformanceValidator(events)
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=engine,
        conformance_validator=validator,
    )

    result = runtime.run(
        "Research competitors",
        "runtime-execution-1",
        execute=True,
    )

    assert isinstance(result, CanonicalRuntimeResult)
    assert result.status is CanonicalRuntimeStatus.COMPLETED
    assert result.request_id == "runtime-execution-1"
    assert result.execution.request_id == "runtime-execution-1"
    assert result.validation.status is ConformanceStatus.PASSED
    assert engine.requests[0].request_id == "runtime-execution-1"
    assert pipeline.calls == 1
    assert len(validator.calls) == 1
    assert validator.calls[0]["receipt"] is result.execution
    assert events == ["execution", "validation"]
    assert [step.order for step in engine.requests[0].workflow_steps] == [
        1,
        2,
    ]
    assert result.analysis is pipeline.result
    assert result.governance.status is LifecycleStageStatus.NOT_IMPLEMENTED
    assert result.evaluation.status is LifecycleStageStatus.NOT_IMPLEMENTED
    assert result.learning.status is LifecycleStageStatus.NOT_IMPLEMENTED


def test_failed_analysis_never_invokes_execution_engine():
    pipeline = CountingPipeline(result=make_result(ready=False))
    engine = CountingExecutionEngine()
    validator = CountingConformanceValidator()
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=engine,
        conformance_validator=validator,
    )

    result = runtime.run(
        "Plan a launch",
        "runtime-no-match-1",
        execute=True,
    )

    assert result.status is CanonicalRuntimeStatus.FAILED
    assert result.execution_requested is True
    assert result.execution_performed is False
    assert result.execution is None
    assert result.analysis.metadata["failure_code"] == "no_capability_match"
    assert result.validation.status is LifecycleStageStatus.NOT_REQUESTED
    assert pipeline.calls == 1
    assert engine.requests == []
    assert validator.calls == []


def test_execution_failure_remains_structured():
    pipeline = CountingPipeline(result=make_result(failure=True))
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=ExecutionEngine(clock=lambda: FIXED_TIME),
    )

    result = runtime.run(
        "Research competitors",
        "runtime-failure-1",
        execute=True,
    )

    assert result.status is CanonicalRuntimeStatus.FAILED
    assert result.execution.status is ExecutionStatus.FAILED
    assert result.validation.status is ConformanceStatus.PASSED
    assert result.validation.operation_outcome is ExecutionStatus.FAILED
    assert result.execution.failed_steps == 1
    assert result.execution.steps[1].error
    assert result.to_dict()["execution"]["status"] == "failed"


def test_canonical_path_does_not_invoke_future_lifecycle_stages(
    monkeypatch,
):
    from aegis_os.evaluation.evaluation_engine import EvaluationEngine
    from aegis_os.learning.learning_engine import LearningEngine

    monkeypatch.setattr(
        EvaluationEngine,
        "evaluate",
        lambda *args, **kwargs: pytest.fail("evaluation must not run"),
    )
    monkeypatch.setattr(
        LearningEngine,
        "learn",
        lambda *args, **kwargs: pytest.fail("learning must not run"),
    )

    runtime = CognitiveRuntime(pipeline=CountingPipeline())
    result = runtime.run(
        "Research competitors",
        "runtime-no-future-stages-1",
    )

    assert result.governance.status is LifecycleStageStatus.NOT_IMPLEMENTED
    assert result.evaluation.status is LifecycleStageStatus.NOT_IMPLEMENTED
    assert result.learning.status is LifecycleStageStatus.NOT_IMPLEMENTED


def test_complete_canonical_envelope_serializes():
    runtime = CognitiveRuntime(
        pipeline=CountingPipeline(result=make_result()),
        execution_engine=CountingExecutionEngine(),
    )

    result = runtime.run(
        "Research competitors",
        "runtime-envelope-1",
        execute=True,
    )
    payload = result.to_dict()

    assert payload == {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "request_id": "runtime-envelope-1",
        "status": "completed",
        "analysis": {
            **result.analysis.to_dict(),
            "request_id": "runtime-envelope-1",
        },
        "execution": result.execution.to_dict(),
        "execution_requested": True,
        "execution_performed": True,
        "simulated": True,
        "validation": result.validation.to_dict(),
        "governance": {
            "status": "not_implemented",
            "detail": ("Governance is not implemented in the canonical runtime."),
        },
        "evaluation": {
            "status": "not_implemented",
            "detail": ("Evaluation is not implemented in the canonical runtime."),
        },
        "learning": {
            "status": "not_implemented",
            "detail": ("Learning is not implemented in the canonical runtime."),
        },
    }
    json.dumps(payload)


def test_canonical_result_rejects_execution_without_validation():
    with pytest.raises(
        CanonicalRuntimeInvariantError,
        match="require conformance validation",
    ):
        CanonicalRuntimeResult(
            request_id="runtime-result-1",
            status=CanonicalRuntimeStatus.COMPLETED,
            analysis=make_result(),
            execution=make_receipt(),
            execution_requested=True,
            execution_performed=True,
        )


def test_canonical_result_rejects_validation_without_execution():
    with pytest.raises(
        CanonicalRuntimeInvariantError,
        match="require validation not_requested",
    ):
        CanonicalRuntimeResult(
            request_id="runtime-result-1",
            status=CanonicalRuntimeStatus.ANALYZED,
            analysis=make_result(),
            execution=None,
            execution_requested=False,
            execution_performed=False,
            validation=make_validation(),
        )


@pytest.mark.parametrize(
    ("validation", "message"),
    [
        pytest.param(
            make_validation(request_id="different-request"),
            "request_id must match",
            id="validation-request-id-mismatch",
        ),
        pytest.param(
            make_validation(operation_outcome=ExecutionStatus.FAILED),
            "outcome must match",
            id="validation-outcome-mismatch",
        ),
    ],
)
def test_canonical_result_rejects_contradictory_validation(
    validation,
    message,
):
    with pytest.raises(CanonicalRuntimeInvariantError, match=message):
        CanonicalRuntimeResult(
            request_id="runtime-result-1",
            status=CanonicalRuntimeStatus.COMPLETED,
            analysis=make_result(),
            execution=make_receipt(),
            execution_requested=True,
            execution_performed=True,
            validation=validation,
        )


def test_canonical_result_accepts_structured_failed_conformance():
    analysis = make_result()
    execution = make_receipt()
    validation = make_validation(status=ConformanceStatus.FAILED)
    result = CanonicalRuntimeResult(
        request_id="runtime-result-1",
        status=CanonicalRuntimeStatus.CONFORMANCE_FAILED,
        analysis=analysis,
        execution=execution,
        execution_requested=True,
        execution_performed=True,
        validation=validation,
    )
    payload = result.to_dict()

    assert result.analysis is analysis
    assert result.execution is execution
    assert result.validation is validation
    assert result.status is CanonicalRuntimeStatus.CONFORMANCE_FAILED
    assert result.execution.status is ExecutionStatus.COMPLETED
    assert result.validation.status is ConformanceStatus.FAILED
    assert payload["request_id"] == "runtime-result-1"
    assert payload["analysis"]["request_id"] == "runtime-result-1"
    assert payload["execution"]["request_id"] == "runtime-result-1"
    assert payload["validation"]["request_id"] == "runtime-result-1"
    assert payload["status"] == "conformance_failed"
    assert all(not check.passed for check in result.validation.checks)
    assert len(payload["validation"]["checks"]) == len(ConformanceCheckName)
    assert len(payload["validation"]["evidence"]) == len(ConformanceCheckName)
    json.dumps(payload)


def test_runtime_preserves_failed_conformance_evidence():
    pipeline = CountingPipeline(result=make_result())
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=ExecutionEngine(clock=lambda: FIXED_TIME),
        conformance_validator=FailedConformanceValidator(),
    )

    result = runtime.run(
        "Research competitors",
        "runtime-conformance-failure-1",
        execute=True,
    )
    failed_checks = [check for check in result.validation.checks if not check.passed]

    assert pipeline.calls == 1
    assert isinstance(result, CanonicalRuntimeResult)
    assert result.status is CanonicalRuntimeStatus.CONFORMANCE_FAILED
    assert result.analysis is pipeline.result
    assert result.execution.status is ExecutionStatus.COMPLETED
    assert result.validation.status is ConformanceStatus.FAILED
    assert result.validation.operation_outcome is ExecutionStatus.COMPLETED
    assert tuple(check.name for check in result.validation.checks) == tuple(
        ConformanceCheckName
    )
    assert all(check.evidence for check in result.validation.checks)
    assert len(result.validation.to_dict()["evidence"]) == len(ConformanceCheckName)
    assert len(failed_checks) == 1
    assert "mission-preservation mismatch" in failed_checks[0].evidence
    payload = result.to_dict()
    assert payload["request_id"] == "runtime-conformance-failure-1"
    assert payload["analysis"]["request_id"] == payload["request_id"]
    assert payload["execution"]["request_id"] == payload["request_id"]
    assert payload["validation"]["request_id"] == payload["request_id"]
    json.dumps(payload)


def test_legacy_cognitive_loop_remains_available():
    orchestrator = StubLegacyOrchestrator()
    runtime = CognitiveRuntime(orchestrator=orchestrator)

    runtime.start()
    result = runtime.process_goal("Preserve legacy compatibility")

    assert orchestrator.goals == ["Preserve legacy compatibility"]
    assert result == {
        "goal": "Preserve legacy compatibility",
        "simulation": True,
    }


def test_runtime_rejects_validation_request_correlation_mismatch():
    runtime = CognitiveRuntime(
        pipeline=CountingPipeline(result=make_result()),
        execution_engine=ExecutionEngine(clock=lambda: FIXED_TIME),
        conformance_validator=MismatchedConformanceValidator(),
    )

    with pytest.raises(
        CanonicalRuntimeInvariantError,
        match="request_id must match",
    ):
        runtime.run(
            "Research competitors",
            "runtime-correlation-1",
            execute=True,
        )
