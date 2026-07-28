from aegis_os.agents.agent_profile import AgentProfile
from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.capability import Capability
from aegis_os.agents.capability_matcher import CapabilityMatcher
from aegis_os.core.cognitive_runtime import CognitiveRuntime
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.pipeline.agent_selector_adapter import AgentSelectorAdapter
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline


def create_default_pipeline() -> CognitiveRequestPipeline:
    """Build the same in-process cognitive pipeline used by the API."""
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
    selector = AgentSelectorAdapter(
        registry=registry,
        matcher=CapabilityMatcher(),
    )
    return CognitiveRequestPipeline(capability_selector=selector)


def create_default_runtime(
    *,
    execution_engine: ExecutionEngine | None = None,
) -> CognitiveRuntime:
    """Build the canonical in-process analysis and execution runtime."""
    return CognitiveRuntime(
        pipeline=create_default_pipeline(),
        execution_engine=execution_engine,
    )
