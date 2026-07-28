from __future__ import annotations

from typing import Any

from aegis_benchmark.models import (
    BenchmarkActual,
    BenchmarkCase,
    BenchmarkResult,
    CriterionResult,
)
from aegis_benchmark.scoring import calculate_case_score

EXECUTION_CRITERIA = {"execution_status", "simulated"}


class BenchmarkEvaluator:
    def evaluate(
        self,
        case: BenchmarkCase,
        actual: BenchmarkActual,
        *,
        include_execution: bool = True,
    ) -> BenchmarkResult:
        criteria: list[CriterionResult] = []
        expected_values = case.expected.to_dict()

        for criterion, expected in expected_values.items():
            if not include_execution and criterion in EXECUTION_CRITERIA:
                continue
            actual_value = getattr(actual, criterion)
            criteria.append(
                CriterionResult(
                    criterion=criterion,
                    expected=expected,
                    actual=actual_value,
                    passed=self._matches(
                        criterion,
                        expected,
                        actual_value,
                    ),
                )
            )

        score = calculate_case_score(criteria)
        return BenchmarkResult(
            case_id=case.id,
            title=case.title,
            category=case.category,
            passed=bool(criteria) and all(item.passed for item in criteria),
            score=score,
            criteria=criteria,
            actual=actual,
        )

    @staticmethod
    def _matches(criterion: str, expected: Any, actual: Any) -> bool:
        if criterion == "required_capabilities":
            return sorted(expected) == sorted(actual)
        return expected == actual
