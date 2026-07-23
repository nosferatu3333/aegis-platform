class Evaluator:
    """
    Evaluates possible decisions.
    """

    def evaluate(self, decision):

        decision.score = len(
            decision.option
        )

        return decision