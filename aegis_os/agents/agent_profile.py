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


        if isinstance(required, str):

            required = (
                required,
            )


        normalized_capabilities = {
            str(
                getattr(capability, "name", capability)
            ).strip().lower()
            for capability in self.capabilities
        }


        for capability in required:

            if (
                str(
                    getattr(capability, "name", capability)
                ).strip().lower()
                in normalized_capabilities
            ):

                score += 1


        return score


    def __repr__(self):

        return (
            f"AgentProfile("
            f"{self.name}, "
            f"{self.capabilities})"
        )
