import json
from datetime import UTC, datetime

import pytest

import aegis_os.core.cognitive_runtime as runtime_module
from aegis_os.core.cognitive_runtime import (
    CanonicalRuntimeResult,
    CanonicalRuntimeStatus,
    CognitiveRuntime,
)
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import ExecutionStatus
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
    def __init__(self):
        self.delegate = ExecutionEngine(clock=lambda: FIXED_TIME)
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self.delegate.execute(request)


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
                ),
                WorkflowStep(1, "Collect", "Collect findings"),
            ]
            if ready
            else []
        ),
        status=PipelineStatus.READY if ready else PipelineStatus.FAILED,
        metadata=({} if ready else {"failure_code": "no_capability_match"}),
    )


def test_analysis_only_runs_once_and_never_constructs_execution(
    monkeypatch,
):
    pipeline = CountingPipeline()
    engine = CountingExecutionEngine()
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=engine,
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
    assert pipeline.calls == 1
    assert engine.requests == []


def test_execution_uses_same_result_type_and_propagates_request():
    pipeline = CountingPipeline(result=make_result())
    engine = CountingExecutionEngine()
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=engine,
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
    assert engine.requests[0].request_id == "runtime-execution-1"
    assert pipeline.calls == 1
    assert [step.order for step in engine.requests[0].workflow_steps] == [
        1,
        2,
    ]
    assert result.analysis is pipeline.result
    assert result.governance is None
    assert result.evaluation is None
    assert result.learning is None
    json.dumps(result.to_dict())


def test_failed_analysis_never_invokes_execution_engine():
    pipeline = CountingPipeline(result=make_result(ready=False))
    engine = CountingExecutionEngine()
    runtime = CognitiveRuntime(
        pipeline=pipeline,
        execution_engine=engine,
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
    assert pipeline.calls == 1
    assert engine.requests == []


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

    assert result.governance is None
    assert result.evaluation is None
    assert result.learning is None
