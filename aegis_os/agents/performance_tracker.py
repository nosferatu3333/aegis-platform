class PerformanceTracker:
    """
    Tracks agent performance over time.
    """

    def __init__(self):

        self.records = {}

    def record(self, agent_name, score):

        if agent_name not in self.records:
            self.records[agent_name] = []

        self.records[agent_name].append(score)

    def average(self, agent_name):

        scores = self.records.get(agent_name, [])

        if not scores:
            return 0

        return sum(scores) / len(scores)

    def get_history(self, agent_name):

        return self.records.get(agent_name, [])
