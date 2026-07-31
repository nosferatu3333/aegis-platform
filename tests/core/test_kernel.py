from __future__ import annotations

from typing import Any

from aegis_os.core.cognitive_runtime import (
    CanonicalRuntimeResult,
    CanonicalRuntimeStatus,
)
from aegis_os.core.kernel import Kernel
from aegis_os.core.legacy_compatibility import (
    LegacyCompatibilityAdapter,
)


class StubCanonicalRuntime:
    def __init__(self, result: Any | None = None) -> None:
        self.result = result if result is not None else object()
        self.started = False
        self.calls: list[tuple[str, str, bool]] = []

    def start(self) -> None:
        self.started = True

    def run(
        self,
        task: str,
        request_id: str,
        *,
        execute: bool = False,
    ) -> Any:
        self.calls.append((task, request_id, execute))
        return self.result


class StubLegacyCompatibility:
    def __init__(self, result: Any | None = None) -> None:
        self.result = result if result is not None else object()
        self.started = False
        self.goals: list[str] = []

    def start(self) -> None:
        self.started = True

    def process_goal(self, goal: str) -> Any:
        self.goals.append(goal)
        return self.result


class StubLegacyRuntime:
    def __init__(self) -> None:
        self.state = "initialized"
        self.start_calls = 0
        self.goals: list[str] = []

    def start(self) -> None:
        self.start_calls += 1
        self.state = "running"

    def process_goal(self, goal: str) -> dict[str, object]:
        self.goals.append(goal)
        return {
            "goal": goal,
            "simulation": True,
        }


def test_kernel_boot_starts_only_canonical_boundary() -> None:
    canonical_runtime = StubCanonicalRuntime()
    legacy_compatibility = StubLegacyCompatibility()
    kernel = Kernel(
        cognitive_runtime=canonical_runtime,
        legacy_compatibility=legacy_compatibility,
    )

    kernel.boot()

    assert kernel.state == "running"
    assert canonical_runtime.started is True
    assert legacy_compatibility.started is False


def test_kernel_routes_analysis_only_request_to_canonical_runtime() -> None:
    expected_result = object()
    canonical_runtime = StubCanonicalRuntime(expected_result)
    kernel = Kernel(
        cognitive_runtime=canonical_runtime,
        legacy_compatibility=StubLegacyCompatibility(),
    )

    result = kernel.process_task(
        "Research competitors",
        "kernel-analysis-1",
    )

    assert result is expected_result
    assert canonical_runtime.calls == [
        ("Research competitors", "kernel-analysis-1", False)
    ]


def test_kernel_routes_simulated_execution_request() -> None:
    expected_result = object()
    canonical_runtime = StubCanonicalRuntime(expected_result)
    kernel = Kernel(
        cognitive_runtime=canonical_runtime,
        legacy_compatibility=StubLegacyCompatibility(),
    )

    result = kernel.process_task(
        "Research competitors",
        "kernel-execution-1",
        execute=True,
    )

    assert result is expected_result
    assert canonical_runtime.calls == [
        ("Research competitors", "kernel-execution-1", True)
    ]


def test_kernel_process_goal_uses_legacy_compatibility_adapter() -> None:
    expected_result = object()
    legacy_compatibility = StubLegacyCompatibility(expected_result)
    kernel = Kernel(
        cognitive_runtime=StubCanonicalRuntime(),
        legacy_compatibility=legacy_compatibility,
    )

    result = kernel.process_goal("Preserve legacy compatibility")

    assert result is expected_result
    assert legacy_compatibility.goals == ["Preserve legacy compatibility"]


def test_legacy_adapter_starts_runtime_lazily_once() -> None:
    legacy_runtime = StubLegacyRuntime()
    adapter = LegacyCompatibilityAdapter(runtime=legacy_runtime)

    first_result = adapter.process_goal("First legacy goal")
    second_result = adapter.process_goal("Second legacy goal")

    assert legacy_runtime.start_calls == 1
    assert legacy_runtime.goals == [
        "First legacy goal",
        "Second legacy goal",
    ]
    assert first_result["goal"] == "First legacy goal"
    assert second_result["goal"] == "Second legacy goal"


def test_default_kernel_returns_canonical_analysis_result() -> None:
    kernel = Kernel()

    result = kernel.process_task(
        "Research competitors",
        "kernel-default-analysis-1",
    )

    assert isinstance(result, CanonicalRuntimeResult)
    assert result.request_id == "kernel-default-analysis-1"
    assert result.status is CanonicalRuntimeStatus.ANALYZED
    assert result.execution_requested is False
    assert result.execution_performed is False


def test_default_kernel_routes_simulated_execution() -> None:
    kernel = Kernel()

    result = kernel.process_task(
        "Research competitors",
        "kernel-default-execution-1",
        execute=True,
    )

    assert isinstance(result, CanonicalRuntimeResult)
    assert result.request_id == "kernel-default-execution-1"
    assert result.status is CanonicalRuntimeStatus.COMPLETED
    assert result.execution_requested is True
    assert result.execution_performed is True
    assert result.simulated is True
