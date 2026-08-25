"""Command-line entry point for the volcanic MDP explorer project.

Runs the full pipeline: terrain generation, MDP value iteration and policy
extraction, the explorer-agent simulation (optionally with dynamic hazards),
and the final mission-map visualization. It also provides terrain-only and
agent-comparison modes for convenient testing.
"""

import argparse
from pathlib import Path

from support.simulation import Simulation
from support.terrain import BASE, CRATER, GAS, LAVA, ROCK, SAFE, SCIENCE, SYMBOLS, Terrain
from support.utils import print_section_header
from support.visualization import render_mission_map


PROJECT_TITLE = "Autonomous Volcanic Terrain Exploration Using Markov Decision Process (MDP)"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_MAP_PATH = "outputs/final_map.png"


def terrain_csv_path(seed: int) -> Path:
    """Return the CSV path used to save the generated terrain for a seed."""
    return PROJECT_ROOT / "data" / f"sample_terrain_seed_{seed}.csv"


def parse_arguments() -> argparse.Namespace:
    """Read optional command-line arguments for the full pipeline demo."""
    parser = argparse.ArgumentParser(
        description="Run the full volcanic MDP exploration pipeline: terrain, MDP, agent, visualization."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for reproducible terrain and simulation. Default: 42.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Optional square grid size. Example: --size 20 creates a 20x20 grid.",
    )
    parser.add_argument(
        "--steps",
        "--max-steps",
        dest="steps",
        type=int,
        default=100,
        help="Maximum number of simulation steps. Default: 100.",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Disable dynamic hazards (gas drift and lava flows) during the simulation.",
    )
    parser.add_argument(
        "--terrain-only",
        action="store_true",
        help="Generate, print, and save the terrain without running the MDP simulation.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run the existing MDP, greedy, and random agent comparison experiments.",
    )
    parser.add_argument(
        "--coverage-target",
        type=float,
        default=0.60,
        help="Stop after visiting this fraction of reachable cells. Default: 0.60.",
    )

    args = parser.parse_args()

    if not 0 < args.coverage_target <= 1:
        parser.error("--coverage-target must be greater than 0 and at most 1.")

    return args


def print_symbol_legend() -> None:
    """Print a short explanation of the terrain symbols."""
    print(f"{SYMBOLS[SAFE]} = Safe cell")
    print(f"{SYMBOLS[LAVA]} = Lava flow")
    print(f"{SYMBOLS[CRATER]} = Crater")
    print(f"{SYMBOLS[GAS]} = Gas emission zone")
    print(f"{SYMBOLS[ROCK]} = Rock or obstacle")
    print(f"{SYMBOLS[SCIENCE]} = Science point")
    print(f"{SYMBOLS[BASE]} = Base station")


def create_terrain(seed: int, size: int | None) -> Terrain:
    """Create and generate terrain using the selected command-line settings."""
    if size is None:
        terrain = Terrain(seed=seed)
    else:
        terrain = Terrain(rows=size, cols=size, seed=seed)

    terrain.generate()
    return terrain


def print_cell_counts(terrain: Terrain) -> None:
    """Print terrain cell counts in a stable, readable order."""
    counts = terrain.count_cell_types()

    for cell_type in [SAFE, LAVA, CRATER, GAS, ROCK, SCIENCE, BASE]:
        print(f"{cell_type}: {counts[cell_type]}")


def main() -> None:
    """Run the selected project demo or comparison mode."""
    args = parse_arguments()

    if args.compare:
        from support.experiments import main as run_comparison

        print_section_header("Project Title")
        print(PROJECT_TITLE)
        print_section_header("Agent Performance Comparison")
        run_comparison()
        return

    dynamic_hazards = not args.static

    print_section_header("Project Title")
    print(PROJECT_TITLE)

    print_section_header("Step 1: Volcanic Terrain Generation")
    terrain = create_terrain(seed=args.seed, size=args.size)
    print(f"Seed: {args.seed}")
    print(f"Grid size: {terrain.rows}x{terrain.cols}")
    print()
    terrain.print_grid()
    print()
    print_cell_counts(terrain)

    csv_path = terrain_csv_path(args.seed)
    terrain.save_to_csv(csv_path)
    print(f"Generated terrain saved to: {csv_path}")

    if args.terrain_only:
        print_section_header("Symbol Legend")
        print_symbol_legend()
        return

    print_section_header("Step 2: MDP Value Iteration and Policy")
    simulation = Simulation(
        terrain,
        max_steps=args.steps,
        coverage_target=args.coverage_target,
        seed=args.seed,
        dynamic_hazards=dynamic_hazards,
    )
    print(f"States: {len(simulation.mdp.get_states())}")
    print(f"Gamma: {simulation.mdp.gamma}")
    print()
    print("Initial policy (before any re-planning):")
    simulation.mdp.print_policy()

    print_section_header("Step 3: Autonomous Agent Simulation")
    print(f"Dynamic hazards: {'ON' if dynamic_hazards else 'OFF'}")
    simulation.run()
    simulation.print_summary()

    print_section_header("Step 4: Mission Map Visualization")
    map_path = render_mission_map(
        terrain,
        path=simulation.agent.path,
        collected_science=simulation.agent.science_collected_positions,
        output_path=DEFAULT_MAP_PATH,
    )
    print(f"Saved mission map: {map_path}")

    print_section_header("Symbol Legend")
    print_symbol_legend()


if __name__ == "__main__":
    main()
