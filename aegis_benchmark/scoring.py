from __future__ import annotations

from collections import defaultdict
from typing import Any

from aegis_benchmark.models import (
    BENCHMARK_VERSION,
    BenchmarkResult,
    BenchmarkRunSummary,
    CriterionResult,
)

METRIC_CRITERIA = {
    "intent_accuracy": {"primary_intent"},
    "capability_accuracy": {"required_capabilities"},
    "agent_selection_accuracy": {"selected_agent"},
    "workflow_accuracy": {
        "workflow_step_count",
        "workflow_order_valid",
    },
    "analysis_status_accuracy": {"analysis_status"},
    "execution_accuracy": {"execution_status"},
    "simulation_compliance_accuracy": {"simulated"},
}


def percentage(passed: int, total: int) -> float:
    return round((passed / total) * 100, 2) if total else 0.0


def calculate_case_score(criteria: list[CriterionResult]) -> float:
    return percentage(
        sum(criterion.passed for criterion in criteria),
        len(criteria),
    )


def calculate_summary(
    results: list[BenchmarkResult],
    *,
    suite: str = "AEGIS Benchmark Suite",
    version: str = BENCHMARK_VERSION,
) -> BenchmarkRunSummary:
    all_criteria = [criterion for result in results for criterion in result.criteria]
    metrics = {
        name: _criteria_accuracy(all_criteria, criterion_names)
        for name, criterion_names in METRIC_CRITERIA.items()
    }

    category_results: dict[str, list[BenchmarkResult]] = defaultdict(list)
    for result in results:
        category_results[result.category].append(result)
    category_breakdown: dict[str, dict[str, Any]] = {}
    for category in sorted(category_results):
        items = category_results[category]
        category_criteria = [criterion for item in items for criterion in item.criteria]
        category_breakdown[category] = {
            "total_cases": len(items),
            "passed_cases": sum(item.passed for item in items),
            "failed_cases": sum(not item.passed for item in items),
            "score": percentage(
                sum(item.passed for item in category_criteria),
                len(category_criteria),
            ),
        }

    return BenchmarkRunSummary(
        suite=suite,
        version=version,
        total_cases=len(results),
        passed_cases=sum(result.passed for result in results),
        failed_cases=sum(not result.passed for result in results),
        overall_score=percentage(
            sum(criterion.passed for criterion in all_criteria),
            len(all_criteria),
        ),
        category_breakdown=category_breakdown,
        results=results,
        **metrics,
    )


def _criteria_accuracy(
    criteria: list[CriterionResult],
    criterion_names: set[str],
) -> float:
    selected = [
        criterion for criterion in criteria if criterion.criterion in criterion_names
    ]
    return percentage(
        sum(criterion.passed for criterion in selected),
        len(selected),
    )
