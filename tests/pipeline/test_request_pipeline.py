import json

from aegis_os.agents.agent_profile import AgentProfile
from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.capability import Capability
from aegis_os.pipeline.agent_selector_adapter import AgentSelectorAdapter
from aegis_os.pipeline.models import PipelineStatus, TaskComplexity
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline


class FakeCapabilitySelector:
    def select(self, task: str, **context):
        return {
            "capability": {
                "id": "iterative_ai_development",
                "name": "Iterative AI Development",
                "workflow": [
                    {
                        "title": "Clarify the outcome",
                        "description": "Define what the user wants to achieve.",
                    },
                    {
                        "title": "Design the first increment",
                        "description": "Identify the smallest useful implementation.",
                    },
                    {
                        "title": "Implement",
                        "description": "Build the initial version.",
                    },
                    {
                        "title": "Review",
                        "description": "Evaluate the implementation.",
                    },
                    {
                        "title": "Refine",
                        "description": "Improve the result using review findings.",
                    },
                ],
            },
            "confidence": 0.91,
            "score": 12,
            "reasons": [
                "Development intent detected.",
                "The mission requires iterative planning.",
            ],
            "matched_tags": [
                "development",
                "planning",
                "iteration",
            ],
        }


def test_pipeline_returns_structured_result():
    pipeline = CognitiveRequestPipeline(capability_selector=FakeCapabilitySelector())

    result = pipeline.process_task("Help me build and launch an AI consulting business")

    assert result.status is PipelineStatus.READY
    assert result.task == ("Help me build and launch an AI consulting business")

    assert result.intent.primary_intent in {
        "development",
        "planning",
    }

    assert result.intent.requires_planning is True
    assert result.intent.complexity in {
        TaskComplexity.MEDIUM,
        TaskComplexity.HIGH,
    }

    assert result.capability.capability_id == "iterative_ai_development"

    assert result.capability.confidence == 0.91
    assert len(result.workflow) == 5
    assert result.workflow[0].order == 1


def test_pipeline_result_can_be_serialized():
    pipeline = CognitiveRequestPipeline(capability_selector=FakeCapabilitySelector())

    result = pipeline.process_task("Build a customer support workflow")

    serialized = result.to_dict()

    assert serialized["schema_version"] == "1.0"
    assert serialized["status"] == "ready"
    assert serialized["capability"]["confidence"] == 0.91
    assert serialized["workflow"][0]["order"] == 1


def test_pipeline_rejects_empty_task():
    pipeline = CognitiveRequestPipeline(capability_selector=FakeCapabilitySelector())

    try:
        pipeline.process_task("   ")
    except ValueError as error:
        assert str(error) == "Task cannot be empty."
    else:
        raise AssertionError("Expected ValueError for empty task.")


def test_pipeline_uses_real_registry_and_capability_matcher():
    registry = AgentRegistry()
    registry.register(
        AgentProfile(
            "Research Agent",
            [Capability("research"), Capability("knowledge")],
        )
    )
    registry.register(
        AgentProfile(
            "Analysis Agent",
            [Capability("analysis"), Capability("evaluation")],
        )
    )

    pipeline = CognitiveRequestPipeline(
        capability_selector=AgentSelectorAdapter(registry)
    )

    result = pipeline.process_task("Research autonomous intelligence systems")
    serialized = result.to_dict()

    assert result.intent.required_capabilities == ("research",)
    assert result.capability.name == "Research Agent"
    assert result.capability.capability_id == "Research Agent"
    assert result.workflow
    assert all(step.capability_id == "Research Agent" for step in result.workflow)
    parsed = json.loads(json.dumps(serialized))
    assert parsed["capability"]["name"] == "Research Agent"
    assert parsed["workflow"]


def test_pipeline_returns_failed_result_when_no_profile_matches():
    registry = AgentRegistry()
    registry.register(
        AgentProfile(
            "Research Agent",
            [Capability("research")],
        )
    )
    pipeline = CognitiveRequestPipeline(
        capability_selector=AgentSelectorAdapter(registry)
    )

    result = pipeline.process_task("Plan a product launch roadmap")
    serialized = result.to_dict()

    assert result.status is PipelineStatus.FAILED
    assert serialized["capability"]["capability_id"] == "unknown"
    assert serialized["workflow"] == []
    assert serialized["metadata"]["failure_code"] == "no_capability_match"
