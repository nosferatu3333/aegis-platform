from aegis_os.agents.agent_ranker import AgentRanker
from aegis_os.agents.performance_tracker import PerformanceTracker


class AgentCoordinator:
    """
    Coordinates adaptive agent selection.
    """

    def __init__(self, registry):

        self.registry = registry

        self.performance_tracker = (
            PerformanceTracker()
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

            return "No suitable agent found"


        result = agent.execute(
            task
        )


        # Temporary learning signal

        self.performance_tracker.record(
            agent.name,
            80
        )


        return result