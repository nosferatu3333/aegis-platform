from aegis_os.agents.base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    """
    Agent specialized in reasoning
    and evaluation.
    """

    def __init__(self):
        super().__init__(
            name="AnalysisAgent",
            role="Analysis and Reasoning"
        )

    def process(self, task):

        result = {
            "agent": self.name,
            "role": self.role,
            "task": task,
            "output": "Analysis completed"
        }

        self.memory.append(result)

        return result