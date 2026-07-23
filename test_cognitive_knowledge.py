from aegis_os.agents.analysis_agent import AnalysisAgent

from aegis_os.memory.working_memory import WorkingMemory
from aegis_os.memory.long_term_memory import LongTermMemory
from aegis_os.memory.reflection_memory import ReflectionMemory

from aegis_os.knowledge.knowledge_base import KnowledgeBase
from aegis_os.knowledge.retriever import Retriever

from aegis_os.cognition.knowledge_context import KnowledgeContext
from aegis_os.cognition.cognitive_cycle import CognitiveCycle


agent = AnalysisAgent()


working = WorkingMemory()

long_term = LongTermMemory()

reflection = ReflectionMemory()


knowledge = KnowledgeBase()


knowledge.add(
    "AI architecture",
    "Multi-agent systems use specialized agents coordinated by a central system."
)


retriever = Retriever(
    knowledge
)


knowledge_context = KnowledgeContext(
    retriever
)


cycle = CognitiveCycle(

    agent,

    working,

    long_term,

    reflection,

    knowledge_context
)


result = cycle.execute(
    "Analyze autonomous systems",
    "AI architecture"
)


print(result)

print("\nWorking Memory:")
print(
    working.get_context()
)


print("\nLong Term Memory:")
print(
    long_term.recall()
)


print("\nReflection:")
print(
    reflection.review()
)