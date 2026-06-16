"""Entry point for the Week 1 project skeleton."""

from pathlib import Path

from support.config import load_config
from support.utils import print_section_header


PROJECT_TITLE = "Autonomous Volcanic Terrain Exploration Using Markov Decision Process (MDP)"


def check_repository_structure() -> list[str]:
    """Return a readable status list for the expected Week 1 files and folders."""
    expected_paths = [
        "README.md",
        "requirements.txt",
        ".gitignore",
        "data/.gitkeep",
        "data/terrain_config.json",
        "support/__init__.py",
        "support/config.py",
        "support/utils.py",
        "support/terrain.py",
        "support/mdp.py",
        "support/agent.py",
        "support/simulation.py",
        "support/visualization.py",
        "support/experiments.py",
        "outputs/.gitkeep",
        "others/.gitkeep",
    ]

    project_root = Path(__file__).resolve().parent
    status_messages = []

    for relative_path in expected_paths:
        path = project_root / relative_path
        if path.exists():
            status_messages.append(f"[OK] {relative_path}")
        else:
            status_messages.append(f"[MISSING] {relative_path}")

    return status_messages


def main() -> None:
    """Run the Week 1 setup check."""
    print_section_header("Project Title")
    print(PROJECT_TITLE)

    print_section_header("Week 1 Setup Status")
    config = load_config()
    print("[OK] Project skeleton is ready.")
    print(f"[OK] Terrain configuration loaded for a {config['grid_size']['rows']}x{config['grid_size']['columns']} grid.")

    print_section_header("Repository Structure Status")
    for message in check_repository_structure():
        print(message)

    print_section_header("Next Development Steps")
    next_steps = [
        "Define the terrain grid representation.",
        "Plan MDP states, actions, rewards, and transitions.",
        "Implement a basic agent interface.",
        "Add simulation flow after the MDP design is approved.",
        "Create simple visualizations once terrain and policies exist.",
    ]

    for index, step in enumerate(next_steps, start=1):
        print(f"{index}. {step}")


if __name__ == "__main__":
    main()
