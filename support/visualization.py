"""Terrain and path visualization for the volcanic explorer project.

This module draws the volcanic terrain grid with matplotlib and saves it as
an image. It can render either a plain terrain map, a terrain map with a
labeled sample path (kept for layout testing), or a full mission map showing
the real path the MDP explorer agent took during a simulation, including the
science cells where samples were collected.
"""

import sys
from pathlib import Path


# Allow this file to run both as a package module and as a direct script:
#   python -m support.visualization
#   python support/visualization.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")  # save figures without needing a display
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from support.terrain import BASE, CRATER, GAS, LAVA, ROCK, SAFE, SCIENCE, Terrain


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = "outputs/final_map.png"

CELL_COLORS = {
    SAFE: "#e8e4d8",
    LAVA: "#c0392b",
    CRATER: "#6b3fa0",
    GAS: "#8fbf6f",
    ROCK: "#5c5c5c",
    SCIENCE: "#f2c744",
    BASE: "#2f6fbf",
}

CELL_LABELS = {
    SAFE: "Safe",
    LAVA: "Lava",
    CRATER: "Crater",
    GAS: "Gas",
    ROCK: "Rock",
    SCIENCE: "Science",
    BASE: "Base",
}


def draw_terrain(terrain: Terrain, axis: plt.Axes) -> None:
    """Draw every cell of the terrain grid as a colored square."""
    for row in range(terrain.rows):
        for col in range(terrain.cols):
            cell_type = terrain.get_cell(row, col)
            color = CELL_COLORS[cell_type]
            axis.add_patch(
                plt.Rectangle((col, terrain.rows - 1 - row), 1, 1, facecolor=color, edgecolor="white", linewidth=0.5)
            )

    axis.set_xlim(0, terrain.cols)
    axis.set_ylim(0, terrain.rows)
    axis.set_aspect("equal")
    axis.set_xticks([])
    axis.set_yticks([])


def draw_sample_path(path: list[tuple[int, int]], terrain: Terrain, axis: plt.Axes) -> None:
    """Draw a labeled test path on top of the terrain for layout testing only."""
    xs = [col + 0.5 for _row, col in path]
    ys = [terrain.rows - 1 - row + 0.5 for row, _col in path]

    axis.plot(xs, ys, color="black", linewidth=1.5, linestyle="--", marker="o", markersize=4, zorder=5)
    axis.plot(xs[0], ys[0], marker="*", markersize=16, color="black", zorder=6)


def build_legend_handles(
    include_sample_path: bool = False,
    include_agent_path: bool = False,
    include_collected_science: bool = False,
) -> list:
    """Build legend entries for the terrain types and any drawn overlays."""
    handles = [Patch(facecolor=CELL_COLORS[cell_type], edgecolor="white", label=CELL_LABELS[cell_type]) for cell_type in CELL_LABELS]

    if include_sample_path:
        handles.append(
            Patch(facecolor="none", edgecolor="black", linestyle="--", label="Sample path (test only, not a final result)")
        )

    if include_agent_path:
        handles.append(
            Line2D([], [], color="black", linewidth=2.0, marker="o", markersize=4, label="Agent path (start ★, end ■)")
        )

    if include_collected_science:
        handles.append(
            Line2D([], [], color="none", marker="*", markersize=12, markerfacecolor="#f2c744", markeredgecolor="black", label="Science sample collected")
        )

    return handles


def draw_agent_path(path: list[tuple[int, int]], terrain: Terrain, axis: plt.Axes) -> None:
    """Draw the real path taken by the explorer agent during a simulation."""
    xs = [col + 0.5 for _row, col in path]
    ys = [terrain.rows - 1 - row + 0.5 for row, _col in path]

    axis.plot(xs, ys, color="black", linewidth=2.0, marker="o", markersize=4, zorder=5)
    axis.plot(xs[0], ys[0], marker="*", markersize=18, color="black", zorder=6)
    axis.plot(xs[-1], ys[-1], marker="s", markersize=10, color="black", zorder=6)


def draw_collected_science(positions: list[tuple[int, int]], terrain: Terrain, axis: plt.Axes) -> None:
    """Mark the cells where the agent collected a science sample."""
    for row, col in positions:
        axis.plot(
            col + 0.5,
            terrain.rows - 1 - row + 0.5,
            marker="*",
            markersize=16,
            markerfacecolor="#f2c744",
            markeredgecolor="black",
            zorder=7,
        )


def render_mission_map(
    terrain: Terrain,
    path: list[tuple[int, int]],
    collected_science: list[tuple[int, int]] | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    title: str = "Volcanic Terrain Exploration\n(actual MDP agent path)",
) -> Path:
    """Render the terrain with the agent's real simulation path and save it."""
    figure, axis = plt.subplots(figsize=(8, 8))

    draw_terrain(terrain, axis)
    draw_agent_path(path, terrain, axis)

    if collected_science:
        draw_collected_science(collected_science, terrain, axis)

    axis.set_title(title)
    axis.legend(
        handles=build_legend_handles(
            include_agent_path=True,
            include_collected_science=bool(collected_science),
        ),
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0,
    )
    figure.tight_layout()

    resolved_path = _resolve_output_path(output_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(resolved_path, dpi=120, bbox_inches="tight")
    plt.close(figure)

    return resolved_path


def make_sample_path(terrain: Terrain, max_length: int = 15) -> list[tuple[int, int]]:
    """Build a short sample path of reachable cells starting at BASE, for layout testing only."""
    path = [terrain.base_location]
    visited = {terrain.base_location}

    while len(path) < max_length:
        current = path[-1]
        neighbors = [cell for cell in terrain.get_neighbors(*current) if cell not in visited]
        if not neighbors:
            break

        path.append(neighbors[0])
        visited.add(neighbors[0])

    return path


def render_terrain_map(
    terrain: Terrain,
    output_path: str = DEFAULT_OUTPUT_PATH,
    path: list[tuple[int, int]] | None = None,
) -> Path:
    """Render the terrain (and an optional sample path) and save it as an image."""
    figure, axis = plt.subplots(figsize=(8, 8))

    draw_terrain(terrain, axis)

    if path:
        draw_sample_path(path, terrain, axis)
        axis.set_title("Volcanic Terrain Map\n(with labeled SAMPLE PATH — test layout only, not a final result)")
    else:
        axis.set_title("Volcanic Terrain Map")

    axis.legend(handles=build_legend_handles(include_sample_path=bool(path)), loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
    figure.tight_layout()

    resolved_path = _resolve_output_path(output_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(resolved_path, dpi=120, bbox_inches="tight")
    plt.close(figure)

    return resolved_path


def _resolve_output_path(path: str) -> Path:
    """Resolve a path relative to the project root unless it is already absolute."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def main() -> None:
    """Run a real simulation and render the mission map with the agent's path."""
    from support.simulation import Simulation

    terrain = Terrain(seed=42)
    terrain.generate()

    simulation = Simulation(terrain, max_steps=100, coverage_target=0.60, seed=42)
    summary = simulation.run()

    output_path = render_mission_map(
        terrain,
        path=simulation.agent.path,
        collected_science=simulation.agent.science_collected_positions,
    )

    print(f"Terrain size: {terrain.rows}x{terrain.cols}")
    print(f"Agent path length: {len(simulation.agent.path)}")
    print(f"Science samples collected: {summary['science_points_collected']}")
    print(f"Survived: {summary['survived']}")
    print(f"Saved mission map: {output_path}")


if __name__ == "__main__":
    main()
