from aegis_os.agents.capability_matcher import CapabilityMatcher


class AgentCoordinator:
    """
    Coordinates agent selection and execution.
    """

    def __init__(self, registry):

        self.registry = registry

        self.matcher = CapabilityMatcher()


    def select_agent(self, required_capabilities):

        profiles = []


        for agent in self.registry.list_agents():

            profiles.append(
                agent.profile
            )


        selected = self.matcher.select(
            profiles,
            required_capabilities
        )


        return selected.name


    def assign(self, required_capabilities, task):

        agent_name = self.select_agent(
            required_capabilities
        )


        agent = self.registry.get(
            agent_name
        )


        return agent.execute(
            task
        )