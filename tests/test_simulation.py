"""Unit tests for support/simulation.py."""

import unittest

from support.simulation import Simulation
from support.terrain import Terrain

REQUIRED_SUMMARY_KEYS = {
    "total_steps",
    "cumulative_reward",
    "coverage_percent",
    "hazards_entered",
    "science_points_collected",
    "survived",
    "path_length",
    "final_position",
    "dynamic_hazard_events",
}


class SimulationRunTests(unittest.TestCase):
    def test_run_returns_a_summary_with_all_required_keys(self):
        terrain = Terrain(seed=3)
        terrain.generate()
        simulation = Simulation(terrain, max_steps=15, coverage_target=0.5, seed=3)

        summary = simulation.run()

        self.assertEqual(set(summary.keys()), REQUIRED_SUMMARY_KEYS)

    def test_summary_values_are_internally_consistent(self):
        terrain = Terrain(seed=5)
        terrain.generate()
        simulation = Simulation(terrain, max_steps=15, coverage_target=0.5, seed=5)

        summary = simulation.run()

        self.assertLessEqual(summary["total_steps"], 15)
        self.assertEqual(summary["path_length"], summary["total_steps"] + 1)
        self.assertGreaterEqual(summary["coverage_percent"], 0.0)
        self.assertLessEqual(summary["coverage_percent"], 100.0)
        self.assertIsInstance(summary["survived"], bool)
        self.assertEqual(summary["dynamic_hazard_events"], 0)

    def test_dynamic_hazards_mode_runs_without_error(self):
        terrain = Terrain(seed=8)
        terrain.generate()
        simulation = Simulation(terrain, max_steps=15, coverage_target=0.5, seed=8, dynamic_hazards=True)

        summary = simulation.run()

        self.assertGreaterEqual(summary["dynamic_hazard_events"], 0)

    def test_print_summary_runs_the_simulation_if_needed(self):
        terrain = Terrain(seed=11)
        terrain.generate()
        simulation = Simulation(terrain, max_steps=10, coverage_target=0.5, seed=11)

        self.assertIsNone(simulation.summary)
        simulation.print_summary()
        self.assertIsNotNone(simulation.summary)


if __name__ == "__main__":
    unittest.main()
