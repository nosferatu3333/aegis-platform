from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


BENCHMARK_VERSION = "0.1"


@dataclass
class BenchmarkExpectation:
    primary_intent: str | None = None
    required_capabilities: list[str] | None = None
    selected_agent: str | None = None
    workflow_step_count: int | None = None
    analysis_status: str | None = None
    execution_status: str | None = None
    simulated: bool | None = None
    failure_code: str | None = None
    workflow_order_valid: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in asdict(self).items()
            if value is not None
        }


@dataclass
class BenchmarkCase:
    id: str
    title: str
    category: str
    difficulty: str
    mission: str
    expected: BenchmarkExpectation
    tags: list[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected"] = self.expected.to_dict()
        return payload


@dataclass
class BenchmarkActual:
    primary_intent: str
    required_capabilities: list[str]
    selected_agent: str | None
    workflow_step_count: int
    workflow_orders: list[int]
    workflow_order_valid: bool
    analysis_status: str
    execution_status: str | None = None
    simulated: bool | None = None
    failure_code: str | None = None
    capability_id: str | None = None
    analysis: dict[str, Any] = field(default_factory=dict)
    execution_receipt: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CriterionResult:
    criterion: str
    expected: Any
    actual: Any
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkResult:
    case_id: str
    title: str
    category: str
    passed: bool
    score: float
    criteria: list[CriterionResult] = field(default_factory=list)
    actual: BenchmarkActual | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "category": self.category,
            "passed": self.passed,
            "score": self.score,
            "criteria": [
                criterion.to_dict() for criterion in self.criteria
            ],
            "actual": self.actual.to_dict() if self.actual else None,
        }


@dataclass
class BenchmarkRunSummary:
    suite: str
    version: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_score: float
    intent_accuracy: float
    capability_accuracy: float
    agent_selection_accuracy: float
    workflow_accuracy: float
    analysis_status_accuracy: float
    execution_accuracy: float
    simulation_compliance_accuracy: float
    category_breakdown: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )
    results: list[BenchmarkResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["results"] = [result.to_dict() for result in self.results]
        return payload
