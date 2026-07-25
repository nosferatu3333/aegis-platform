class PatternDetector:
    """
    Detects repeated experiences.
    """

    def detect(self, experiences):

        patterns = []


        for experience in experiences:

            if experience not in patterns:
                patterns.append(
                    experience
                )


        return patterns