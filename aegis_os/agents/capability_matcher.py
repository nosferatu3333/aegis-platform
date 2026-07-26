class CapabilityMatcher:
    """
    Selects the best agent based on capabilities.
    """

    def select(
        self,
        profiles,
        required_capabilities
    ):

        best_agent = None

        highest_score = -1


        for profile in profiles:

            score = profile.matches(
                required_capabilities
            )

            if score <= 0:

                continue


            if score > highest_score:

                highest_score = score

                best_agent = profile


        return best_agent
