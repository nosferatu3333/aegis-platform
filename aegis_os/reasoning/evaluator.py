class Evaluator:
    """
    Evaluates possible decisions.
    """

    def evaluate(self, decision):

        decision.score = len(
            decision.option
        )

        decision.score_basis = (
            "string_length_heuristic"
        )

        return decision
