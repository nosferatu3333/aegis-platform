from aegis_os.agents.base_agent import BaseAgent
from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.agent_coordinator import AgentCoordinator


registry = AgentRegistry()


researcher = BaseAgent(
    "ResearchAgent",
    "Research"
)

analyst = BaseAgent(
    "AnalysisAgent",
    "Analysis"
)


registry.register(researcher)
registry.register(analyst)


coordinator = AgentCoordinator(
    registry
)


researcher.activate()
analyst.activate()


result = coordinator.assign_task(
    "ResearchAgent",
    "Analyze AI operating systems"
)


print(result)