class AgentRegistry:
    """
    Stores and manages available agents.
    """

    def __init__(self):

        self.agents = {}

    def register(self, agent):

        self.agents[agent.name] = agent

    def get(self, name):

        return self.agents.get(name)

    def list_agents(self):

        return list(self.agents.values())

    def list_profiles(self):

        return [getattr(agent, "profile", agent) for agent in self.agents.values()]
