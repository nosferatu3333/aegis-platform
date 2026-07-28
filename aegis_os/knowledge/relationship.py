class Relationship:
    """
    Represents a relationship between concepts.
    """

    def __init__(self, source, relation, target):

        self.source = source

        self.relation = relation

        self.target = target

    def __repr__(self):

        return f"{self.source.name} {self.relation} {self.target.name}"
