"""Simulation loop that connects terrain, the MDP policy, and the explorer agent."""

import random
import sys
from pathlib import Path


if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from support.agent import MDPExplorerAgent
from support.hazards import DynamicHazards
from support.mdp import VolcanicMDP
from support.terrain import Terrain
from support.utils import print_section_header


class Simulation:
    """Run an MDP explorer agent across a terrain until it stops or finishes."""

    def __init__(
        self,
        terrain: Terrain,
        max_steps: int = 100,
        coverage_target: float = 0.60,
        seed: int = 42,
        stuck_limit: int = 8,
        dynamic_hazards: bool = False,
    ) -> None:
        """Build the MDP, compute a policy, and create the agent ready to run."""
        self.terrain = terrain
        self.max_steps = max_steps
        self.coverage_target = coverage_target
        self.seed = seed
        self.stuck_limit = stuck_limit

        self.mdp = VolcanicMDP(terrain)
        self.mdp.value_iteration()
        self.policy = self.mdp.extract_policy()

        self.agent = MDPExplorerAgent(terrain, self.mdp, self.policy, rng=random.Random(seed))
        self.hazards = DynamicHazards(terrain, seed=seed) if dynamic_hazards else None
        self.summary = None

    def calculate_coverage(self) -> float:
        """Return the percentage of reachable (non-rock) cells visited so far."""
        total_reachable = len(self.mdp.get_states())

        if total_reachable == 0:
            return 0.0

        return len(self.agent.visited) / total_reachable * 100

    def run(self) -> dict:
        """Run the agent until max steps, death, coverage, or a long hold at one cell."""
        previous_position = self.agent.position
        same_cell_streak = 0

        for _ in range(self.max_steps):
            if not self.agent.alive:
                break

            self.agent.step()

            # Dynamic hazards evolve after the agent moves. A lava flow can
            # engulf the agent, and any change makes the agent re-plan.
            if self.hazards is not None and self.hazards.step():
                self.agent.check_current_cell()
                if self.agent.alive:
                    self.agent.replan()

            if self.calculate_coverage() >= self.coverage_target * 100:
                break

            # The optimal policy eventually parks the agent (usually at BASE)
            # once every objective is collected; stop the mission at that point.
            same_cell_streak = same_cell_streak + 1 if self.agent.position == previous_position else 0
            previous_position = self.agent.position

            if same_cell_streak >= self.stuck_limit:
                break

        self.summary = self._build_summary()
        return self.summary

    def _build_summary(self) -> dict:
        """Combine the agent's stats with coverage into the shared summary format."""
        agent_summary = self.agent.mission_summary()

        return {
            "total_steps": agent_summary["steps_taken"],
            "cumulative_reward": agent_summary["cumulative_reward"],
            "coverage_percent": self.calculate_coverage(),
            "hazards_entered": agent_summary["hazards_entered"],
            "science_points_collected": agent_summary["science_points_collected"],
            "survived": agent_summary["alive"],
            "path_length": agent_summary["path_length"],
            "final_position": agent_summary["final_position"],
            "dynamic_hazard_events": self.hazards.total_events if self.hazards else 0,
        }

    def print_summary(self) -> None:
        """Run the simulation if needed, then print a clear mission summary."""
        if self.summary is None:
            self.run()

        print_section_header("Mission Summary")
        print(f"Total steps: {self.summary['total_steps']}")
        print(f"Cumulative reward: {self.summary['cumulative_reward']:.2f}")
        print(f"Coverage: {self.summary['coverage_percent']:.1f}%")
        print(f"Hazards entered: {self.summary['hazards_entered']}")
        print(f"Science points collected: {self.summary['science_points_collected']}")
        print(f"Survived: {self.summary['survived']}")
        print(f"Path length: {self.summary['path_length']}")
        print(f"Final position: {self.summary['final_position']}")
        print(f"Dynamic hazard events: {self.summary['dynamic_hazard_events']}")


if __name__ == "__main__":
    for dynamic in (False, True):
        terrain = Terrain(seed=42)
        terrain.generate()

        mode = "dynamic hazards" if dynamic else "static terrain"
        print_section_header(f"Simulation Start ({mode})")
        print(f"Grid size: {terrain.rows}x{terrain.cols}")

        simulation = Simulation(terrain, max_steps=100, coverage_target=0.60, seed=42, dynamic_hazards=dynamic)
        simulation.run()
        simulation.print_summary()
