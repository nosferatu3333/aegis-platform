class KnowledgeBase:
    """
    Central repository for structured knowledge.

    Stores concepts, facts and information.
    """

    def __init__(self):
        self.knowledge = {}


    def add(self, concept, information):
        self.knowledge[concept] = information


    def get(self, concept):
        return self.knowledge.get(concept)


    def list_concepts(self):
        return list(self.knowledge.keys())