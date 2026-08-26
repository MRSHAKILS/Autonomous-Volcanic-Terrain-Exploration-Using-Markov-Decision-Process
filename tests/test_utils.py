"""Unit tests for support/utils.py."""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from support.utils import ensure_directory_exists, load_json, print_section_header


class EnsureDirectoryExistsTests(unittest.TestCase):
    def test_creates_missing_directory(self):
        with TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "nested" / "outputs"
            result = ensure_directory_exists(target)

            self.assertTrue(target.is_dir())
            self.assertEqual(result, target)

    def test_is_safe_to_call_on_existing_directory(self):
        with TemporaryDirectory() as tmp_dir:
            result = ensure_directory_exists(tmp_dir)
            self.assertEqual(result, Path(tmp_dir))


class LoadJsonTests(unittest.TestCase):
    def test_loads_valid_json_file(self):
        with TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "data.json"
            json_path.write_text(json.dumps({"seed": 42}), encoding="utf-8")

            self.assertEqual(load_json(json_path), {"seed": 42})

    def test_raises_value_error_on_malformed_json(self):
        with TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "broken.json"
            json_path.write_text("{not valid json", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_json(json_path)


class PrintSectionHeaderTests(unittest.TestCase):
    def test_prints_title_between_separator_lines(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            print_section_header("Mission Summary")

        lines = buffer.getvalue().splitlines()
        self.assertIn("Mission Summary", lines)
        self.assertTrue(all(char == "=" for char in lines[-1]))


if __name__ == "__main__":
    unittest.main()
