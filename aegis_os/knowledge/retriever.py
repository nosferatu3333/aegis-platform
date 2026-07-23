class Retriever:
    """
    Retrieves relevant knowledge
    from the knowledge system.
    """

    def __init__(self, knowledge_base):

        self.knowledge_base = knowledge_base


    def search(self, query):

        results = []


        knowledge_items = (
            self.knowledge_base.all()
        )


        query_words = set(
            query.lower().split()
        )


        for item in knowledge_items:

            text = str(item).lower()


            item_words = set(
                text.split()
            )


            similarity = len(
                query_words.intersection(
                    item_words
                )
            )


            if similarity > 0:

                results.append(
                    {
                        "knowledge": item,
                        "relevance": similarity
                    }
                )


        results.sort(
            key=lambda x: x["relevance"],
            reverse=True
        )


        return results