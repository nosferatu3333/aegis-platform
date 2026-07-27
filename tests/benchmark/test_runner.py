from aegis_benchmark.loader import load_benchmark_directory
from aegis_benchmark.models import BenchmarkCase, BenchmarkExpectation
from aegis_benchmark.runner import BenchmarkRunner


def test_runner_uses_real_pipeline_for_research_case():
    case = BenchmarkCase(
        "research",
        "Research",
        "research",
        "easy",
        "Research autonomous intelligence systems",
        BenchmarkExpectation(
            primary_intent="research",
            required_capabilities=["research"],
            selected_agent="Research Agent",
            workflow_step_count=5,
            workflow_order_valid=True,
            analysis_status="ready",
        ),
    )

    result = BenchmarkRunner().run_case(case)

    assert result.passed is True
    assert result.actual.selected_agent == "Research Agent"
    assert result.actual.workflow_orders == [1, 2, 3, 4, 5]


def test_runner_preserves_unsupported_no_match_behavior():
    case = BenchmarkCase(
        "unsupported",
        "Unsupported",
        "unsupported",
        "easy",
        "Plan a product launch roadmap",
        BenchmarkExpectation(
            analysis_status="failed",
            failure_code="no_capability_match",
            workflow_step_count=0,
        ),
    )

    result = BenchmarkRunner().run_case(case)

    assert result.passed is True
    assert result.actual.selected_agent is None
    assert result.actual.execution_receipt is None


def test_runner_reuses_simulated_execution_engine():
    case = BenchmarkCase(
        "execution",
        "Execution",
        "execution",
        "easy",
        "Analyze market risk",
        BenchmarkExpectation(
            selected_agent="Analysis Agent",
            execution_status="completed",
            simulated=True,
        ),
    )

    result = BenchmarkRunner().run_case(case)

    assert result.passed is True
    assert result.actual.execution_receipt["completed_steps"] == 5
    assert result.actual.execution_receipt["simulated"] is True


def test_initial_suite_passes_and_has_expected_category_counts():
    cases = load_benchmark_directory("benchmarks/missions")

    summary = BenchmarkRunner().run_suite(cases)

    assert summary.total_cases == 17
    assert summary.passed_cases == 17
    assert {
        category: values["total_cases"]
        for category, values in summary.category_breakdown.items()
    } == {
        "analysis": 5,
        "execution": 3,
        "research": 6,
        "unsupported": 3,
    }
