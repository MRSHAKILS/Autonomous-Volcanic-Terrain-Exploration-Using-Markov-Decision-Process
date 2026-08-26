"""Autonomous explorer agent that follows an MDP policy through the terrain.

The agent starts at the BASE cell and repeatedly asks the policy which action
to take. Because movement is stochastic (see `VolcanicMDP.transition_probabilities`),
each step samples one real outcome from that probability distribution instead
of assuming the intended move always succeeds.

Science samples follow a collect-once rule: when the agent first reaches a
science cell it gathers the sample, the cell becomes ordinary ground, and the
agent re-runs value iteration so the policy targets the next objective instead
of camping on one high-value cell.
"""

import random
import sys
from pathlib import Path


if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from support.mdp import STAY, VolcanicMDP
from support.terrain import BASE, HAZARD_TYPES, LAVA, SAFE, SCIENCE, Terrain
from support.utils import print_section_header


class MDPExplorerAgent:
    """An explorer rover that moves through the terrain using an MDP policy."""

    def __init__(
        self,
        terrain: Terrain,
        mdp: VolcanicMDP,
        policy: dict[tuple[int, int], str],
        rng: random.Random | None = None,
    ) -> None:
        """Set up the agent at BASE, ready to follow the given policy."""
        self.terrain = terrain
        self.mdp = mdp
        self.policy = policy
        self.rng = rng or random.Random()

        self.position = self.find_base()
        self.visited = {self.position}
        self.path = [self.position]
        self.cumulative_reward = 0.0
        self.hazards_entered = 0
        self.science_points_collected = 0
        self.science_collected_positions: list[tuple[int, int]] = []
        self.alive = True

    def find_base(self) -> tuple[int, int]:
        """Locate the BASE cell in the terrain."""
        for row in range(self.terrain.rows):
            for col in range(self.terrain.cols):
                if self.terrain.get_cell(row, col) == BASE:
                    return row, col

        raise ValueError("No BASE cell was found in the terrain.")

    def choose_action(self) -> str:
        """Return the policy action for the agent's current position."""
        return self.policy.get(self.position, STAY)

    def step(self) -> bool:
        """Take one action and move the agent to a sampled next state.

        Returns False without changing state if the agent is no longer alive.
        """
        if not self.alive:
            return False

        action = self.choose_action()
        next_state = self._sample_next_state(action)
        reward = self.mdp.reward(self.position, action, next_state, visited=self.visited)

        self.cumulative_reward += reward
        self._update_trackers(next_state)
        self.position = next_state
        self.path.append(self.position)
        self.visited.add(self.position)

        if self.alive and self.terrain.get_cell(*self.position) == SCIENCE:
            self._collect_science(self.position)

        return True

    def _collect_science(self, position: tuple[int, int]) -> None:
        """Apply the collect-once rule: gather the sample, then re-plan.

        The science cell becomes ordinary ground so its reward can only be
        earned a single time, and the policy is recomputed so the agent heads
        to the next objective instead of camping here.
        """
        self.science_collected_positions.append(position)
        self.terrain.set_cell(position[0], position[1], SAFE)
        self.replan()

    def check_current_cell(self) -> None:
        """Re-check the cell under the agent after the environment changed.

        Dynamic hazards can move onto the agent between its own steps; being
        caught by a lava flow is fatal.
        """
        if not self.alive:
            return

        if self.terrain.get_cell(*self.position) == LAVA:
            self.hazards_entered += 1
            self.alive = False

    def replan(self) -> None:
        """Re-run value iteration on the current terrain and refresh the policy.

        Baseline agents that override ``choose_action`` run with an empty
        policy, so there is nothing to recompute for them.
        """
        if not self.policy:
            return

        self.mdp.value_iteration()
        self.policy = self.mdp.extract_policy()

    def _sample_next_state(self, action: str) -> tuple[int, int]:
        """Randomly sample a real outcome from the action's transition probabilities."""
        transitions = self.mdp.transition_probabilities(self.position, action)
        possible_states = list(transitions.keys())
        state_weights = list(transitions.values())

        return self.rng.choices(possible_states, weights=state_weights, k=1)[0]

    def _update_trackers(self, next_state: tuple[int, int]) -> None:
        """Update hazard, science, and survival tracking for the new cell."""
        cell_type = self.terrain.get_cell(*next_state)

        if cell_type in HAZARD_TYPES:
            self.hazards_entered += 1

        if cell_type == LAVA:
            self.alive = False

        if cell_type == SCIENCE and next_state not in self.visited:
            self.science_points_collected += 1

    def mission_summary(self) -> dict:
        """Return the agent's current mission statistics."""
        return {
            "steps_taken": len(self.path) - 1,
            "cumulative_reward": self.cumulative_reward,
            "hazards_entered": self.hazards_entered,
            "science_points_collected": self.science_points_collected,
            "alive": self.alive,
            "path_length": len(self.path),
            "visited_count": len(self.visited),
            "final_position": self.position,
        }

    def print_mission_summary(self) -> None:
        """Print the agent's mission statistics in a readable format."""
        summary = self.mission_summary()

        print_section_header("Mission Summary")
        print(f"Steps taken: {summary['steps_taken']}")
        print(f"Cumulative reward: {summary['cumulative_reward']:.2f}")
        print(f"Hazards entered: {summary['hazards_entered']}")
        print(f"Science points collected: {summary['science_points_collected']}")
        print(f"Survived: {summary['alive']}")
        print(f"Cells visited: {summary['visited_count']}")
        print(f"Final position: {summary['final_position']}")


if __name__ == "__main__":
    if __package__ is None or __package__ == "":
        from mdp import VolcanicMDP
        from terrain import Terrain
    else:
        from support.mdp import VolcanicMDP
        from support.terrain import Terrain

    terrain = Terrain(seed=42)
    terrain.generate()

    mdp = VolcanicMDP(terrain)
    mdp.value_iteration()
    policy = mdp.extract_policy()

    agent = MDPExplorerAgent(terrain, mdp, policy, rng=random.Random(42))

    print_section_header("Agent Start")
    print(f"Starting position (BASE): {agent.position}")

    for _ in range(20):
        if not agent.step():
            break

    agent.print_mission_summary()
