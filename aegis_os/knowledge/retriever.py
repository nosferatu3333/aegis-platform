class Retriever:
    """
    Retrieves relevant knowledge
    from the knowledge base.
    """

    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base


    def search(self, concept):

        result = self.knowledge_base.get(
            concept
        )

        return result