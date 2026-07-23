class KnowledgeContext:
    """
    Provides relevant knowledge
    to cognitive processes.
    """

    def __init__(self, retriever):
        self.retriever = retriever


    def build_context(self, topic):
        """
        Retrieves knowledge related
        to a specific topic.
        """

        knowledge = self.retriever.search(
            topic
        )

        return {
            "topic": topic,
            "knowledge": knowledge
        }