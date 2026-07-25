class ReflectionMemory:
    """
    Stores evaluations and lessons learned.

    Used for future improvement.
    """

    def __init__(self):
        self.reflections = []

    def record(self, reflection):
        self.reflections.append(reflection)

    def review(self):
        return self.reflections