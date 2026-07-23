from aegis_os.agents.base_agent import BaseAgent
from aegis_os.agents.agent_profile import AgentProfile


class ResearchAgent(BaseAgent):
    """
    Agent specialized in research tasks.
    """

    def __init__(self):

        super().__init__(
            name="Research Agent",
            role="Information Discovery"
        )


        self.profile = AgentProfile(
            self.name,
            [
                "research",
                "information",
                "knowledge",
                "retrieval"
            ]
        )


    def execute(self, task):

        self.start()

        return (
            f"Research completed for: {task}"
        )