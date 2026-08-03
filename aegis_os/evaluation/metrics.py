class Metrics:
    """
    Defines evaluation measurements.
    """

    def __init__(self, quality=0, efficiency=0, accuracy=0):

        self.quality = quality
        self.efficiency = efficiency
        self.accuracy = accuracy

    def score(self):

        return (self.quality + self.efficiency + self.accuracy) / 3

    def __repr__(self):

        return (
            f"Metrics("
            f"quality={self.quality}, "
            f"efficiency={self.efficiency}, "
            f"accuracy={self.accuracy})"
        )
