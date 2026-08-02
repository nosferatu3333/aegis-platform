from __future__ import annotations

from typing import Any, Protocol

from aegis_core.contracts import CapabilitySelection

from aegis_os.pipeline.bounded_planning_adapter import BoundedPlanningAdapter
from aegis_os.pipeline.intent_analyzer import IntentAnalyzer
from aegis_os.pipeline.models import (
    CapabilityMatch,
    CognitiveRequestResult,
    PipelineStatus,
)
from aegis_os.pipeline.workflow_generator import WorkflowGenerator


class CapabilitySelectorProtocol(Protocol):
    """Minimal selector interface required by the pipeline."""

    def select(self, task: str, **context: Any) -> Any: ...


class CognitiveRequestPipeline:
    """
    Coordinates mission interpretation, capability selection,
    and workflow generation.

    This is the first complete AEGIS MVP backend vertical slice.
    """

    def __init__(
        self,
        capability_selector: CapabilitySelectorProtocol,
        intent_analyzer: IntentAnalyzer | None = None,
        workflow_generator: WorkflowGenerator | None = None,
        bounded_planning_adapter: BoundedPlanningAdapter | None = None,
    ) -> None:
        self.capability_selector = capability_selector
        self.intent_analyzer = intent_analyzer or IntentAnalyzer()
        self.workflow_generator = workflow_generator or WorkflowGenerator()
        self.bounded_planning_adapter = (
            bounded_planning_adapter or BoundedPlanningAdapter()
        )

    def process_task(self, task: str) -> CognitiveRequestResult:
        clean_task = task.strip()

        if not clean_task:
            raise ValueError("Task cannot be empty.")

        intent = self.intent_analyzer.analyze(clean_task)

        selection = self.capability_selector.select(
            clean_task,
            intent=intent,
            required_capabilities=intent.required_capabilities,
        )

        capability = self._build_capability_match(selection)

        if selection is None:
            return CognitiveRequestResult(
                task=clean_task,
                intent=intent,
                capability=capability,
                workflow=[],
                status=PipelineStatus.FAILED,
                metadata={
                    "pipeline_version": "0.1.0",
                    "workflow_steps": 0,
                    "failure_code": "no_capability_match",
                    "failure_reason": (
                        "No registered profile matched the required capabilities."
                    ),
                },
            )

        workflow_definition = self._read_value(
            selection,
            "workflow",
            default=None,
        )

        if workflow_definition is None:
            selected_capability = self._read_value(
                selection,
                "capability",
                default=None,
            )

            workflow_definition = self._read_value(
                selected_capability,
                "workflow",
                default=None,
            )

        workflow = self.workflow_generator.generate(
            capability_id=capability.capability_id,
            workflow_definition=workflow_definition,
        )

        return CognitiveRequestResult(
            task=clean_task,
            intent=intent,
            capability=capability,
            workflow=workflow,
            status=PipelineStatus.READY,
            metadata={
                "pipeline_version": "0.3.0",
                "workflow_steps": len(workflow),
                "capability_source": self._read_value(
                    selection, "source", default="platform-internal"
                ),
                "capability_source_path": self._read_value(
                    selection, "source_path", default=None
                ),
            },
        )

    def process_selection(
        self,
        *,
        task: str,
        interpretation_id: str,
        selection: CapabilitySelection,
        workflow_definition: Any = None,
    ) -> CognitiveRequestResult:
        """Create a bounded, non-executing plan from a canonical selection."""

        clean_task = task.strip()
        if not clean_task:
            raise ValueError("Task cannot be empty.")

        intent = self.intent_analyzer.analyze(clean_task)
        capability = CapabilityMatch(
            capability_id=selection.capability_id,
            name=selection.capability_id,
            confidence=1.0,
            score=1.0,
            reasons=(selection.rationale,),
        )
        workflow = self.workflow_generator.generate(
            capability_id=selection.capability_id,
            workflow_definition=workflow_definition,
        )
        canonical_plan = self.bounded_planning_adapter.build(
            selection=selection,
            interpretation_id=interpretation_id,
            objective=clean_task,
            workflow=workflow,
            intent=intent,
        )

        return CognitiveRequestResult(
            task=clean_task,
            intent=intent,
            capability=capability,
            workflow=workflow,
            status=PipelineStatus.READY,
            metadata={
                "pipeline_version": "0.2.0",
                "workflow_steps": len(workflow),
                "planning_boundary": "bounded_non_executing",
            },
            canonical_plan=canonical_plan,
        )

    def _build_capability_match(
        self,
        selection: Any,
    ) -> CapabilityMatch:
        selected_capability = self._read_value(
            selection,
            "capability",
            default=selection,
        )

        selected_name = self._read_value(
            selected_capability,
            "name",
            default=None,
        )

        capability_id = str(
            self._read_value(
                selected_capability,
                "id",
                default=self._read_value(
                    selected_capability,
                    "capability_id",
                    default=selected_name or "unknown",
                ),
            )
        )

        name = str(selected_name or capability_id)

        raw_confidence = self._read_value(
            selection,
            "confidence",
            default=0.0,
        )

        raw_score = self._read_value(
            selection,
            "score",
            default=raw_confidence,
        )

        reasons = self._as_string_tuple(
            self._read_value(
                selection,
                "reasons",
                default=self._read_value(
                    selection,
                    "reason",
                    default=(),
                ),
            )
        )

        matched_tags = self._as_string_tuple(
            self._read_value(
                selection,
                "matched_tags",
                default=(),
            )
        )

        confidence = self._normalize_confidence(raw_confidence)

        return CapabilityMatch(
            capability_id=capability_id,
            name=name,
            confidence=confidence,
            score=float(raw_score or 0.0),
            reasons=reasons,
            matched_tags=matched_tags,
        )

    @staticmethod
    def _read_value(
        source: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(key, default)

        return getattr(source, key, default)

    @staticmethod
    def _as_string_tuple(value: Any) -> tuple[str, ...]:
        if value is None:
            return ()

        if isinstance(value, str):
            return (value,)

        try:
            return tuple(str(item) for item in value)
        except TypeError:
            return (str(value),)

    @staticmethod
    def _normalize_confidence(value: Any) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0

        if confidence > 1.0:
            confidence /= 100.0

        return max(0.0, min(confidence, 1.0))
