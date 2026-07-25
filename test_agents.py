"""Executable tests for Platform agent selection."""

import unittest

from aegis_os.agents.agent_coordinator import AgentCoordinator
from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.analysis_agent import AnalysisAgent
from aegis_os.agents.execution_agent import ExecutionAgent
from aegis_os.agents.research_agent import ResearchAgent


class AgentSelectionTests(unittest.TestCase):
    def setUp(self):
        registry = AgentRegistry()
        registry.register(ResearchAgent())
        registry.register(AnalysisAgent())
        registry.register(ExecutionAgent())
        self.coordinator = AgentCoordinator(registry)

    def test_display_name_alias_maps_to_one_real_capability(self):
        result = self.coordinator.assign(
            "Research Agent",
            "Study autonomous intelligence",
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["agent"], "Research Agent")
        self.assertEqual(
            result["required_capabilities"],
            ["research"],
        )
        self.assertTrue(result["simulation"])

    def test_unknown_capability_does_not_fall_through_to_first_agent(self):
        result = self.coordinator.assign(
            ("nonexistent-capability",),
            "Do not route this task accidentally",
        )

        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["agent"])
        self.assertTrue(result["failures"])


if __name__ == "__main__":
    unittest.main()
