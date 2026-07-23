from aegis_os.agents.agent_ranker import AgentRanker
from aegis_os.agents.performance_tracker import PerformanceTracker
from aegis_os.agents.agent_memory import AgentMemory


class AgentCoordinator:
    """
    Coordinates adaptive agent selection.
    """

    def __init__(self, registry):

        self.registry = registry


        self.performance_tracker = (
            PerformanceTracker()
        )


        self.agent_memory = (
            AgentMemory()
        )


        self.ranker = AgentRanker(
            self.performance_tracker
        )


    def select_agent(
        self,
        required_capabilities
    ):

        agents = (
            self.registry.list_agents()
        )


        ranking = self.ranker.rank(
            agents,
            required_capabilities
        )


        if not ranking:

            return None


        return ranking[0][0]



    def assign(
        self,
        required_capabilities,
        task
    ):

        agent = self.select_agent(
            required_capabilities
        )


        if not agent:

            return (
                "No suitable agent found"
            )


        result = agent.execute(
            task
        )


        return {
            "agent": agent.name,
            "result": result
        }



    def learn_from_result(
        self,
        agent_name,
        task,
        result,
        score
    ):

        self.agent_memory.remember(
            agent_name,
            task,
            result,
            score
        )


        self.performance_tracker.record(
            agent_name,
            score
        )