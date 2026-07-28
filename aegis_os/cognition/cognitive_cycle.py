class CognitiveCycle:
    """
    Core cognitive workflow.

    Connects:
    - Agents
    - Memory
    - Knowledge Context

    Creates the Aegis learning loop.
    """

    def __init__(
        self,
        agent,
        working_memory,
        long_term_memory,
        reflection_memory,
        knowledge_context=None,
    ):

        self.agent = agent

        self.working_memory = working_memory

        self.long_term_memory = long_term_memory

        self.reflection_memory = reflection_memory

        self.knowledge_context = knowledge_context

    def execute(self, task, knowledge_topic=None):

        context = None

        # 1. Retrieve knowledge

        if self.knowledge_context and knowledge_topic:
            context = self.knowledge_context.build_context(knowledge_topic)

        # 2. Store active context

        self.working_memory.add({"task": task, "context": context})

        # 3. Execute agent

        result = self.agent.process(task)

        # 4. Store experience

        self.long_term_memory.store(
            {"task": task, "result": result, "context": context}
        )

        # 5. Reflection

        reflection = {
            "task": task,
            "result": result,
            "knowledge_used": context,
            "evaluation": "completed successfully",
        }

        self.reflection_memory.record(reflection)

        return result
