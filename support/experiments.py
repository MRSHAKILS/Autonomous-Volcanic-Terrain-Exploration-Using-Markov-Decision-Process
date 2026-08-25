"""Baseline experiments and performance comparison (Member 4).

This module shows that the MDP explorer performs better than two simple
baseline strategies on the volcanic terrain. It builds on Member 2's
``MDPExplorerAgent`` (``support/agent.py``) so that every agent is measured in
exactly the same way: the two baselines are thin subclasses that only override
``choose_action``. Everything else - stochastic movement sampling, reward
accounting, hazard/science/survival tracking - is inherited unchanged.

Three agents are compared on the same maps under the same uncertain movement:

1. MDP agent    - follows the value-iteration policy (Member 2's agent).
2. Random agent - picks a random movement direction each step.
3. Greedy agent - walks toward the nearest unvisited cell (nearest-unvisited),
                  avoiding only rock and lava while planning.

Exploration rule (applied to every agent): a science sample can only be
collected once. When an agent first reaches a science cell it becomes ordinary
ground, and the MDP agent re-runs value iteration so it heads to the next
objective instead of camping on one high-value cell. This rule lives in
``MDPExplorerAgent`` itself (``support/agent.py``), so the baselines inherit
it automatically and every agent is measured under the same environment.

Run it with::

    python support/experiments.py

It writes ``outputs/experiment_results.csv`` and
``outputs/performance_plot.png``.
"""

import random
import sys
from collections import deque
from pathlib import Path


# Allow this file to run both as a package module and as a direct script:
#   python -m support.experiments
#   python support/experiments.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")  # save figures without needing a display
import matplotlib.pyplot as plt
import pandas as pd

from support.agent import MDPExplorerAgent
from support.config import get_mdp_parameters
from support.mdp import ACTION_DELTAS, MOVEMENT_ACTIONS, STAY, VolcanicMDP
from support.terrain import LAVA, ROCK, Terrain


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CSV_PATH = "outputs/experiment_results.csv"
DEFAULT_PLOT_PATH = "outputs/performance_plot.png"

MAX_STEPS = 100       # step budget per run (matches Member 2's Simulation)
STUCK_LIMIT = 8       # stop early if the agent stays in one cell this many steps
NUM_SEEDS = 20        # number of random terrains to average over


GAMMA = get_mdp_parameters()["gamma"]

AGENT_MDP = "mdp"
AGENT_RANDOM = "random"
AGENT_GREEDY = "greedy"

METRIC_COLUMNS = [
    "agent_type",
    "seed",
    "total_reward",
    "coverage_percent",
    "hazards_entered",
    "science_points_collected",
    "survived",
    "total_steps",
]


# ---------------------------------------------------------------------------
# Baseline agents. Both reuse Member 2's MDPExplorerAgent and only change how
# the next action is chosen, so their metrics are gathered by the exact same
# code path as the MDP agent (fair comparison).
# ---------------------------------------------------------------------------


class RandomAgent(MDPExplorerAgent):
    """Baseline that ignores the policy and walks in a random direction."""

    def choose_action(self) -> str:
        return self.rng.choice(MOVEMENT_ACTIONS)


class GreedyAgent(MDPExplorerAgent):
    """Baseline that always heads toward the nearest unvisited reachable cell."""

    def choose_action(self) -> str:
        return _greedy_action(self.terrain, self.position, self.visited)


def _greedy_action(terrain: Terrain, position, visited) -> str:
    """Return a movement action toward the nearest unvisited reachable cell.

    This is the classic "greedy nearest-unvisited" coverage strategy. It plans
    with a breadth-first search that treats rock and lava as impassable, but it
    does not reason about the softer cost of gas or craters, so it will walk
    through those hazards on its way to new ground.
    """
    queue = deque([position])
    came_from = {position: None}
    target = None

    while queue:
        current = queue.popleft()

        if current != position and current not in visited:
            target = current
            break

        row, col = current
        for delta_row, delta_col in ACTION_DELTAS.values():
            neighbor = (row + delta_row, col + delta_col)

            if neighbor in came_from:
                continue
            if not terrain.is_valid_position(*neighbor):
                continue
            if terrain.get_cell(*neighbor) in (ROCK, LAVA):
                continue

            came_from[neighbor] = current
            queue.append(neighbor)

    if target is None:
        return STAY  # nothing new is reachable; hold position

    # Walk the path back to find the first step away from the current cell.
    step = target
    while came_from[step] != position:
        step = came_from[step]

    move = (step[0] - position[0], step[1] - position[1])
    for action, delta in ACTION_DELTAS.items():
        if delta == move:
            return action

    return STAY


# ---------------------------------------------------------------------------
# Core rollout shared by all agents.
# ---------------------------------------------------------------------------


def _make_agent(agent_type: str, terrain, mdp, policy, rng) -> MDPExplorerAgent:
    """Create the requested agent, all sharing MDPExplorerAgent's machinery."""
    if agent_type == AGENT_RANDOM:
        return RandomAgent(terrain, mdp, policy, rng)
    if agent_type == AGENT_GREEDY:
        return GreedyAgent(terrain, mdp, policy, rng)
    return MDPExplorerAgent(terrain, mdp, policy, rng)


def _run_episode(seed: int, agent_type: str) -> dict:
    """Run a single exploration episode and return its metrics.

    The three agents differ only in how they choose an action. The
    environment (terrain, movement uncertainty, rewards, the collect-once rule,
    and termination) is identical for all of them.
    """
    terrain = Terrain(seed=seed)
    terrain.generate()
    mdp = VolcanicMDP(terrain, gamma=GAMMA)
    total_states = len(mdp.get_states())

    # Only the MDP agent needs a policy; the baselines override choose_action.
    if agent_type == AGENT_MDP:
        mdp.value_iteration()
        policy = mdp.extract_policy()
    else:
        policy = {}

    rng = random.Random(seed)  # deterministic movement sampling per run
    agent = _make_agent(agent_type, terrain, mdp, policy, rng)

    previous_position = agent.position
    same_cell_streak = 0

    for _ in range(MAX_STEPS):
        if not agent.alive:
            break

        # The collect-once science rule (and the MDP agent's re-plan after
        # each sample) is applied inside MDPExplorerAgent.step().
        agent.step()
        position = agent.position

        same_cell_streak = same_cell_streak + 1 if position == previous_position else 0
        previous_position = position

        if not agent.alive or same_cell_streak >= STUCK_LIMIT:
            break

    summary = agent.mission_summary()
    coverage_percent = 100.0 * summary["visited_count"] / total_states

    return {
        "agent_type": agent_type,
        "seed": seed,
        "total_reward": round(summary["cumulative_reward"], 2),
        "coverage_percent": round(coverage_percent, 2),
        "hazards_entered": summary["hazards_entered"],
        "science_points_collected": summary["science_points_collected"],
        "survived": summary["alive"],
        "total_steps": summary["steps_taken"],
    }


# ---------------------------------------------------------------------------
# Required public functions.
# ---------------------------------------------------------------------------


def run_mdp_agent(seed: int) -> dict:
    """Run one episode of the MDP policy agent and return its metrics."""
    return _run_episode(seed, AGENT_MDP)


def run_random_agent(seed: int) -> dict:
    """Run one episode of the random-movement agent and return its metrics."""
    return _run_episode(seed, AGENT_RANDOM)


def run_greedy_agent(seed: int) -> dict:
    """Run one episode of the greedy nearest-unvisited agent."""
    return _run_episode(seed, AGENT_GREEDY)


def run_experiments(num_seeds: int = NUM_SEEDS) -> list[dict]:
    """Run all three agents on ``num_seeds`` terrains and collect the results."""
    results = []

    for seed in range(num_seeds):
        results.append(run_mdp_agent(seed))
        results.append(run_random_agent(seed))
        results.append(run_greedy_agent(seed))
        print(f"  seed {seed:2d}/{num_seeds - 1} complete")

    return results


def save_results(results: list[dict], path: str = DEFAULT_CSV_PATH) -> Path:
    """Save one row per run to a CSV file and return the written path."""
    output_path = _resolve_output_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frame = pd.DataFrame(results, columns=METRIC_COLUMNS)
    frame.to_csv(output_path, index=False)

    return output_path


def plot_results(results: list[dict], path: str = DEFAULT_PLOT_PATH) -> Path:
    """Save a bar chart comparing the average performance of each agent."""
    averages = _average_by_agent(results)
    order = [AGENT_MDP, AGENT_GREEDY, AGENT_RANDOM]
    labels = ["MDP", "Greedy", "Random"]
    colors = ["#2a7f3f", "#c08a2d", "#b23b3b"]

    panels = [
        ("Average Total Reward", [averages[a]["total_reward"] for a in order]),
        ("Average Coverage (%)", [averages[a]["coverage_percent"] for a in order]),
        ("Average Hazards Entered", [averages[a]["hazards_entered"] for a in order]),
        ("Survival Rate (%)", [averages[a]["survival_rate"] for a in order]),
    ]

    figure, axes = plt.subplots(2, 2, figsize=(10, 8))

    for axis, (title, values) in zip(axes.flat, panels):
        axis.bar(labels, values, color=colors)
        axis.set_title(title)
        axis.grid(axis="y", alpha=0.3)
        for index, value in enumerate(values):
            axis.text(
                index,
                value,
                f"{value:.1f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=9,
            )

    seed_count = len({row["seed"] for row in results})
    figure.suptitle(
        f"MDP vs Baseline Agents (averaged over {seed_count} terrains)",
        fontsize=14,
        fontweight="bold",
    )
    figure.tight_layout(rect=(0, 0, 1, 0.96))

    output_path = _resolve_output_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=120)
    plt.close(figure)

    return output_path


# ---------------------------------------------------------------------------
# Small internal helpers for aggregation and reporting.
# ---------------------------------------------------------------------------


def _resolve_output_path(path: str) -> Path:
    """Resolve a path relative to the project root unless it is absolute."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def _average_by_agent(results: list[dict]) -> dict:
    """Compute mean metrics (and survival rate) for each agent type."""
    averages = {}

    for agent_type in (AGENT_MDP, AGENT_RANDOM, AGENT_GREEDY):
        rows = [row for row in results if row["agent_type"] == agent_type]
        if not rows:
            continue

        count = len(rows)
        averages[agent_type] = {
            "total_reward": sum(r["total_reward"] for r in rows) / count,
            "coverage_percent": sum(r["coverage_percent"] for r in rows) / count,
            "hazards_entered": sum(r["hazards_entered"] for r in rows) / count,
            "science_points_collected": sum(r["science_points_collected"] for r in rows) / count,
            "total_steps": sum(r["total_steps"] for r in rows) / count,
            "survival_rate": 100.0 * sum(1 for r in rows if r["survived"]) / count,
        }

    return averages


def print_summary(results: list[dict]) -> None:
    """Print a clean averaged comparison table to the terminal."""
    averages = _average_by_agent(results)

    print()
    print("=" * 78)
    print("Average performance per agent")
    print("=" * 78)
    header = f"{'Agent':<10}{'Reward':>10}{'Coverage%':>12}{'Hazards':>10}{'Science':>10}{'Survival%':>12}{'Steps':>9}"
    print(header)
    print("-" * 78)

    for agent_type, label in ((AGENT_MDP, "MDP"), (AGENT_GREEDY, "Greedy"), (AGENT_RANDOM, "Random")):
        stats = averages[agent_type]
        print(
            f"{label:<10}"
            f"{stats['total_reward']:>10.1f}"
            f"{stats['coverage_percent']:>12.1f}"
            f"{stats['hazards_entered']:>10.1f}"
            f"{stats['science_points_collected']:>10.1f}"
            f"{stats['survival_rate']:>12.1f}"
            f"{stats['total_steps']:>9.1f}"
        )

    print("=" * 78)


def main() -> None:
    """Run the full experiment and save both output files."""
    print("Running volcanic terrain exploration experiments...")
    print(f"Agents: MDP, Random, Greedy  |  Seeds: 0..{NUM_SEEDS - 1}  |  Max steps: {MAX_STEPS}")

    results = run_experiments(NUM_SEEDS)

    csv_path = save_results(results)
    plot_path = plot_results(results)
    print_summary(results)

    print()
    print(f"Saved results CSV : {csv_path}")
    print(f"Saved performance : {plot_path}")


if __name__ == "__main__":
    main()
