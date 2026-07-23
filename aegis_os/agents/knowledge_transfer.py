class KnowledgeTransfer:
    """
    Transfers learned insights between agents.
    """

    def __init__(self):

        self.shared_knowledge = []


    def transfer(
        self,
        source_agent,
        target_agent,
        insight
    ):

        knowledge = {

            "from": source_agent,

            "to": target_agent,

            "insight": insight

        }


        self.shared_knowledge.append(
            knowledge
        )


        return knowledge


    def get_for_agent(
        self,
        agent_name
    ):

        return [
            item
            for item in self.shared_knowledge
            if item["to"] == agent_name
        ]