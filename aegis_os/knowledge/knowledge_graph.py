from aegis_os.knowledge.concept import Concept as Concept
from aegis_os.knowledge.relationship import Relationship as Relationship


class KnowledgeGraph:
    """
    Stores concepts and relationships.
    """

    def __init__(self):

        self.concepts = []

        self.relationships = []

    def add_concept(self, concept):

        self.concepts.append(concept)

    def add_relationship(self, relationship):

        self.relationships.append(relationship)

    def find_concept(self, name):

        for concept in self.concepts:
            if concept.name == name:
                return concept

        return None

    def get_relationships(self):

        return self.relationships

    def __repr__(self):

        return (
            f"KnowledgeGraph("
            f"concepts={len(self.concepts)}, "
            f"relationships={len(self.relationships)})"
        )
