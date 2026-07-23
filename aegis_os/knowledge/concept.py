class Concept:
    """
    Represents a knowledge concept.
    """

    def __init__(self, name, category=None):

        self.name = name

        self.category = category


    def __repr__(self):

        return (
            f"Concept("
            f"name={self.name}, "
            f"category={self.category})"
        )