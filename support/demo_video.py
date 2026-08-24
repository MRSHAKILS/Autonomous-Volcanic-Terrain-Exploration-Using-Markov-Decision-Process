"""Demo video generation for the volcanic MDP explorer project.

Runs a full simulation with dynamic hazards while recording the terrain and
the agent after every step, then renders the recording as an animation:
the terrain evolves (gas drifts, lava spreads and cools), the agent's path
grows frame by frame, and collected science samples are starred.

Run it with::

    python support/demo_video.py

It writes ``outputs/demo_video.mp4`` (and a GIF fallback if ffmpeg is not
installed).
"""

import sys
from pathlib import Path


# Allow this file to run both as a package module and as a direct script:
#   python -m support.demo_video
#   python support/demo_video.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")  # save animations without needing a display
import matplotlib.animation as animation
import matplotlib.pyplot as plt

from support.simulation import Simulation
from support.terrain import Terrain
from support.visualization import CELL_COLORS, build_legend_handles, draw_collected_science


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO_PATH = "outputs/demo_video.mp4"
FRAMES_PER_SECOND = 3


def record_simulation(seed: int = 42, max_steps: int = 100, dynamic_hazards: bool = True) -> tuple[Simulation, list[dict]]:
    """Run one simulation and capture a frame snapshot after every step."""
    terrain = Terrain(seed=seed)
    terrain.generate()

    simulation = Simulation(
        terrain,
        max_steps=max_steps,
        coverage_target=0.60,
        seed=seed,
        dynamic_hazards=dynamic_hazards,
    )

    frames = [_snapshot(simulation)]  # initial state before the first step
    simulation.run(on_step=lambda sim: frames.append(_snapshot(sim)))

    return simulation, frames


def _snapshot(simulation: Simulation) -> dict:
    """Copy everything needed to draw one animation frame later."""
    agent = simulation.agent

    return {
        "grid": [row[:] for row in simulation.terrain.grid],
        "path": list(agent.path),
        "collected": list(agent.science_collected_positions),
        "reward": agent.cumulative_reward,
        "science": agent.science_points_collected,
        "alive": agent.alive,
    }


def _draw_frame(frame: dict, frame_index: int, terrain_rows: int, terrain_cols: int, axis: plt.Axes) -> None:
    """Draw a single recorded frame onto the axis."""
    axis.clear()

    for row in range(terrain_rows):
        for col in range(terrain_cols):
            axis.add_patch(
                plt.Rectangle(
                    (col, terrain_rows - 1 - row),
                    1,
                    1,
                    facecolor=CELL_COLORS[frame["grid"][row][col]],
                    edgecolor="white",
                    linewidth=0.5,
                )
            )

    path = frame["path"]
    xs = [col + 0.5 for _row, col in path]
    ys = [terrain_rows - 1 - row + 0.5 for row, _col in path]
    axis.plot(xs, ys, color="black", linewidth=2.0, marker="o", markersize=3, zorder=5)
    axis.plot(xs[0], ys[0], marker="*", markersize=16, color="black", zorder=6)
    axis.plot(xs[-1], ys[-1], marker="s", markersize=9, color="black", zorder=6)

    class _TerrainLike:
        rows = terrain_rows

    draw_collected_science(frame["collected"], _TerrainLike, axis)

    status = "exploring" if frame["alive"] else "DESTROYED BY LAVA"
    axis.set_title(
        f"Volcanic Terrain Exploration — step {frame_index}\n"
        f"reward: {frame['reward']:.0f}   science: {frame['science']}   status: {status}"
    )
    axis.set_xlim(0, terrain_cols)
    axis.set_ylim(0, terrain_rows)
    axis.set_aspect("equal")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.legend(
        handles=build_legend_handles(include_agent_path=True, include_collected_science=True),
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0,
        fontsize=8,
    )


def render_video(frames: list[dict], terrain_rows: int, terrain_cols: int, output_path: str = DEFAULT_VIDEO_PATH) -> Path:
    """Render the recorded frames to a video file and return the written path."""
    figure, axis = plt.subplots(figsize=(8, 6))
    figure.subplots_adjust(right=0.72)

    def update(frame_index: int):
        _draw_frame(frames[frame_index], frame_index, terrain_rows, terrain_cols, axis)
        return []

    video = animation.FuncAnimation(figure, update, frames=len(frames), blit=False)

    resolved_path = _resolve_output_path(output_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    if animation.FFMpegWriter.isAvailable():
        video.save(resolved_path, writer=animation.FFMpegWriter(fps=FRAMES_PER_SECOND), dpi=110)
    else:
        resolved_path = resolved_path.with_suffix(".gif")
        video.save(resolved_path, writer=animation.PillowWriter(fps=FRAMES_PER_SECOND), dpi=110)

    plt.close(figure)
    return resolved_path


def _resolve_output_path(path: str) -> Path:
    """Resolve a path relative to the project root unless it is absolute."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def main() -> None:
    """Record a dynamic-hazard mission and save it as the demo video."""
    print("Recording simulation (seed 42, dynamic hazards ON)...")
    simulation, frames = record_simulation(seed=42)

    summary = simulation.summary
    print(f"Recorded {len(frames)} frames ({summary['total_steps']} steps).")
    print(f"Science collected: {summary['science_points_collected']}  |  Survived: {summary['survived']}")

    output_path = render_video(frames, simulation.terrain.rows, simulation.terrain.cols)
    print(f"Saved demo video: {output_path}")


if __name__ == "__main__":
    main()
