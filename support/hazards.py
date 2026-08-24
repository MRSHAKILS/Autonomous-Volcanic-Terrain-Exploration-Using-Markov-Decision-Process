"""Dynamic hazard behavior for the volcanic terrain.

This module makes the environment change while the agent is exploring:

- Gas clouds drift: a gas cell can move into a random neighboring safe cell.
- Lava pulses: a lava cell can spread into a neighboring safe cell, and that
  new flow cools back to safe ground after a fixed number of steps. Original
  lava cells never cool.

Only SAFE cells are ever converted, so BASE, SCIENCE, ROCK, and CRATER cells
are never destroyed and the MDP state space (all non-rock cells) stays fixed.
Because hazards only swap between SAFE, GAS, and LAVA, the simulation just
re-runs value iteration on the updated terrain whenever something changed.
"""

import random
import sys
from pathlib import Path


# Allow this file to run both as a package module and as a direct script:
#   python -m support.hazards
#   python support/hazards.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from support.terrain import GAS, LAVA, SAFE, Terrain


class DynamicHazards:
    """Evolve gas and lava cells over time using simple seeded rules."""

    def __init__(
        self,
        terrain: Terrain,
        seed: int | None = None,
        gas_drift_probability: float = 0.15,
        lava_spread_probability: float = 0.08,
        lava_cooldown_steps: int = 6,
    ) -> None:
        """Attach dynamic hazard behavior to an already generated terrain."""
        self.terrain = terrain
        self.rng = random.Random(seed)
        self.gas_drift_probability = gas_drift_probability
        self.lava_spread_probability = lava_spread_probability
        self.lava_cooldown_steps = lava_cooldown_steps

        # New lava flows cool back to safe ground; original lava is permanent.
        self.active_lava_flows: dict[tuple[int, int], int] = {}
        self.total_events = 0

    def step(self) -> bool:
        """Advance the hazards by one time step.

        Returns True if any cell changed, so the caller knows to re-plan.
        """
        changed = self._cool_lava_flows()
        changed = self._drift_gas() or changed
        changed = self._spread_lava() or changed
        return changed

    def _cool_lava_flows(self) -> bool:
        """Turn spread lava back into safe ground once its cooldown expires."""
        changed = False

        for position in list(self.active_lava_flows):
            self.active_lava_flows[position] -= 1

            if self.active_lava_flows[position] <= 0:
                del self.active_lava_flows[position]
                # Only revert the cell if it is still lava (it always should be).
                if self.terrain.get_cell(*position) == LAVA:
                    self.terrain.set_cell(position[0], position[1], SAFE)
                    self.total_events += 1
                    changed = True

        return changed

    def _drift_gas(self) -> bool:
        """Move each gas cloud into a random neighboring safe cell sometimes."""
        changed = False

        for position in self._cells_of_type(GAS):
            if self.rng.random() >= self.gas_drift_probability:
                continue

            target = self._random_safe_neighbor(position)
            if target is None:
                continue

            self.terrain.set_cell(position[0], position[1], SAFE)
            self.terrain.set_cell(target[0], target[1], GAS)
            self.total_events += 1
            changed = True

        return changed

    def _spread_lava(self) -> bool:
        """Let each lava cell occasionally spill into a neighboring safe cell."""
        changed = False

        for position in self._cells_of_type(LAVA):
            if self.rng.random() >= self.lava_spread_probability:
                continue

            target = self._random_safe_neighbor(position)
            if target is None:
                continue

            self.terrain.set_cell(target[0], target[1], LAVA)
            self.active_lava_flows[target] = self.lava_cooldown_steps
            self.total_events += 1
            changed = True

        return changed

    def _cells_of_type(self, cell_type: str) -> list[tuple[int, int]]:
        """Snapshot every position holding the given cell type before mutating."""
        return [
            (row, col)
            for row in range(self.terrain.rows)
            for col in range(self.terrain.cols)
            if self.terrain.get_cell(row, col) == cell_type
        ]

    def _random_safe_neighbor(self, position: tuple[int, int]) -> tuple[int, int] | None:
        """Pick a random neighboring SAFE cell, or None if there is none."""
        candidates = [
            neighbor
            for neighbor in self.terrain.get_neighbors(*position)
            if self.terrain.get_cell(*neighbor) == SAFE
        ]

        if not candidates:
            return None

        return self.rng.choice(candidates)


if __name__ == "__main__":
    terrain = Terrain(seed=42)
    terrain.generate()

    print("Initial terrain:")
    terrain.print_grid()

    hazards = DynamicHazards(terrain, seed=42)
    for step_number in range(1, 21):
        if hazards.step():
            print(f"Step {step_number}: terrain changed (total events: {hazards.total_events})")

    print()
    print("Terrain after 20 dynamic-hazard steps:")
    terrain.print_grid()
