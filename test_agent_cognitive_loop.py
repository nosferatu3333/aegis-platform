"""Characterization tests for the stabilized Platform orchestrator."""

import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from aegis_os.cognition.orchestrator import CognitiveOrchestrator
from aegis_os.memory.memory_manager import MemoryManager


class CognitiveOrchestratorTests(unittest.TestCase):
    def test_orchestrator_exposes_all_placeholder_boundaries(self):
        with TemporaryDirectory() as directory:
            memory = MemoryManager(
                state_path=str(
                    Path(directory) / "aegis_state.json"
                )
            )
            aegis = CognitiveOrchestrator(
                memory_manager=memory
            )

            with contextlib.redirect_stdout(io.StringIO()):
                result = aegis.process(
                    "Develop autonomous intelligence"
                )

        self.assertEqual(
            result["decision"].score_basis,
            "string_length_heuristic",
        )
        self.assertEqual(result["agent"], "Research Agent")
        self.assertEqual(
            result["required_capabilities"],
            ("research",),
        )
        self.assertEqual(result["plan"].status, "partial")
        self.assertFalse(result["plan"].tasks_executed)
        self.assertEqual(result["result"]["status"], "completed")
        self.assertTrue(result["result"]["simulation"])
        self.assertTrue(result["evaluation"].heuristic)
        self.assertFalse(result["evaluation"].measurement)
        self.assertEqual(result["evaluation"].confidence, 0.1)
        self.assertFalse(result["learning"]["cross_run_validation"])
        self.assertFalse(result["learning"]["promoted"])
        self.assertEqual(len(memory.get_experiences()), 1)
        self.assertTrue(result["simulation"])


if __name__ == "__main__":
    unittest.main()
