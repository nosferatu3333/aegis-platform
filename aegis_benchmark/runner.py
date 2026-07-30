from __future__ import annotations

from datetime import UTC, datetime

from aegis_benchmark.evaluator import BenchmarkEvaluator
from aegis_benchmark.models import (
    BenchmarkActual,
    BenchmarkCase,
    BenchmarkResult,
    BenchmarkRunSummary,
)
from aegis_benchmark.scoring import calculate_summary
from aegis_os.core.cognitive_runtime import CognitiveRuntime
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.pipeline.composition import create_default_runtime
from aegis_os.pipeline.models import PipelineStatus
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

BENCHMARK_TIME = datetime(2000, 1, 1, tzinfo=UTC)


class BenchmarkRunner:
    def __init__(
        self,
        pipeline: CognitiveRequestPipeline | None = None,
        execution_engine: ExecutionEngine | None = None,
        evaluator: BenchmarkEvaluator | None = None,
        runtime: CognitiveRuntime | None = None,
        *,
        execute: bool = True,
    ) -> None:
        benchmark_engine = execution_engine or ExecutionEngine(
            clock=lambda: BENCHMARK_TIME
        )
        if runtime is not None:
            self.runtime = runtime
        elif pipeline is not None:
            self.runtime = CognitiveRuntime(
                pipeline=pipeline,
                execution_engine=benchmark_engine,
            )
        else:
            self.runtime = create_default_runtime(
                execution_engine=benchmark_engine,
            )
        self.evaluator = evaluator or BenchmarkEvaluator()
        self.execute = execute

    def run_case(self, case: BenchmarkCase) -> BenchmarkResult:
        wants_execution = (
            case.expected.execution_status is not None
            or case.expected.simulated is not None
        )
        runtime_result = self.runtime.run(
            case.mission,
            request_id=f"benchmark-{case.id}",
            execute=self.execute and wants_execution,
        )
        analysis = runtime_result.analysis
        analysis_payload = analysis.to_dict()
        receipt_payload = (
            runtime_result.execution.to_dict() if runtime_result.execution else None
        )

        orders = [step.order for step in analysis.workflow]
        actual = BenchmarkActual(
            primary_intent=analysis.intent.primary_intent,
            required_capabilities=list(analysis.intent.required_capabilities),
            selected_agent=(
                analysis.capability.name
                if analysis.status is PipelineStatus.READY
                else None
            ),
            capability_id=analysis.capability.capability_id,
            workflow_step_count=len(analysis.workflow),
            workflow_orders=orders,
            workflow_order_valid=orders == list(range(1, len(orders) + 1)),
            analysis_status=analysis.status.value,
            execution_status=(receipt_payload["status"] if receipt_payload else None),
            simulated=(receipt_payload["simulated"] if receipt_payload else None),
            failure_code=analysis.metadata.get("failure_code"),
            analysis=analysis_payload,
            execution_receipt=receipt_payload,
        )
        return self.evaluator.evaluate(
            case,
            actual,
            include_execution=self.execute,
        )

    def run_suite(
        self,
        cases: list[BenchmarkCase],
    ) -> BenchmarkRunSummary:
        results = [self.run_case(case) for case in cases if case.enabled]
        return calculate_summary(results)
