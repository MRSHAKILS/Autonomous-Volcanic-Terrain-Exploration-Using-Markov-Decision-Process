"""Small utility helpers used across the project."""

import json
from pathlib import Path


def ensure_directory_exists(directory_path: str | Path) -> Path:
    """Create a directory if it does not already exist and return its path."""
    resolved_path = Path(directory_path)
    resolved_path.mkdir(parents=True, exist_ok=True)
    return resolved_path


def print_section_header(title: str) -> None:
    """Print a simple section header for console output."""
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def load_json(file_path: str | Path) -> dict:
    """Load and return JSON data from a file."""
    json_path = Path(file_path)

    try:
        with json_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON format in file: {json_path}") from error
