"""Small utility helpers used across the project."""

import json
from pathlib import Path


def ensure_directory_exists(directory_path: str | Path) -> Path:
    """Create a directory if it does not already exist and return its path."""
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def print_section_header(title: str) -> None:
    """Print a simple section header for console output."""
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def load_json(file_path: str | Path) -> dict:
    """Load and return JSON data from a file."""
    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON format in file: {path}") from error


# TODO: Add result-saving helpers after simulation and experiment outputs are
# introduced in later weeks.
