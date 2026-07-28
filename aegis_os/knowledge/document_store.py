class DocumentStore:
    """
    Stores raw information sources.

    Documents can later come from files,
    APIs or external systems.
    """

    def __init__(self):
        self.documents = []

    def add_document(self, document):
        self.documents.append(document)

    def all_documents(self):
        return self.documents
