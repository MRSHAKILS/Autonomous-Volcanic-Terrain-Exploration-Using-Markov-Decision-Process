"""Week 2 terrain generation demo for the volcanic MDP explorer project."""

import argparse
from pathlib import Path

from support.terrain import BASE, CRATER, GAS, LAVA, ROCK, SAFE, SCIENCE, SYMBOLS, Terrain
from support.utils import print_section_header


PROJECT_TITLE = "Autonomous Volcanic Terrain Exploration Using Markov Decision Process (MDP)"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "sample_terrain_seed_42.csv"


def parse_arguments() -> argparse.Namespace:
    """Read optional command-line arguments for the terrain demo."""
    parser = argparse.ArgumentParser(
        description="Generate a volcanic terrain grid for the Week 2 project demo."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for reproducible terrain generation. Default: 42.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Optional square grid size. Example: --size 20 creates a 20x20 grid.",
    )

    return parser.parse_args()


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
    """Run the Week 2 volcanic terrain generation demo."""
    args = parse_arguments()

    print_section_header("Project Title")
    print(PROJECT_TITLE)

    print_section_header("Week 2: Volcanic Terrain Generation")
    terrain = create_terrain(seed=args.seed, size=args.size)
    print(f"Seed: {args.seed}")
    print(f"Grid size: {terrain.rows}x{terrain.cols}")

    print_section_header("Generated Terrain Grid")
    terrain.print_grid()

    print_section_header("Terrain Cell Counts")
    print_cell_counts(terrain)

    terrain.save_to_csv(DEFAULT_OUTPUT_PATH)
    print_section_header("Saved Terrain File")
    print(f"Generated terrain saved to: {DEFAULT_OUTPUT_PATH}")

    print_section_header("Symbol Legend")
    print_symbol_legend()

    print_section_header("Week 3 Preview")
    print("Next step: use this terrain grid as the environment for MDP state, reward, and transition design.")
    print("MDP value iteration and agent movement are not implemented yet.")


if __name__ == "__main__":
    main()
