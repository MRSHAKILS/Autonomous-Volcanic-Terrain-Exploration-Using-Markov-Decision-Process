"""Unit tests for support/hazards.py."""

import unittest

from support.hazards import DynamicHazards
from support.terrain import BASE, ROCK, TERRAIN_TYPES, Terrain


class DynamicHazardsTests(unittest.TestCase):
    def test_step_returns_a_boolean_and_never_raises(self):
        terrain = Terrain(seed=4)
        terrain.generate()
        hazards = DynamicHazards(terrain, seed=4)

        for _ in range(20):
            self.assertIsInstance(hazards.step(), bool)

    def test_total_events_only_grows(self):
        terrain = Terrain(seed=6)
        terrain.generate()
        hazards = DynamicHazards(terrain, seed=6)

        previous_total = hazards.total_events
        for _ in range(20):
            hazards.step()
            self.assertGreaterEqual(hazards.total_events, previous_total)
            previous_total = hazards.total_events

    def test_base_and_rock_cells_are_never_overwritten(self):
        terrain = Terrain(seed=9)
        terrain.generate()
        base_position = terrain.base_location
        rock_positions = [
            (row, col)
            for row in range(terrain.rows)
            for col in range(terrain.cols)
            if terrain.get_cell(row, col) == ROCK
        ]
        hazards = DynamicHazards(terrain, seed=9)

        for _ in range(30):
            hazards.step()

        self.assertEqual(terrain.get_cell(*base_position), BASE)
        for position in rock_positions:
            self.assertEqual(terrain.get_cell(*position), ROCK)

    def test_grid_only_ever_contains_known_terrain_types(self):
        terrain = Terrain(seed=13)
        terrain.generate()
        hazards = DynamicHazards(terrain, seed=13)

        for _ in range(30):
            hazards.step()

        for row in range(terrain.rows):
            for col in range(terrain.cols):
                self.assertIn(terrain.get_cell(row, col), TERRAIN_TYPES)


if __name__ == "__main__":
    unittest.main()
