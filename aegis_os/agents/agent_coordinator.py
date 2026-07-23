class AgentCoordinator:
    """
    Coordinates agent execution.
    """

    def __init__(self, registry):

        self.registry = registry


    def assign(self, agent_name, task):

        agent = self.registry.get(
            agent_name
        )


        if not agent:

            return (
                f"Agent {agent_name} not found"
            )


        return agent.execute(
            task
        )