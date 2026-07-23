class AgentRegistry:
    """
    Central registry for Aegis agents.

    Keeps track of available cognitive units.
    """

    def __init__(self):
        self.agents = {}

    def register(self, agent):
        self.agents[agent.name] = agent

        print(
            f"Agent registered: {agent.name}"
        )

    def get(self, name):
        return self.agents.get(name)

    def list_agents(self):
        return list(self.agents.keys())