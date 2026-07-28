from aegis_os.knowledge.concept import Concept
from aegis_os.knowledge.relationship import Relationship


class KnowledgeExtractor:
    """
    Converts experiences into structured knowledge.
    """

    def extract(self, experience):

        words = experience.split()

        if len(words) < 3:
            return None

        source = Concept(words[0], "Experience")

        target = Concept(words[-1], "Outcome")

        relationship = Relationship(source, "influences", target)

        return {"concepts": [source, target], "relationship": relationship}
