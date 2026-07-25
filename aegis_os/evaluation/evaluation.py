from aegis_os.evaluation.metrics import Metrics


class Evaluation:
    """
    Represents the result evaluation
    of an executed action.
    """

    def __init__(
        self,
        objective,
        result
    ):

        self.objective = objective

        self.result = result

        self.metrics = Metrics()

        self.heuristic = True

        self.measurement = False

        self.confidence = 0.1


    def set_metrics(
        self,
        quality,
        efficiency,
        accuracy
    ):

        self.metrics = Metrics(
            quality,
            efficiency,
            accuracy
        )


    def __repr__(self):

        return (
            f"Evaluation("
            f"objective={self.objective}, "
            f"score={self.metrics.score()})"
        )
