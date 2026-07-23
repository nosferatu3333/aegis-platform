from aegis_os.agents.research_agent import ResearchAgent
from aegis_os.agents.analysis_agent import AnalysisAgent
from aegis_os.agents.execution_agent import ExecutionAgent

from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.agent_coordinator import AgentCoordinator


registry = AgentRegistry()


registry.register(
    ResearchAgent()
)

registry.register(
    AnalysisAgent()
)

registry.register(
    ExecutionAgent()
)


print("Available Agents:")

print(
    registry.list_agents()
)


coordinator = AgentCoordinator(
    registry
)


result = coordinator.assign(
    "Research Agent",
    "Study autonomous intelligence"
)


print("\nResult:")

print(result)