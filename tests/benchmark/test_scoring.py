from aegis_benchmark.models import BenchmarkResult, CriterionResult
from aegis_benchmark.scoring import (
    calculate_case_score,
    calculate_summary,
    percentage,
)


def test_case_score_uses_passed_declared_criteria():
    criteria = [
        CriterionResult("one", 1, 1, True),
        CriterionResult("two", 2, 3, False),
        CriterionResult("three", 3, 3, True),
    ]

    assert calculate_case_score(criteria) == 66.67


def test_summary_calculates_metrics_and_categories():
    result = BenchmarkResult(
        "case",
        "Case",
        "research",
        False,
        50.0,
        [
            CriterionResult("primary_intent", "research", "research", True),
            CriterionResult(
                "selected_agent",
                "Research Agent",
                "Analysis Agent",
                False,
            ),
        ],
    )

    summary = calculate_summary([result])

    assert summary.overall_score == 50.0
    assert summary.intent_accuracy == 100.0
    assert summary.agent_selection_accuracy == 0.0
    assert summary.category_breakdown["research"]["failed_cases"] == 1


def test_zero_denominators_are_safe():
    summary = calculate_summary([])

    assert percentage(0, 0) == 0.0
    assert summary.overall_score == 0.0
    assert summary.execution_accuracy == 0.0
