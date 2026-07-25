"""Executable tests for Platform's simulated collaboration layer."""

import unittest

from aegis_os.agents.analysis_agent import AnalysisAgent
from aegis_os.agents.collaboration_engine import CollaborationEngine
from aegis_os.agents.execution_agent import ExecutionAgent
from aegis_os.agents.research_agent import ResearchAgent


class CollaborationTests(unittest.TestCase):
    def test_team_executes_each_simulated_member_once(self):
        engine = CollaborationEngine()
        team = engine.create_team(
            "Develop autonomous intelligence",
            [
                ResearchAgent(),
                AnalysisAgent(),
                ExecutionAgent(),
            ],
        )

        result = engine.execute(team)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["results"]), 3)
        self.assertTrue(result["simulation"])
        self.assertEqual(
            [item["agent"] for item in result["results"]],
            [
                "Research Agent",
                "Analysis Agent",
                "Execution Agent",
            ],
        )


if __name__ == "__main__":
    unittest.main()
