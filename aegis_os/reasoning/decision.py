class Decision:
    """
    Represents a possible strategic choice.
    """

    def __init__(self, option, score=0):
        self.option = option
        self.score = score
        self.status = "pending"
        self.score_basis = "unscored"

    def select(self):
        self.status = "selected"

    def reject(self):
        self.status = "rejected"

    def __repr__(self):

        return (
            f"Decision("
            f"option={self.option}, "
            f"score={self.score}, "
            f"score_basis={self.score_basis}, "
            f"status={self.status})"
        )
