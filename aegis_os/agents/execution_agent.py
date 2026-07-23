from aegis_os.agents.base_agent import BaseAgent
from aegis_os.agents.agent_profile import AgentProfile


class ExecutionAgent(BaseAgent):
    """
    Agent specialized in execution tasks.
    """

    def __init__(self):

        super().__init__(
            name="Execution Agent",
            role="Task Execution"
        )


        self.profile = AgentProfile(
            self.name,
            [
                "execution",
                "action",
                "operations",
                "implementation"
            ]
        )


    def execute(self, task):

        self.start()

        return (
            f"Execution completed for: {task}"
        )