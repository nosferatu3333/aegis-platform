from aegis_os.agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """
    Agent specialized in information gathering
    and knowledge discovery.
    """

    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            role="Research and Information Gathering"
        )

    def process(self, task):

        result = {
            "agent": self.name,
            "role": self.role,
            "task": task,
            "output": "Research completed"
        }

        self.memory.append(result)

        return result