class AgentMemory:
    """
    Stores individual agent experiences.

    Tracks:
    - tasks executed
    - results
    - evaluation scores
    - performance history
    """

    def __init__(self):

        self.memory = {}


    def remember(
        self,
        agent_name,
        task,
        result,
        score
    ):

        if agent_name not in self.memory:

            self.memory[agent_name] = []


        experience = {

            "task": task,

            "result": result,

            "score": score

        }


        self.memory[agent_name].append(
            experience
        )


    def recall(
        self,
        agent_name
    ):

        return self.memory.get(
            agent_name,
            []
        )


    def average_score(
        self,
        agent_name
    ):

        experiences = self.recall(
            agent_name
        )


        if not experiences:

            return 0


        scores = [
            item["score"]
            for item in experiences
        ]


        return sum(scores) / len(scores)


    def best_agent(self):

        ranking = []


        for agent, experiences in self.memory.items():

            score = self.average_score(
                agent
            )


            ranking.append(
                (
                    agent,
                    score
                )
            )


        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )


        return ranking