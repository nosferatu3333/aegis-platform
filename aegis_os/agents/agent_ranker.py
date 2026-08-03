class AgentRanker:
    """
    Ranks agents using capability
    compatibility and performance.
    """

    def __init__(self, performance_tracker):

        self.performance_tracker = performance_tracker

    def rank(self, agents, required_capabilities):

        ranking = []

        for agent in agents:
            capability_score = agent.profile.matches(required_capabilities)

            if capability_score <= 0:
                continue

            performance_score = self.performance_tracker.average(agent.name)

            total_score = capability_score * 10 + performance_score

            ranking.append((agent, total_score))

        ranking.sort(key=lambda x: x[1], reverse=True)

        return ranking
