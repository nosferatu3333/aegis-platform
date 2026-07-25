class WorkingMemory:
    """
    Short-term memory system.

    Stores active context and current tasks.
    """

    def __init__(self):
        self.context = []

    def add(self, item):
        self.context.append(item)

    def clear(self):
        self.context = []

    def get_context(self):
        return self.context