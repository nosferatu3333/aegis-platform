from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aegis_os.pipeline.models import WorkflowStep


class WorkflowGenerator:
    """
    Converts capability workflow definitions into dashboard-ready steps.
    """

    DEFAULT_WORKFLOW: tuple[tuple[str, str], ...] = (
        (
            "Clarify the objective",
            "Define the intended outcome, constraints, and success criteria.",
        ),
        (
            "Analyze the mission",
            "Identify the information and operational requirements.",
        ),
        (
            "Prepare an approach",
            "Organize the mission into a coherent sequence of actions.",
        ),
        (
            "Execute the first increment",
            "Produce the smallest useful version of the requested outcome.",
        ),
        (
            "Evaluate the result",
            "Review the output and identify necessary refinements.",
        ),
    )

    def generate(
        self,
        capability_id: str,
        workflow_definition: Iterable[Any] | None = None,
    ) -> list[WorkflowStep]:
        raw_steps = list(workflow_definition or [])

        if not raw_steps:
            return self._default_steps(capability_id)

        workflow: list[WorkflowStep] = []

        for index, raw_step in enumerate(raw_steps, start=1):
            title, description = self._parse_step(raw_step, index)

            workflow.append(
                WorkflowStep(
                    order=index,
                    title=title,
                    description=description,
                    capability_id=capability_id,
                )
            )

        return workflow

    def _default_steps(self, capability_id: str) -> list[WorkflowStep]:
        return [
            WorkflowStep(
                order=index,
                title=title,
                description=description,
                capability_id=capability_id,
            )
            for index, (title, description) in enumerate(
                self.DEFAULT_WORKFLOW,
                start=1,
            )
        ]

    @staticmethod
    def _parse_step(raw_step: Any, index: int) -> tuple[str, str]:
        if isinstance(raw_step, str):
            clean_title = raw_step.strip()

            return (
                clean_title or f"Workflow step {index}",
                clean_title or "Execute the defined workflow step.",
            )

        if isinstance(raw_step, dict):
            title = str(
                raw_step.get("title")
                or raw_step.get("name")
                or f"Workflow step {index}"
            ).strip()

            description = str(
                raw_step.get("description") or raw_step.get("instruction") or title
            ).strip()

            return title, description

        title = (
            getattr(raw_step, "title", None)
            or getattr(raw_step, "action", None)
        )
        description = (
            getattr(raw_step, "description", None)
            or getattr(raw_step, "expected_result", None)
        )

        return (
            str(title or f"Workflow step {index}").strip(),
            str(description or title or "Execute workflow step.").strip(),
        )
