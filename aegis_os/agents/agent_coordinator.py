from aegis_os.agents.agent_memory import AgentMemory
from aegis_os.agents.agent_ranker import AgentRanker
from aegis_os.agents.performance_tracker import PerformanceTracker


class AgentCoordinator:
    """
    Coordinates adaptive agent selection.
    """

    def __init__(self, registry):

        self.registry = registry

        self.performance_tracker = PerformanceTracker()

        self.agent_memory = AgentMemory()

        self.ranker = AgentRanker(self.performance_tracker)

    def select_agent(self, required_capabilities):

        required_capabilities = self.normalize_capabilities(required_capabilities)

        agents = self.registry.list_agents()

        ranking = self.ranker.rank(agents, required_capabilities)

        if not ranking:
            return None

        return ranking[0][0]

    def assign(self, required_capabilities, task):

        normalized_capabilities = self.normalize_capabilities(required_capabilities)

        agent = self.select_agent(normalized_capabilities)

        if not agent:
            return {
                "status": "failed",
                "agent": None,
                "required_capabilities": list(normalized_capabilities),
                "result": None,
                "failures": ["No suitable agent found"],
                "simulation": True,
            }

        result = agent.execute(task)

        return {
            "status": "completed",
            "agent": agent.name,
            "required_capabilities": list(normalized_capabilities),
            "result": result,
            "failures": [],
            "simulation": True,
        }

    @staticmethod
    def normalize_capabilities(required_capabilities):

        aliases = {
            "research agent": "research",
            "analysis agent": "analysis",
            "execution agent": "execution",
        }

        if isinstance(required_capabilities, str):
            required_capabilities = (required_capabilities,)

        normalized = []

        for capability in required_capabilities:
            value = str(capability).strip().lower()

            value = aliases.get(value, value)

            if value and value not in normalized:
                normalized.append(value)

        return tuple(normalized)

    def learn_from_result(self, agent_name, task, result, score):

        self.agent_memory.remember(agent_name, task, result, score)

        self.performance_tracker.record(agent_name, score)
