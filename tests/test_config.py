"""Unit tests for support/config.py."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support.config import get_mdp_parameters, load_config, validate_config


class LoadConfigTests(unittest.TestCase):
    def test_missing_file_raises_file_not_found(self):
        missing_path = Path("does_not_exist_terrain_config.json")
        with self.assertRaises(FileNotFoundError):
            load_config(missing_path)

    def test_loads_well_formed_config(self):
        with TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "terrain_config.json"
            config_path.write_text(json.dumps({"grid_size": {"rows": 10, "columns": 10}}), encoding="utf-8")

            config = load_config(config_path)
            self.assertEqual(config["grid_size"]["rows"], 10)


class ValidateConfigTests(unittest.TestCase):
    def test_accepts_empty_config(self):
        validate_config({})

    def test_rejects_non_dict_config(self):
        with self.assertRaises(ValueError):
            validate_config(["not", "a", "dict"])

    def test_rejects_non_positive_grid_size(self):
        with self.assertRaises(ValueError):
            validate_config({"grid_size": {"rows": 0, "columns": 10}})

    def test_rejects_out_of_range_probability(self):
        with self.assertRaises(ValueError):
            validate_config({"default_probabilities": {"lava": 1.5}})

    def test_rejects_movement_probabilities_that_do_not_sum_to_one(self):
        with self.assertRaises(ValueError):
            validate_config(
                {
                    "mdp_parameters": {
                        "movement_probabilities": {
                            "intended_direction": 0.5,
                            "left_drift": 0.1,
                            "right_drift": 0.1,
                            "stay": 0.05,
                        }
                    }
                }
            )


class GetMdpParametersTests(unittest.TestCase):
    def test_falls_back_to_defaults_when_file_is_missing(self):
        parameters = get_mdp_parameters(Path("does_not_exist_terrain_config.json"))

        self.assertEqual(parameters["gamma"], 0.92)
        self.assertAlmostEqual(sum(parameters["movement_probabilities"].values()), 1.0)

    def test_overrides_only_the_configured_values(self):
        with TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "terrain_config.json"
            config_path.write_text(json.dumps({"mdp_parameters": {"gamma": 0.5}}), encoding="utf-8")

            parameters = get_mdp_parameters(config_path)

            self.assertEqual(parameters["gamma"], 0.5)
            self.assertAlmostEqual(sum(parameters["movement_probabilities"].values()), 1.0)


if __name__ == "__main__":
    unittest.main()
