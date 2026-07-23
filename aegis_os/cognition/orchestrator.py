from aegis_os.reasoning.decision_engine import DecisionEngine
from aegis_os.planning.planning_engine import PlanningEngine
from aegis_os.evaluation.evaluation_engine import EvaluationEngine
from aegis_os.learning.learning_engine import LearningEngine

from aegis_os.memory.memory_manager import MemoryManager

from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.agent_coordinator import AgentCoordinator

from aegis_os.agents.research_agent import ResearchAgent
from aegis_os.agents.analysis_agent import AnalysisAgent
from aegis_os.agents.execution_agent import ExecutionAgent


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


    def __init__(self):

        self.decision_engine = DecisionEngine()

        self.planning_engine = PlanningEngine()

        self.evaluation_engine = EvaluationEngine()

        self.learning_engine = LearningEngine()


        self.memory_manager = MemoryManager()


        # Agent system

        self.registry = AgentRegistry()


        self.registry.register(
            ResearchAgent()
        )

        self.registry.register(
            AnalysisAgent()
        )

        self.registry.register(
            ExecutionAgent()
        )


        self.agent_coordinator = AgentCoordinator(
            self.registry
        )


    def select_agent(self, decision):

        option = decision.option.lower()


        if "research" in option:

            return "Research Agent"


        if "analyze" in option:

            return "Analysis Agent"


        return "Execution Agent"



    def process(self, goal):

        print(
            f"\nGoal received: {goal}"
        )


        # Decision

        decision = self.decision_engine.decide(
            [
                f"Research {goal}",
                f"Analyze {goal}",
                f"Build {goal}"
            ]
        )


        print(
            "\nDecision:",
            decision
        )


        # Agent Selection

        agent = self.select_agent(
            decision
        )


        print(
            "\nSelected Agent:",
            agent
        )


        # Planning

        plan = self.planning_engine.create_plan(
            decision.option
        )


        print(
            "\nPlan:",
            plan
        )


        # Agent Execution

        result = self.agent_coordinator.assign(
            agent,
            plan.goal
        )


        print(
            "\nAgent Result:",
            result
        )


        # Evaluation

        evaluation = self.evaluation_engine.evaluate(
            goal,
            result
        )


        print(
            "\nEvaluation:",
            evaluation
        )


        # Learning

        learning = self.learning_engine.learn(
            result
        )


        print(
            "\nLearning:",
            learning
        )


        self.memory_manager.remember_experience(
            result
        )


        return {
            "decision": decision,
            "agent": agent,
            "plan": plan,
            "result": result,
            "evaluation": evaluation,
            "learning": learning
        }