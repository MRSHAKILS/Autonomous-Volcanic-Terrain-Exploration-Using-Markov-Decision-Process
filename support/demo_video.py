"""One-minute demo-run video for the volcanic MDP explorer project.

Per the course requirements, the video showcases the project's functionality
from the user's perspective, screen-capture style: a terminal session runs
the real pipeline (``python main.py``), an animated playback of the recorded
mission plays (the agent moving while gas drifts and lava spreads), the
mission map opens, the baseline comparison runs
(``python support/experiments.py``), and the performance plot opens. All
terminal text is the genuine output of those commands, captured when this
script runs, so the video always matches the current code.

Run it with::

    python support/demo_video.py

It writes ``outputs/demo_video.mp4`` (exactly 60 seconds; GIF fallback if
ffmpeg is not installed).
"""

import subprocess
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
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from support.simulation import Simulation
from support.terrain import Terrain
from support.visualization import CELL_COLORS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO_PATH = "outputs/demo_video.mp4"

FRAMES_PER_SECOND = 5
TOTAL_SECONDS = 60

TERMINAL_BG = "#14161d"
TERMINAL_BAR = "#2a2e3a"
TEXT_COLOR = "#d6d9e0"
PROMPT_COLOR = "#7ec46f"
VISIBLE_LINES = 26
FONT_SIZE = 10.5

PROMPT = "user@rover volcanic-mdp-explorer $ "


def record_simulation(seed: int = 42, max_steps: int = 100) -> list[dict]:
    """Run one dynamic-hazard simulation and snapshot it after every step."""
    terrain = Terrain(seed=seed)
    terrain.generate()

    simulation = Simulation(terrain, max_steps=max_steps, coverage_target=0.60, seed=seed, dynamic_hazards=True)

    snapshots = [_snapshot(simulation)]  # initial state before the first step
    simulation.run(on_step=lambda sim: snapshots.append(_snapshot(sim)))
    return snapshots


def _snapshot(simulation: Simulation) -> dict:
    """Copy everything needed to draw one mission-playback frame later."""
    agent = simulation.agent

    return {
        "grid": [row[:] for row in simulation.terrain.grid],
        "path": list(agent.path),
        "collected": list(agent.science_collected_positions),
        "reward": agent.cumulative_reward,
        "science": agent.science_points_collected,
        "alive": agent.alive,
    }


def _run_and_capture(arguments: list[str]) -> list[str]:
    """Run one project command and return its real output lines."""
    result = subprocess.run(
        [sys.executable, *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.rstrip("\n").split("\n")


# ---------------------------------------------------------------------------
# Frame plan: each frame is a dict describing one 1/5-second screen state.
# ---------------------------------------------------------------------------


def _typing_frames(previous_lines: list[str], command: str, seconds: float) -> list[dict]:
    """Frames showing the command being typed at the prompt."""
    count = max(int(seconds * FRAMES_PER_SECOND), 1)
    frames = []

    for index in range(count):
        typed = command[: max(1, round(len(command) * (index + 1) / count))]
        frames.append({"lines": previous_lines + [PROMPT + typed], "image": None, "mission": None})

    return frames


def _output_frames(previous_lines: list[str], command: str, output: list[str], seconds: float) -> list[dict]:
    """Frames revealing command output progressively, then holding."""
    count = max(int(seconds * FRAMES_PER_SECOND), 1)
    base = previous_lines + [PROMPT + command]
    reveal_count = max(count - 2 * FRAMES_PER_SECOND, count // 2)  # hold ~2s at the end
    frames = []

    for index in range(count):
        shown = min(len(output), max(1, round(len(output) * (index + 1) / reveal_count)))
        frames.append({"lines": base + output[:shown], "image": None, "mission": None})

    return frames


def _image_frames(lines: list[str], image_path: Path, title: str, seconds: float) -> list[dict]:
    """Frames showing a generated image opened over the terminal."""
    count = max(int(seconds * FRAMES_PER_SECOND), 1)
    return [{"lines": lines, "image": (image_path, title), "mission": None} for _ in range(count)]


def _mission_frames(lines: list[str], snapshots: list[dict], seconds: float) -> list[dict]:
    """Frames playing back the recorded mission step by step."""
    count = max(int(seconds * FRAMES_PER_SECOND), 1)
    frames = []

    for index in range(count):
        step = min(index * len(snapshots) // count, len(snapshots) - 1)
        frames.append({"lines": lines, "image": None, "mission": (snapshots[step], step)})

    return frames


def build_frames() -> list[dict]:
    """Run the real pipeline, capture its output, and plan all 300 frames."""
    print("Running `python main.py` to capture real output...")
    main_output = _run_and_capture(["main.py"])

    print("Recording the mission playback (dynamic hazards ON)...")
    snapshots = record_simulation(seed=42)

    print("Running `python support/experiments.py` (this takes a while)...")
    experiments_output = _run_and_capture(["support/experiments.py"])
    experiments_tail = experiments_output[-14:]  # summary table + saved paths

    mission_map = PROJECT_ROOT / "outputs" / "final_map.png"
    performance_plot = PROJECT_ROOT / "outputs" / "performance_plot.png"

    frames: list[dict] = []

    # 0-2s: type the pipeline command.
    frames += _typing_frames([], "python main.py", 2)
    # 2-20s: the full pipeline output scrolls through.
    frames += _output_frames([], "python main.py", main_output, 18)
    # 20-34s: animated playback of the recorded mission.
    tail_after_main = frames[-1]["lines"]
    frames += _mission_frames(tail_after_main, snapshots, 14)
    # 34-40s: the generated mission map opens.
    frames += _image_frames(tail_after_main, mission_map, "outputs/final_map.png (mission map)", 6)
    # 40-42s: type the experiments command.
    frames += _typing_frames(tail_after_main + [""], "python support/experiments.py", 2)
    # 42-50s: the comparison summary appears.
    frames += _output_frames(tail_after_main + [""], "python support/experiments.py", experiments_tail, 8)
    # 50-57s: the performance plot opens.
    tail_after_experiments = frames[-1]["lines"]
    frames += _image_frames(tail_after_experiments, performance_plot, "outputs/performance_plot.png (MDP vs baselines)", 7)
    # 57-60s: closing terminal state.
    closing = tail_after_experiments + ["", PROMPT + "# every run is seeded and fully reproducible"]
    frames += [{"lines": closing, "image": None, "mission": None}] * (3 * FRAMES_PER_SECOND)

    # Trim or pad to exactly 60 seconds.
    target = TOTAL_SECONDS * FRAMES_PER_SECOND
    frames = frames[:target]
    frames += [frames[-1]] * (target - len(frames))
    return frames


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------


def _draw_frame(figure: plt.Figure, frame: dict) -> None:
    figure.clear()
    axis = figure.add_axes((0, 0, 1, 1))
    axis.axis("off")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)

    # Terminal background and title bar.
    axis.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor=TERMINAL_BG, zorder=0))
    axis.add_patch(plt.Rectangle((0, 0.955), 1, 0.045, facecolor=TERMINAL_BAR, zorder=1))
    for index, color in enumerate(("#e0605e", "#e0b34f", "#6cc04a")):
        axis.plot(0.018 + index * 0.016, 0.9775, marker="o", markersize=6, color=color, zorder=2)
    axis.text(0.5, 0.9775, "Terminal: volcanic-mdp-explorer", ha="center", va="center", fontsize=10, color="#aab0bd", zorder=2)

    # Visible tail of the terminal text.
    lines = frame["lines"][-VISIBLE_LINES:]
    y = 0.925
    for line in lines:
        color = PROMPT_COLOR if line.startswith(PROMPT) else TEXT_COLOR
        axis.text(0.015, y, line, fontsize=FONT_SIZE, family="monospace", color=color, va="top", zorder=3)
        y -= 0.034

    # Optional animated mission-playback "window" over the terminal.
    if frame["mission"] is not None:
        snapshot, step = frame["mission"]
        axis.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="black", alpha=0.45, zorder=4))
        axis.add_patch(
            plt.Rectangle((0.235, 0.045, ), 0.53, 0.88, facecolor="#f2f0ea", edgecolor="#888888", zorder=4.5)
        )

        window = figure.add_axes((0.27, 0.09, 0.46, 0.72))
        window.set_zorder(5)
        _draw_mission(window, snapshot)

        status = "exploring" if snapshot["alive"] else "destroyed by lava"
        window.set_title(
            f"Mission playback (dynamic hazards ON)\n"
            f"step {step}   reward {snapshot['reward']:.0f}   science {snapshot['science']}   status: {status}",
            fontsize=11,
            color="#33363d",
            pad=8,
        )

    # Optional image "window" opened over the terminal.
    if frame["image"] is not None:
        image_path, title = frame["image"]
        axis.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="black", alpha=0.45, zorder=4))

        window = figure.add_axes((0.2, 0.06, 0.6, 0.8))
        window.imshow(mpimg.imread(str(image_path)))
        window.axis("off")
        window.set_zorder(5)
        window.set_title(title, fontsize=11, color="#33363d", pad=8)
        for spine_position in ((0.185, 0.045, 0.63, 0.86),):
            axis.add_patch(
                plt.Rectangle(
                    spine_position[:2],
                    spine_position[2],
                    spine_position[3],
                    facecolor="#f2f0ea",
                    edgecolor="#888888",
                    zorder=4.5,
                )
            )


def _draw_mission(window: plt.Axes, snapshot: dict) -> None:
    """Draw one recorded mission snapshot: terrain, path so far, samples."""
    grid = snapshot["grid"]
    rows, cols = len(grid), len(grid[0])

    for row in range(rows):
        for col in range(cols):
            window.add_patch(
                plt.Rectangle(
                    (col, rows - 1 - row),
                    1,
                    1,
                    facecolor=CELL_COLORS[grid[row][col]],
                    edgecolor="white",
                    linewidth=0.5,
                )
            )

    path = snapshot["path"]
    xs = [col + 0.5 for _row, col in path]
    ys = [rows - 1 - row + 0.5 for row, _col in path]
    window.plot(xs, ys, color="black", linewidth=2.0, marker="o", markersize=3, zorder=5)
    window.plot(xs[0], ys[0], marker="*", markersize=15, color="black", zorder=6)
    window.plot(xs[-1], ys[-1], marker="s", markersize=8, color="black", zorder=6)

    for row, col in snapshot["collected"]:
        window.plot(
            col + 0.5,
            rows - 1 - row + 0.5,
            marker="*",
            markersize=14,
            markerfacecolor="#f2c744",
            markeredgecolor="black",
            zorder=7,
        )

    window.set_xlim(0, cols)
    window.set_ylim(0, rows)
    window.set_aspect("equal")
    window.set_xticks([])
    window.set_yticks([])


def render_video(frames: list[dict], output_path: str = DEFAULT_VIDEO_PATH) -> Path:
    """Render the planned frames to a 60-second video file."""
    figure = plt.figure(figsize=(12.8, 7.2), dpi=100)

    def update(frame_number: int):
        _draw_frame(figure, frames[frame_number])
        return []

    video = animation.FuncAnimation(figure, update, frames=len(frames), blit=False)

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


def main() -> None:
    """Capture a real demo run and render it as the one-minute video."""
    frames = build_frames()
    print(f"Rendering {TOTAL_SECONDS}s video at {FRAMES_PER_SECOND} fps ({len(frames)} frames)...")
    output_path = render_video(frames)
    print(f"Saved demo video: {output_path}")


if __name__ == "__main__":
    main()
