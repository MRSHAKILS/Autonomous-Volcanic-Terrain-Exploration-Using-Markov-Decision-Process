"""Volcanic terrain generation for Week 2.

This module creates a simple grid-based volcanic map that will later be used
by the MDP, agent, simulation, and visualization modules.
"""

import csv
import random
import sys
from pathlib import Path


# Allow this file to run both as a module and as a direct script:
#   python -m support.terrain
#   python support/terrain.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from support.config import load_config


SAFE = "SAFE"
LAVA = "LAVA"
CRATER = "CRATER"
GAS = "GAS"
ROCK = "ROCK"
SCIENCE = "SCIENCE"
BASE = "BASE"

TERRAIN_TYPES = [SAFE, LAVA, CRATER, GAS, ROCK, SCIENCE, BASE]
HAZARD_TYPES = [LAVA, CRATER, GAS]
OBSTACLE_TYPES = [ROCK]

SYMBOLS = {
    SAFE: ".",
    LAVA: "L",
    CRATER: "C",
    GAS: "G",
    ROCK: "R",
    SCIENCE: "S",
    BASE: "B",
}

CONFIG_NAME_TO_CELL_TYPE = {
    "safe": SAFE,
    "lava": LAVA,
    "crater": CRATER,
    "gas": GAS,
    "rock": ROCK,
    "science_point": SCIENCE,
    "base": BASE,
}

DEFAULT_PROBABILITIES = {
    SAFE: 0.55,
    LAVA: 0.08,
    CRATER: 0.07,
    GAS: 0.06,
    ROCK: 0.14,
    SCIENCE: 0.10,
}


class Terrain:
    """Create and manage a 2D volcanic terrain grid."""

    def __init__(self, rows: int | None = None, cols: int | None = None, seed: int | None = None) -> None:
        """Set up terrain settings before generating the grid."""
        self.seed = seed
        self.random_generator = random.Random(seed)
        self.config = self._load_default_config()
        self._uses_custom_grid_size = rows is not None or cols is not None

        self.rows = rows or self._get_config_grid_value("rows", default=15)
        self.cols = cols or self._get_config_grid_value("columns", default=15)
        self.probabilities = self._get_probabilities_from_config()
        self.base_location = self._get_base_location()
        self.grid = self._create_empty_grid()

    def _load_default_config(self) -> dict:
        """Load terrain settings from the project config file if it exists."""
        try:
            return load_config()
        except (FileNotFoundError, ValueError):
            return {}

    def _get_config_grid_value(self, key: str, default: int) -> int:
        """Read a grid size value from config, falling back to a safe default."""
        grid_size = self.config.get("grid_size", {})
        value = grid_size.get(key, default)

        if not isinstance(value, int) or value <= 0:
            return default

        return value

    def _get_probabilities_from_config(self) -> dict[str, float]:
        """Read terrain probabilities from config and keep the map balanced."""
        config_probabilities = self.config.get("default_probabilities", {})
        probabilities = DEFAULT_PROBABILITIES.copy()

        for config_name, probability in config_probabilities.items():
            cell_type = CONFIG_NAME_TO_CELL_TYPE.get(config_name)
            if cell_type in probabilities and isinstance(probability, (int, float)):
                probabilities[cell_type] = max(0.0, float(probability))

        return self._limit_crowded_hazards(probabilities)

    def _limit_crowded_hazards(self, probabilities: dict[str, float]) -> dict[str, float]:
        """Limit hazardous cells so the generated map stays usable."""
        max_hazard_total = 0.30
        hazard_total = sum(probabilities.get(cell_type, 0.0) for cell_type in HAZARD_TYPES)

        if hazard_total > max_hazard_total:
            scale = max_hazard_total / hazard_total
            for cell_type in HAZARD_TYPES:
                probabilities[cell_type] *= scale

        return probabilities

    def _get_base_location(self) -> tuple[int, int]:
        """Return the base location, using bottom-left as the default."""
        if self._uses_custom_grid_size:
            return self.rows - 1, 0

        config_location = self.config.get("base_location", {})
        row = config_location.get("row")
        col = config_location.get("column")

        if isinstance(row, int) and isinstance(col, int):
            if 0 <= row < self.rows and 0 <= col < self.cols:
                return row, col

        return self.rows - 1, 0

    def _create_empty_grid(self) -> list[list[str]]:
        """Create a grid filled with safe cells."""
        return [[SAFE for _ in range(self.cols)] for _ in range(self.rows)]

    def generate(self) -> list[list[str]]:
        """Generate a new random terrain grid."""
        self.grid = self._create_empty_grid()

        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) == self.base_location:
                    continue

                self.grid[row][col] = self._choose_random_cell_type()

        base_row, base_col = self.base_location
        self.grid[base_row][base_col] = BASE

        return self.grid

    def _choose_random_cell_type(self) -> str:
        """Choose one cell type using configured probabilities."""
        random_value = self.random_generator.random()
        running_total = 0.0

        for cell_type in [LAVA, CRATER, GAS, ROCK, SCIENCE]:
            running_total += self.probabilities.get(cell_type, 0.0)
            if random_value < running_total:
                return cell_type

        return SAFE

    def get_cell(self, row: int, col: int) -> str:
        """Return the terrain type at a grid position."""
        if not self.is_valid_position(row, col):
            raise IndexError(f"Invalid grid position: ({row}, {col})")

        return self.grid[row][col]

    def set_cell(self, row: int, col: int, cell_type: str) -> None:
        """Set the terrain type at a grid position."""
        if not self.is_valid_position(row, col):
            raise IndexError(f"Invalid grid position: ({row}, {col})")

        normalized_type = cell_type.upper()
        if normalized_type not in TERRAIN_TYPES:
            raise ValueError(f"Unknown terrain type: {cell_type}")

        base_row, base_col = self.base_location
        if (row, col) == (base_row, base_col) and normalized_type != BASE:
            raise ValueError("The base cell cannot be overwritten.")

        self.grid[row][col] = normalized_type

    def is_valid_position(self, row: int, col: int) -> bool:
        """Check whether a position is inside the terrain grid."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_obstacle(self, row: int, col: int) -> bool:
        """Return True if the cell blocks movement."""
        return self.get_cell(row, col) in OBSTACLE_TYPES

    def is_hazard(self, row: int, col: int) -> bool:
        """Return True if the cell is a hazardous terrain type."""
        return self.get_cell(row, col) in HAZARD_TYPES

    def get_neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Return valid non-obstacle neighboring positions."""
        possible_neighbors = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]
        neighbors = []

        for neighbor_row, neighbor_col in possible_neighbors:
            if self.is_valid_position(neighbor_row, neighbor_col):
                if not self.is_obstacle(neighbor_row, neighbor_col):
                    neighbors.append((neighbor_row, neighbor_col))

        return neighbors

    def count_cell_types(self) -> dict[str, int]:
        """Count how many cells of each terrain type exist in the grid."""
        counts = {cell_type: 0 for cell_type in TERRAIN_TYPES}

        for row in self.grid:
            for cell_type in row:
                counts[cell_type] += 1

        return counts

    def save_to_csv(self, path: str | Path) -> None:
        """Save the terrain grid to a CSV file."""
        csv_path = Path(path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(self.grid)

    def load_from_csv(self, path: str | Path) -> list[list[str]]:
        """Load a terrain grid from a CSV file."""
        csv_path = Path(path)

        with csv_path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            loaded_grid = [[cell.strip().upper() for cell in row] for row in reader]

        self._validate_loaded_grid(loaded_grid)
        self.grid = loaded_grid
        self.rows = len(loaded_grid)
        self.cols = len(loaded_grid[0])
        self.base_location = self._find_base_location()

        return self.grid

    def _validate_loaded_grid(self, loaded_grid: list[list[str]]) -> None:
        """Check that a loaded CSV grid is rectangular and uses known cells."""
        if not loaded_grid:
            raise ValueError("The CSV file does not contain any terrain rows.")

        expected_cols = len(loaded_grid[0])
        if expected_cols == 0:
            raise ValueError("The CSV file contains an empty terrain row.")

        base_count = 0
        for row in loaded_grid:
            if len(row) != expected_cols:
                raise ValueError("The loaded terrain grid must be rectangular.")

            for cell_type in row:
                if cell_type not in TERRAIN_TYPES:
                    raise ValueError(f"Unknown terrain type in CSV: {cell_type}")
                if cell_type == BASE:
                    base_count += 1

        if base_count != 1:
            raise ValueError("The loaded terrain grid must contain exactly one BASE cell.")

    def _find_base_location(self) -> tuple[int, int]:
        """Find the base location in the current grid."""
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == BASE:
                    return row, col

        raise ValueError("No BASE cell was found in the terrain grid.")

    def print_grid(self) -> None:
        """Print the terrain grid with simple text symbols."""
        for row in self.grid:
            symbols = [SYMBOLS[cell_type] for cell_type in row]
            print(" ".join(symbols))


# TODO: In Week 3, connect this terrain representation to the MDP state space.
# TODO: In Week 4, allow hazards to change during simulation if dynamic terrain
# behavior is needed.


if __name__ == "__main__":
    terrain = Terrain(seed=42)
    terrain.generate()
    terrain.print_grid()
    print(terrain.count_cell_types())
