"""Unit tests for support/agent.py."""

import random
import unittest

from support.agent import MDPExplorerAgent
from support.mdp import STAY, VolcanicMDP
from support.terrain import BASE, LAVA, SCIENCE, Terrain


def build_small_terrain() -> Terrain:
    """Build a tiny, deterministic terrain for agent unit tests.

    Every non-base cell starts SAFE so tests do not depend on random
    terrain generation; individual cells are overridden as each test needs.
    """
    terrain = Terrain(rows=3, cols=3, seed=0)
    terrain.set_cell(*terrain.base_location, BASE)
    return terrain


def build_agent(terrain: Terrain, seed: int = 1) -> MDPExplorerAgent:
    """Create an agent with a real value-iteration policy for the given terrain."""
    mdp = VolcanicMDP(terrain)
    mdp.value_iteration()
    policy = mdp.extract_policy()
    return MDPExplorerAgent(terrain, mdp, policy, rng=random.Random(seed))


class FindBaseTests(unittest.TestCase):
    def test_agent_starts_at_the_terrain_base_cell(self):
        terrain = build_small_terrain()
        agent = build_agent(terrain)

        self.assertEqual(agent.position, terrain.base_location)
        self.assertEqual(agent.path, [terrain.base_location])
        self.assertEqual(agent.visited, {terrain.base_location})


class ChooseActionTests(unittest.TestCase):
    def test_choose_action_returns_a_policy_action_for_every_state(self):
        terrain = build_small_terrain()
        agent = build_agent(terrain)

        for state in agent.mdp.get_states():
            agent.position = state
            self.assertIn(agent.choose_action(), agent.mdp.get_actions())


class StepMechanicsTests(unittest.TestCase):
    def test_stay_action_updates_path_and_reward_without_moving(self):
        terrain = build_small_terrain()
        agent = build_agent(terrain)
        agent.policy[agent.position] = STAY
        start_position = agent.position

        moved = agent.step()

        self.assertTrue(moved)
        self.assertEqual(agent.position, start_position)
        self.assertEqual(agent.path, [start_position, start_position])
        # BASE reward (+5) minus the revisit penalty (-2) for staying on an
        # already-visited cell.
        self.assertEqual(agent.cumulative_reward, 3.0)

    def test_dead_agent_cannot_take_another_step(self):
        terrain = build_small_terrain()
        agent = build_agent(terrain)
        agent.alive = False

        self.assertFalse(agent.step())
        self.assertEqual(len(agent.path), 1)


class TrackerUpdateTests(unittest.TestCase):
    def test_entering_lava_kills_the_agent(self):
        terrain = build_small_terrain()
        lava_position = (0, 0)
        terrain.set_cell(*lava_position, LAVA)
        agent = build_agent(terrain)

        agent._update_trackers(lava_position)

        self.assertFalse(agent.alive)
        self.assertEqual(agent.hazards_entered, 1)

    def test_reaching_a_new_science_cell_is_counted_once(self):
        terrain = build_small_terrain()
        science_position = (0, 0)
        terrain.set_cell(*science_position, SCIENCE)
        agent = build_agent(terrain)

        agent._update_trackers(science_position)
        agent.visited.add(science_position)
        agent._update_trackers(science_position)

        self.assertEqual(agent.science_points_collected, 1)


class MissionSummaryTests(unittest.TestCase):
    def test_summary_contains_expected_keys_and_types(self):
        terrain = build_small_terrain()
        agent = build_agent(terrain)
        agent.policy[agent.position] = STAY
        agent.step()

        summary = agent.mission_summary()

        self.assertEqual(summary["steps_taken"], 1)
        self.assertIsInstance(summary["cumulative_reward"], float)
        self.assertIsInstance(summary["alive"], bool)
        self.assertEqual(summary["path_length"], len(agent.path))
        self.assertEqual(summary["final_position"], agent.position)


if __name__ == "__main__":
    unittest.main()
