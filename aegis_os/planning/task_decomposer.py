class TaskDecomposer:
    """
    Converts high-level objectives
    into smaller executable tasks.
    """

    def decompose(self, goal):

        return [f"Research: {goal}", f"Analyze: {goal}", f"Execute: {goal}"]
