from aegis_os.agents.base_agent import BaseAgent


class ExecutionAgent(BaseAgent):
    """
    Agent specialized in performing actions
    and executing workflows.
    """

    def __init__(self):
        super().__init__(
            name="ExecutionAgent",
            role="Task Execution"
        )

    def process(self, task):

        result = {
            "agent": self.name,
            "role": self.role,
            "task": task,
            "output": "Execution completed"
        }

        self.memory.append(result)

        return result
