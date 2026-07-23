class CognitiveCycle:
    """
    Core cognitive workflow.

    Connects agents with memory systems
    to create continuous learning.
    """

    def __init__(
        self,
        agent,
        working_memory,
        long_term_memory,
        reflection_memory
    ):
        self.agent = agent
        self.working_memory = working_memory
        self.long_term_memory = long_term_memory
        self.reflection_memory = reflection_memory


    def execute(self, task):

        # 1. Store active context
        self.working_memory.add(task)


        # 2. Agent execution
        result = self.agent.process(task)


        # 3. Store experience
        self.long_term_memory.store(result)


        # 4. Reflect on outcome
        reflection = {
            "task": task,
            "evaluation": "completed successfully"
        }

        self.reflection_memory.record(
            reflection
        )


        return result