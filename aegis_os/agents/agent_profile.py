class AgentProfile:
    """
    Defines agent identity and capabilities.
    """

    def __init__(
        self,
        name,
        capabilities
    ):

        self.name = name

        self.capabilities = capabilities


    def matches(self, required):

        score = 0


        for capability in required:

            if capability in self.capabilities:

                score += 1


        return score


    def __repr__(self):

        return (
            f"AgentProfile("
            f"{self.name}, "
            f"{self.capabilities})"
        )