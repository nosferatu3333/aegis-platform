from aegis_benchmark.evaluator import BenchmarkEvaluator
from aegis_benchmark.models import (
    BenchmarkActual,
    BenchmarkCase,
    BenchmarkExpectation,
)


def make_actual():
    return BenchmarkActual(
        primary_intent="research",
        required_capabilities=["research"],
        selected_agent="Research Agent",
        workflow_step_count=5,
        workflow_orders=[1, 2, 3, 4, 5],
        workflow_order_valid=True,
        analysis_status="ready",
    )


def test_declared_criteria_are_evaluated_individually():
    case = BenchmarkCase(
        "case",
        "Case",
        "research",
        "easy",
        "Research systems",
        BenchmarkExpectation(
            primary_intent="research",
            selected_agent="Wrong Agent",
        ),
    )

    result = BenchmarkEvaluator().evaluate(case, make_actual())

    assert [item.criterion for item in result.criteria] == [
        "primary_intent",
        "selected_agent",
    ]
    assert [item.passed for item in result.criteria] == [True, False]
    assert result.score == 50.0
    assert result.passed is False


def test_omitted_expectations_do_not_affect_scoring():
    case = BenchmarkCase(
        "case",
        "Case",
        "research",
        "easy",
        "Research systems",
        BenchmarkExpectation(primary_intent="research"),
    )

    result = BenchmarkEvaluator().evaluate(case, make_actual())

    assert len(result.criteria) == 1
    assert result.score == 100.0


def test_required_capability_comparison_is_order_independent():
    actual = make_actual()
    actual.required_capabilities = ["analysis", "research"]
    case = BenchmarkCase(
        "case",
        "Case",
        "research",
        "easy",
        "Research systems",
        BenchmarkExpectation(required_capabilities=["research", "analysis"]),
    )

    assert BenchmarkEvaluator().evaluate(case, actual).passed is True
