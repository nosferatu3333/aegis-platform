from __future__ import annotations

from typing import Any

from aegis_os.core.cognitive_runtime import (
    CanonicalRuntimeResult,
    CognitiveRuntime,
)
from aegis_os.core.events import Event
from aegis_os.core.legacy_compatibility import (
    LegacyCompatibilityAdapter,
)


class Kernel:
    """Aegis OS central cognitive entry boundary."""

    def __init__(
        self,
        cognitive_runtime: CognitiveRuntime | None = None,
        legacy_compatibility: LegacyCompatibilityAdapter | None = None,
    ) -> None:
        self.name = "Aegis Kernel"
        self.version = "0.3.0"
        self.state = "created"

        if cognitive_runtime is None:
            from aegis_os.pipeline.composition import (
                create_default_runtime,
            )

            cognitive_runtime = create_default_runtime()

        self.cognitive_runtime = cognitive_runtime
        self.legacy_compatibility = legacy_compatibility or LegacyCompatibilityAdapter()

    def boot(self) -> None:
        self.state = "running"

        print(f"{self.name} v{self.version}")
        print("Kernel state:", self.state)
        print("Aegis OS online.")

        self.cognitive_runtime.start()

    def create_event(
        self,
        event_type: str,
        data: Any = None,
    ) -> Event:
        return Event(event_type, data)

    def process_task(
        self,
        task: str,
        request_id: str,
        *,
        execute: bool = False,
    ) -> CanonicalRuntimeResult:
        """Route a task through the canonical typed runtime."""

        return self.cognitive_runtime.run(
            task,
            request_id,
            execute=execute,
        )

    def process_goal(self, goal: str) -> Any:
        """Preserve the historical goal contract through its adapter."""

        return self.legacy_compatibility.process_goal(goal)
