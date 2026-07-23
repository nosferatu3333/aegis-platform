from aegis_os.agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """
    Agent specialized in research tasks.
    """

    def __init__(self):

        super().__init__(
            name="Research Agent",
            role="Information Discovery"
        )


    def execute(self, task):

        self.start()


        result = (
            f"Research completed for: {task}"
        )


        return result