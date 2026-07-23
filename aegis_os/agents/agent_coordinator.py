class AgentCoordinator:
    """
    Coordinates communication and task distribution
    between Aegis agents.
    """

    def __init__(self, registry):
        self.registry = registry

    def assign_task(self, agent_name, task):
        """
        Sends a task to a specific agent.
        """

        agent = self.registry.get(agent_name)

        if not agent:
            return {
                "status": "error",
                "message": f"Agent {agent_name} not found"
            }

        return agent.process(task)

    def available_agents(self):
        return self.registry.list_agents()