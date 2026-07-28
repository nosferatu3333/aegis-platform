from aegis_os.agents.agent_coordinator import AgentCoordinator
from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.analysis_agent import AnalysisAgent
from aegis_os.agents.execution_agent import ExecutionAgent
from aegis_os.agents.research_agent import ResearchAgent
from aegis_os.evaluation.evaluation_engine import EvaluationEngine
from aegis_os.learning.learning_engine import LearningEngine
from aegis_os.memory.memory_manager import MemoryManager
from aegis_os.planning.planning_engine import PlanningEngine
from aegis_os.reasoning.decision_engine import DecisionEngine


class CognitiveOrchestrator:
    """
    Coordinates the complete Aegis cognitive system.

    Goal
      ↓
    Decision
      ↓
    Agent Selection
      ↓
    Execution
      ↓
    Evaluation
      ↓
    Learning
    """

    def __init__(self, *, memory_manager=None):

        self.decision_engine = DecisionEngine()

        self.planning_engine = PlanningEngine()

        self.evaluation_engine = EvaluationEngine()

        self.memory_manager = (
            memory_manager if memory_manager is not None else MemoryManager()
        )

        self.learning_engine = LearningEngine(self.memory_manager)

        # Agent system

        self.registry = AgentRegistry()

        self.registry.register(ResearchAgent())

        self.registry.register(AnalysisAgent())

        self.registry.register(ExecutionAgent())

        self.agent_coordinator = AgentCoordinator(self.registry)

    def select_agent(self, decision):

        option = decision.option.lower()

        if "research" in option:
            return ("research",)

        if "analyze" in option:
            return ("analysis",)

        return ("execution",)

    def process(self, goal):

        print(f"\nGoal received: {goal}")

        # Decision

        decision = self.decision_engine.decide(
            [f"Research {goal}", f"Analyze {goal}", f"Build {goal}"]
        )

        print("\nDecision:", decision)

        # Agent Selection

        required_capabilities = self.select_agent(decision)

        print("\nSelected Agent:", required_capabilities)

        # Planning

        plan = self.planning_engine.create_plan(decision.option)

        print("\nPlan:", plan)

        # Agent Execution

        result = self.agent_coordinator.assign(required_capabilities, plan.goal)

        plan.mark_assignment_observed()

        print("\nAgent Result:", result)

        # Evaluation

        evaluation = self.evaluation_engine.evaluate(goal, result)

        print("\nEvaluation:", evaluation)

        # Learning

        learning = self.learning_engine.learn(result)

        print("\nLearning:", learning)

        return {
            "decision": decision,
            "agent": result.get("agent"),
            "required_capabilities": required_capabilities,
            "plan": plan,
            "result": result,
            "evaluation": evaluation,
            "learning": learning,
            "simulation": True,
        }
