"""Configuration loading for the volcanic MDP explorer project."""

from pathlib import Path

from support.utils import load_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "data" / "terrain_config.json"

DEFAULT_MDP_PARAMETERS = {
    "gamma": 0.92,
    "movement_probabilities": {
        "intended_direction": 0.75,
        "left_drift": 0.10,
        "right_drift": 0.10,
        "stay": 0.05,
    },
}

MOVEMENT_PROBABILITY_KEYS = [
    "intended_direction",
    "left_drift",
    "right_drift",
    "stay",
]


def load_config(config_path: Path = CONFIG_PATH) -> dict:
    """Load and validate the terrain configuration from a JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file was not found: {config_path}")

    config = load_json(config_path)
    validate_config(config)

    return config


def validate_config(config: dict) -> None:
    """Validate values that are present in the project config.

    Missing sections are allowed because the project has safe defaults. Values
    that are present but invalid should fail loudly so mistakes are easy to fix.
    """
    if not isinstance(config, dict):
        raise ValueError("Configuration data must be a JSON object.")

    _validate_grid_size(config.get("grid_size"))
    _validate_default_probabilities(config.get("default_probabilities"))
    _validate_base_location(config.get("base_location"))
    _validate_mdp_parameters(config.get("mdp_parameters"))


def get_mdp_parameters(config_path: Path = CONFIG_PATH) -> dict:
    """Return MDP parameters from config, using defaults for missing values."""
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        return _copy_default_mdp_parameters()

    mdp_parameters = config.get("mdp_parameters", {})
    merged = _copy_default_mdp_parameters()

    if "gamma" in mdp_parameters:
        merged["gamma"] = float(mdp_parameters["gamma"])

    configured_movement = mdp_parameters.get("movement_probabilities", {})
    for key in MOVEMENT_PROBABILITY_KEYS:
        if key in configured_movement:
            merged["movement_probabilities"][key] = float(configured_movement[key])

    _validate_movement_probabilities(merged["movement_probabilities"])

    return merged


def _copy_default_mdp_parameters() -> dict:
    """Return a fresh copy of the default MDP parameter dictionary."""
    return {
        "gamma": DEFAULT_MDP_PARAMETERS["gamma"],
        "movement_probabilities": DEFAULT_MDP_PARAMETERS["movement_probabilities"].copy(),
    }


def _validate_grid_size(grid_size: object) -> None:
    """Validate grid size values if the section is present."""
    if grid_size is None:
        return
    if not isinstance(grid_size, dict):
        raise ValueError("grid_size must be a JSON object.")

    for key in ["rows", "columns"]:
        if key in grid_size:
            value = grid_size[key]
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"grid_size.{key} must be a positive integer.")


def _validate_default_probabilities(probabilities: object) -> None:
    """Validate terrain probabilities if the section is present."""
    if probabilities is None:
        return
    if not isinstance(probabilities, dict):
        raise ValueError("default_probabilities must be a JSON object.")

    for terrain_name, probability in probabilities.items():
        if not isinstance(probability, (int, float)):
            raise ValueError(f"default_probabilities.{terrain_name} must be a number.")
        if probability < 0 or probability > 1:
            raise ValueError(f"default_probabilities.{terrain_name} must be between 0 and 1.")


def _validate_base_location(base_location: object) -> None:
    """Validate base location values if the section is present."""
    if base_location is None:
        return
    if not isinstance(base_location, dict):
        raise ValueError("base_location must be a JSON object.")

    for key in ["row", "column"]:
        if key in base_location:
            value = base_location[key]
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"base_location.{key} must be a non-negative integer.")


def _validate_mdp_parameters(mdp_parameters: object) -> None:
    """Validate MDP values if the section is present."""
    if mdp_parameters is None:
        return
    if not isinstance(mdp_parameters, dict):
        raise ValueError("mdp_parameters must be a JSON object.")

    if "gamma" in mdp_parameters:
        gamma = mdp_parameters["gamma"]
        if not isinstance(gamma, (int, float)) or not 0 < gamma < 1:
            raise ValueError("mdp_parameters.gamma must be a number between 0 and 1.")

    if "movement_probabilities" in mdp_parameters:
        movement_probabilities = mdp_parameters["movement_probabilities"]
        if not isinstance(movement_probabilities, dict):
            raise ValueError("mdp_parameters.movement_probabilities must be a JSON object.")

        merged = DEFAULT_MDP_PARAMETERS["movement_probabilities"].copy()
        for key, value in movement_probabilities.items():
            if key not in MOVEMENT_PROBABILITY_KEYS:
                raise ValueError(f"Unknown movement probability key: {key}")
            if not isinstance(value, (int, float)):
                raise ValueError(f"movement_probabilities.{key} must be a number.")
            merged[key] = float(value)

        _validate_movement_probabilities(merged)


def _validate_movement_probabilities(probabilities: dict) -> None:
    """Validate that movement probabilities are usable by the MDP."""
    total = 0.0

    for key in MOVEMENT_PROBABILITY_KEYS:
        value = probabilities.get(key)
        if not isinstance(value, (int, float)):
            raise ValueError(f"movement_probabilities.{key} must be a number.")
        if value < 0 or value > 1:
            raise ValueError(f"movement_probabilities.{key} must be between 0 and 1.")
        total += value

    if abs(total - 1.0) > 1e-9:
        raise ValueError("MDP movement probabilities must sum to 1.0.")
