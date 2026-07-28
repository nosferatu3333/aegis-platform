class AgentReflection:
    """
    Generates insights from agent experiences.
    """

    def __init__(self):

        self.insights = {}

    def reflect(self, agent_name, experiences):

        if not experiences:
            return None

        scores = [item["score"] for item in experiences]

        average = sum(scores) / len(scores)

        if average >= 80:
            insight = f"{agent_name} performs effectively in this task domain."

        else:
            insight = f"{agent_name} requires improvement in this domain."

        if agent_name not in self.insights:
            self.insights[agent_name] = []

        self.insights[agent_name].append(insight)

        return insight

    def get_insights(self, agent_name):

        return self.insights.get(agent_name, [])
