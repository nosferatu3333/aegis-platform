"""In-memory knowledge collection for the Platform prototype."""


class KnowledgeBase:
    """Store knowledge records without triggering cognition during import."""

    def __init__(self):
        self.records = []

    def add(self, record):
        self.records.append(record)
        return record

    def all(self):
        return list(self.records)

    def search(self, term):
        normalized = str(term).lower()
        return [
            record
            for record in self.records
            if normalized in str(record).lower()
        ]
