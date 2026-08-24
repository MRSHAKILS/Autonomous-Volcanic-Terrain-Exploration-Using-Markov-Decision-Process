"""Demo video generation for the volcanic MDP explorer project.

Renders a 60-second silent presentation of the whole project, paced for a
voice-over to be recorded on top later:

1. Title card (0-6s)
2. The problem and the terrain (6-16s)
3. How the MDP works, with the actual policy drawn on the map (16-26s)
4. A live mission with dynamic hazards (26-46s)
5. Experimental results vs the baselines (46-55s)
6. Outro (55-60s)

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

from support.mdp import ACTION_DELTAS, SCAN, STAY
from support.simulation import Simulation
from support.terrain import Terrain
from support.visualization import CELL_COLORS, build_legend_handles, draw_collected_science


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO_PATH = "outputs/demo_video.mp4"

FRAMES_PER_SECOND = 5
SCENE_SECONDS = [6, 10, 10, 20, 9, 5]  # title, problem, mdp, mission, results, outro

DARK_BG = "#151821"
LIGHT_BG = "#f7f5ef"
ACCENT = "#c0392b"

# Averages from `python support/experiments.py` (20 seeds); used as a fallback
# when outputs/experiment_results.csv has not been generated locally.
FALLBACK_RESULTS = {
    "MDP": {"reward": 42.0, "survival": 60.0},
    "Greedy": {"reward": -124.5, "survival": 30.0},
    "Random": {"reward": -179.5, "survival": 15.0},
}


# ---------------------------------------------------------------------------
# Mission recording (scene 4 source material).
# ---------------------------------------------------------------------------


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


def _load_results() -> dict:
    """Load averaged experiment results from the CSV, or use the fallback."""
    csv_path = PROJECT_ROOT / "outputs" / "experiment_results.csv"
    if not csv_path.exists():
        return FALLBACK_RESULTS

    try:
        import pandas as pd

        frame = pd.read_csv(csv_path)
        labels = {"mdp": "MDP", "greedy": "Greedy", "random": "Random"}
        results = {}
        for agent_type, label in labels.items():
            rows = frame[frame["agent_type"] == agent_type]
            results[label] = {
                "reward": float(rows["total_reward"].mean()),
                "survival": 100.0 * float(rows["survived"].mean()),
            }
        return results
    except Exception:
        return FALLBACK_RESULTS


# ---------------------------------------------------------------------------
# Shared drawing helpers.
# ---------------------------------------------------------------------------


def _draw_grid(axis: plt.Axes, grid: list[list[str]]) -> None:
    """Draw a terrain grid (list of rows of cell types) as colored squares."""
    rows, cols = len(grid), len(grid[0])

    for row in range(rows):
        for col in range(cols):
            axis.add_patch(
                plt.Rectangle(
                    (col, rows - 1 - row),
                    1,
                    1,
                    facecolor=CELL_COLORS[grid[row][col]],
                    edgecolor="white",
                    linewidth=0.5,
                )
            )

    axis.set_xlim(0, cols)
    axis.set_ylim(0, rows)
    axis.set_aspect("equal")
    axis.set_xticks([])
    axis.set_yticks([])


def _draw_policy_arrows(axis: plt.Axes, policy: dict, rows: int) -> None:
    """Draw the extracted policy as small arrows (STAY = dot, SCAN = ?)."""
    for (row, col), action in policy.items():
        x, y = col + 0.5, rows - 1 - row + 0.5

        if action in ACTION_DELTAS:
            drow, dcol = ACTION_DELTAS[action]
            axis.annotate(
                "",
                xy=(x + dcol * 0.32, y - drow * 0.32),
                xytext=(x - dcol * 0.32, y + drow * 0.32),
                arrowprops={"arrowstyle": "-|>", "color": "black", "linewidth": 1.2},
                zorder=5,
            )
        elif action == STAY:
            axis.plot(x, y, marker="o", markersize=4, color="black", zorder=5)
        elif action == SCAN:
            axis.text(x, y, "?", ha="center", va="center", fontsize=9, color="black", zorder=5)


def _fill_background(figure: plt.Figure, color: str) -> plt.Axes:
    """Cover the whole figure with a solid background and return the axes.

    The animation writer does not honor per-frame figure facecolors, so dark
    scenes paint their own background rectangle instead.
    """
    axis = figure.add_axes((0, 0, 1, 1))
    axis.axis("off")
    axis.add_patch(plt.Rectangle((0, 0), 1, 1, transform=axis.transAxes, facecolor=color, zorder=-1))
    return axis


def _bullet_text(axis: plt.Axes, title: str, bullets: list[str], visible_count: int) -> None:
    """Render a title and a progressively revealed bullet list on a blank axis."""
    axis.axis("off")
    axis.text(0.0, 0.97, title, fontsize=20, fontweight="bold", va="top", transform=axis.transAxes)

    y = 0.82
    for bullet in bullets[:visible_count]:
        axis.text(0.0, y, f"•  {bullet}", fontsize=13.5, va="top", wrap=True, transform=axis.transAxes)
        y -= 0.13


def _reveal_count(local_frame: int, scene_frames: int, total_items: int) -> int:
    """How many bullets should be visible this frame (evenly staged reveal)."""
    return min(total_items, 1 + local_frame * total_items // max(scene_frames - 4, 1))


# ---------------------------------------------------------------------------
# Scenes. Each receives (figure, local_frame, scene_frames, context).
# ---------------------------------------------------------------------------


def _scene_title(figure: plt.Figure, local_frame: int, scene_frames: int, context: dict) -> None:
    axis = _fill_background(figure, DARK_BG)

    axis.text(0.5, 0.66, "Autonomous Volcanic Terrain Exploration", ha="center", fontsize=27, fontweight="bold", color="white")
    axis.text(0.5, 0.57, "Using a Markov Decision Process (MDP)", ha="center", fontsize=20, color="#e8c15a")
    axis.text(0.5, 0.40, "CSE 440 — Artificial Intelligence   ·   Section 1   ·   Group 5", ha="center", fontsize=13, color="#cccccc")
    axis.text(
        0.5,
        0.30,
        "Shakil Ahmed  ·  Fahim Foysal  ·  Shefa Tabassum  ·  Tanvir Ahmed",
        ha="center",
        fontsize=12.5,
        color="#9fb2c8",
    )
    axis.text(0.5, 0.12, "A 60-second tour of the project", ha="center", fontsize=11, color="#777777", style="italic")


def _scene_problem(figure: plt.Figure, local_frame: int, scene_frames: int, context: dict) -> None:

    map_axis = figure.add_axes((0.04, 0.10, 0.44, 0.80))
    _draw_grid(map_axis, context["initial_grid"])
    map_axis.set_title("A randomly generated volcanic terrain", fontsize=13)
    map_axis.legend(handles=build_legend_handles(), loc="upper left", bbox_to_anchor=(0.0, -0.03), ncol=4, fontsize=8, frameon=False)

    bullets = [
        "Volcanic terrain is too dangerous for humans to explore directly",
        "An autonomous rover must collect science samples and survive",
        "Lava is fatal — craters and gas zones are costly — rock blocks the way",
        "Movement is unreliable: the rover can slip sideways or stall",
        "The terrain itself changes while the rover is out there",
    ]
    text_axis = figure.add_axes((0.53, 0.10, 0.44, 0.80))
    _bullet_text(text_axis, "The problem", bullets, _reveal_count(local_frame, scene_frames, len(bullets)))


def _scene_mdp(figure: plt.Figure, local_frame: int, scene_frames: int, context: dict) -> None:

    map_axis = figure.add_axes((0.04, 0.10, 0.44, 0.80))
    _draw_grid(map_axis, context["initial_grid"])
    _draw_policy_arrows(map_axis, context["policy"], rows=len(context["initial_grid"]))
    map_axis.set_title("The computed policy: best action in every cell", fontsize=13)

    bullets = [
        "States: every walkable cell of the grid",
        "Actions: up / down / left / right / stay / scan",
        "Transitions: 75% intended · 10% drift each side · 5% stall",
        "Rewards: science +20 · base +5 · gas −15 · crater −40 · lava −100",
        "Value iteration (γ = 0.9) → an optimal policy for the whole map",
    ]
    text_axis = figure.add_axes((0.53, 0.10, 0.44, 0.80))
    _bullet_text(text_axis, "How the MDP works", bullets, _reveal_count(local_frame, scene_frames, len(bullets)))


def _scene_mission(figure: plt.Figure, local_frame: int, scene_frames: int, context: dict) -> None:

    frames = context["mission_frames"]
    frame_index = min(local_frame * len(frames) // scene_frames, len(frames) - 1)
    frame = frames[frame_index]

    map_axis = figure.add_axes((0.04, 0.08, 0.52, 0.84))
    _draw_grid(map_axis, frame["grid"])

    path = frame["path"]
    rows = len(frame["grid"])
    xs = [col + 0.5 for _row, col in path]
    ys = [rows - 1 - row + 0.5 for row, _col in path]
    map_axis.plot(xs, ys, color="black", linewidth=2.0, marker="o", markersize=3, zorder=5)
    map_axis.plot(xs[0], ys[0], marker="*", markersize=16, color="black", zorder=6)
    map_axis.plot(xs[-1], ys[-1], marker="s", markersize=9, color="black", zorder=6)

    class _TerrainLike:
        pass

    _TerrainLike.rows = rows
    draw_collected_science(frame["collected"], _TerrainLike, map_axis)

    status = "exploring" if frame["alive"] else "destroyed by lava"
    map_axis.set_title(f"Live mission — step {frame_index}", fontsize=13)

    captions = [
        "The agent follows the MDP policy from the base station",
        "Each science sample is collected once — then it re-plans",
        "Dynamic hazards: gas clouds drift, lava spreads and cools",
        "Every terrain change triggers a fresh round of value iteration",
    ]
    caption_index = min(local_frame * len(captions) // scene_frames, len(captions) - 1)

    text_axis = figure.add_axes((0.60, 0.08, 0.37, 0.84))
    text_axis.axis("off")
    text_axis.text(0.0, 0.97, "The mission", fontsize=20, fontweight="bold", va="top", transform=text_axis.transAxes)
    text_axis.text(0.0, 0.80, captions[caption_index], fontsize=14, va="top", wrap=True, transform=text_axis.transAxes)
    text_axis.text(
        0.0,
        0.42,
        f"steps: {max(len(path) - 1, 0)}\nreward: {frame['reward']:.0f}\nscience collected: {frame['science']}\nstatus: {status}",
        fontsize=13,
        va="top",
        family="monospace",
        transform=text_axis.transAxes,
    )
    text_axis.legend(
        handles=build_legend_handles(include_agent_path=True, include_collected_science=True),
        loc="lower left",
        fontsize=8,
        frameon=False,
    )


def _scene_results(figure: plt.Figure, local_frame: int, scene_frames: int, context: dict) -> None:

    results = context["results"]
    labels = ["MDP", "Greedy", "Random"]
    colors = ["#2a7f3f", "#c08a2d", "#b23b3b"]

    figure.text(0.5, 0.92, "MDP vs baselines — 20 random terrains", ha="center", fontsize=19, fontweight="bold")

    reward_axis = figure.add_axes((0.08, 0.16, 0.38, 0.62))
    rewards = [results[label]["reward"] for label in labels]
    reward_axis.bar(labels, rewards, color=colors)
    reward_axis.axhline(0, color="black", linewidth=0.8)
    reward_axis.set_title("Average total reward", fontsize=13)
    for index, value in enumerate(rewards):
        reward_axis.text(index, value, f"{value:.0f}", ha="center", va="bottom" if value >= 0 else "top", fontsize=11)

    survival_axis = figure.add_axes((0.56, 0.16, 0.38, 0.62))
    survivals = [results[label]["survival"] for label in labels]
    survival_axis.bar(labels, survivals, color=colors)
    survival_axis.set_ylim(0, 100)
    survival_axis.set_title("Survival rate (%)", fontsize=13)
    for index, value in enumerate(survivals):
        survival_axis.text(index, value, f"{value:.0f}%", ha="center", va="bottom", fontsize=11)

    figure.text(
        0.5,
        0.045,
        "Only the MDP agent earns positive reward — with twice the survival of greedy and far fewer hazards entered",
        ha="center",
        fontsize=12.5,
        color=ACCENT,
    )


def _scene_outro(figure: plt.Figure, local_frame: int, scene_frames: int, context: dict) -> None:
    axis = _fill_background(figure, DARK_BG)

    axis.text(0.5, 0.62, "Plan under uncertainty. Adapt when the world changes. Survive.", ha="center", fontsize=18, color="white")
    axis.text(0.5, 0.46, "Autonomous Volcanic Terrain Exploration Using MDP", ha="center", fontsize=14, color="#e8c15a")
    axis.text(0.5, 0.36, "CSE 440 · Group 5 — Shakil · Fahim · Shefa · Tanvir", ha="center", fontsize=12, color="#9fb2c8")


SCENES = [_scene_title, _scene_problem, _scene_mdp, _scene_mission, _scene_results, _scene_outro]


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------


def render_video(context: dict, output_path: str = DEFAULT_VIDEO_PATH) -> Path:
    """Render all scenes to a 60-second video and return the written path."""
    scene_frame_counts = [seconds * FRAMES_PER_SECOND for seconds in SCENE_SECONDS]
    total_frames = sum(scene_frame_counts)

    figure = plt.figure(figsize=(12.8, 7.2), dpi=100)

    def update(frame_number: int):
        figure.clear()

        remaining = frame_number
        for scene, scene_frames in zip(SCENES, scene_frame_counts):
            if remaining < scene_frames:
                scene(figure, remaining, scene_frames, context)
                break
            remaining -= scene_frames

        return []

    video = animation.FuncAnimation(figure, update, frames=total_frames, blit=False)

    resolved_path = _resolve_output_path(output_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    if animation.FFMpegWriter.isAvailable():
        video.save(resolved_path, writer=animation.FFMpegWriter(fps=FRAMES_PER_SECOND), dpi=100)
    else:
        resolved_path = resolved_path.with_suffix(".gif")
        video.save(resolved_path, writer=animation.PillowWriter(fps=FRAMES_PER_SECOND), dpi=100)

    plt.close(figure)
    return resolved_path


def _resolve_output_path(path: str) -> Path:
    """Resolve a path relative to the project root unless it is absolute."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def build_context(seed: int = 42) -> dict:
    """Gather everything the scenes need: terrain, policy, mission, results."""
    # A pristine terrain and its policy for the problem/MDP scenes.
    terrain = Terrain(seed=seed)
    terrain.generate()
    initial_grid = [row[:] for row in terrain.grid]

    from support.mdp import VolcanicMDP

    mdp = VolcanicMDP(terrain)
    mdp.value_iteration()
    policy = mdp.extract_policy()

    # A fresh recording of the dynamic-hazard mission for the live scene.
    simulation, mission_frames = record_simulation(seed=seed)

    return {
        "initial_grid": initial_grid,
        "policy": policy,
        "mission_frames": mission_frames,
        "results": _load_results(),
        "summary": simulation.summary,
    }


def main() -> None:
    """Build the 60-second project presentation video."""
    print("Preparing scenes (terrain, policy, mission recording, results)...")
    context = build_context(seed=42)

    summary = context["summary"]
    print(f"Mission recorded: {summary['total_steps']} steps, science {summary['science_points_collected']}, survived {summary['survived']}")

    total_seconds = sum(SCENE_SECONDS)
    print(f"Rendering {total_seconds}s video at {FRAMES_PER_SECOND} fps ({total_seconds * FRAMES_PER_SECOND} frames)...")
    output_path = render_video(context)
    print(f"Saved demo video: {output_path}")


if __name__ == "__main__":
    main()
