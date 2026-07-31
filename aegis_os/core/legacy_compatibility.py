from __future__ import annotations

from typing import Any

from aegis_os.core.cognitive_runtime import CognitiveRuntime


class LegacyCompatibilityAdapter:
    """Preserve the historical cognitive-loop boundary explicitly."""

    def __init__(
        self,
        runtime: CognitiveRuntime | None = None,
    ) -> None:
        self._runtime = runtime

    @property
    def runtime(self) -> CognitiveRuntime:
        """Construct the historical runtime only when requested."""

        if self._runtime is None:
            self._runtime = CognitiveRuntime()
        return self._runtime

    def start(self) -> None:
        """Start the historical runtime at most when it is needed."""

        runtime = self.runtime
        if runtime.state != "running":
            runtime.start()

    def process_goal(self, goal: str) -> Any:
        """Delegate one historical goal without adding cognitive logic."""

        self.start()
        return self.runtime.process_goal(goal)
