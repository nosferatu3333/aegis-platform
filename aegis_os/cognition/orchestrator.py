from aegis_os.reasoning.decision_engine import DecisionEngine
from aegis_os.planning.planning_engine import PlanningEngine
from aegis_os.evaluation.evaluation_engine import EvaluationEngine
from aegis_os.learning.learning_engine import LearningEngine


class CognitiveOrchestrator:
    """
    Coordinates the Aegis cognitive loop.
    
    Connects:
    Decision
    Planning
    Execution
    Evaluation
    Learning
    """

    def __init__(self):

        self.decision_engine = DecisionEngine()

        self.planning_engine = PlanningEngine()

        self.evaluation_engine = EvaluationEngine()

        self.learning_engine = LearningEngine()


    def process(self, goal):

        print(
            f"\nGoal received: {goal}"
        )


        # 1. Decision

        decision = self.decision_engine.decide(
            [
                f"Research {goal}",
                f"Build {goal}",
                f"Analyze {goal}"
            ]
        )

        print(
            "\nDecision:",
            decision
        )


        # 2. Planning

        plan = self.planning_engine.create_plan(
            decision.option
        )

        print(
            "\nPlan:",
            plan
        )


        # 3. Execution

        result = (
            f"Executed plan: {plan.goal}"
        )

        print(
            "\nExecution:",
            result
        )


        # 4. Evaluation

        evaluation = self.evaluation_engine.evaluate(
            goal,
            result
        )

        print(
            "\nEvaluation:",
            evaluation
        )


        # 5. Learning

        learning = self.learning_engine.learn(
            result
        )

        print(
            "\nLearning:",
            learning
        )


        return {
            "decision": decision,
            "plan": plan,
            "result": result,
            "evaluation": evaluation,
            "learning": learning
        }