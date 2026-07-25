class LongTermMemory:
    """
    Persistent memory system.

    Stores experiences and knowledge.
    """

    def __init__(self):
        self.storage = []

    def store(self, information):
        self.storage.append(information)

    def recall(self):
        return self.storage