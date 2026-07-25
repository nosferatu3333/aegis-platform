class StrategyMemory:
    """
    Stores successful strategies
    for future decisions.
    """

    def __init__(self):
        self.strategies = []


    def store(self, strategy):

        self.strategies.append(
            strategy
        )


    def retrieve(self):

        return self.strategies


    def __repr__(self):

        return (
            f"StrategyMemory("
            f"{self.strategies})"
        )