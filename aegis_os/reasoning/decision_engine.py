from aegis_os.reasoning.decision import Decision
from aegis_os.reasoning.evaluator import Evaluator


class DecisionEngine:
    """
    Generates and selects strategies.
    """

    def __init__(self):

        self.evaluator = Evaluator()

    def decide(self, options):

        decisions = []

        for option in options:
            decision = Decision(option)

            self.evaluator.evaluate(decision)

            decisions.append(decision)

        selected = max(decisions, key=lambda x: x.score)

        selected.select()

        return selected
