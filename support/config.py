"""Configuration loading for the volcanic MDP explorer project."""

from pathlib import Path

from support.utils import load_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "data" / "terrain_config.json"


def load_config(config_path: Path = CONFIG_PATH) -> dict:
    """Load the terrain configuration from a JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file was not found: {config_path}")

    config = load_json(config_path)

    required_sections = [
        "grid_size",
        "terrain_types",
        "default_probabilities",
        "base_location",
        "mdp_parameters",
    ]

    missing_sections = []
    for section in required_sections:
        if section not in config:
            missing_sections.append(section)

    if missing_sections:
        missing_text = ", ".join(missing_sections)
        raise ValueError(f"Configuration file is missing required section(s): {missing_text}")

    return config
