from aegis_os.agents.agent_profile import AgentProfile
from aegis_os.agents.base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    """
    Agent specialized in analysis tasks.
    """

    def __init__(self):

        super().__init__(name="Analysis Agent", role="Data Analysis")

        self.profile = AgentProfile(
            self.name, ["analysis", "reasoning", "evaluation", "insight"]
        )

    def execute(self, task):

        self.start()

        return f"Analysis completed for: {task}"
