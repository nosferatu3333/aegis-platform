"""Regression tests for Platform knowledge imports and retrieval."""

import unittest

from aegis_os.knowledge.knowledge_base import KnowledgeBase
from aegis_os.knowledge.retriever import Retriever


class KnowledgeTests(unittest.TestCase):
    def test_knowledge_import_has_no_cognitive_side_effect(self):
        knowledge = KnowledgeBase()
        knowledge.add(
            {
                "subject": "Aegis",
                "fact": "Platform is the control plane",
            }
        )

        results = Retriever(knowledge).search("control plane")

        self.assertEqual(len(knowledge.all()), 1)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
