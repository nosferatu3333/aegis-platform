class Capability:
    """
    Represents an agent capability.
    """

    def __init__(self, name):

        self.name = name


    def __repr__(self):

        return (
            f"Capability({self.name})"
        )