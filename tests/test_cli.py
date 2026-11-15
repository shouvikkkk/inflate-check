"""Tests for inflatecheck.cli (exit codes, formats, input errors)."""

import json
import os
import tempfile
import unittest

from inflatecheck.cli import main

ORIGINAL = "- Prefer pytest.\n- Just this once, skip the lint step.\n"
INFLATED = "- Always use pytest.\n- Skip the lint step.\n"
CLEAN = "- Prefer pytest.\n- Just this once, skip the lint step.\n"


class TestCli(unittest.TestCase):
    def _write(self, content):
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_clean_exit_0(self):
        self.assertEqual(main([self._write(ORIGINAL), self._write(CLEAN)]), 0)

    def test_inflated_exit_1(self):
        self.assertEqual(main([self._write(ORIGINAL), self._write(INFLATED)]), 1)

    def test_threshold_allows_inflation(self):
        # Both items inflate = 100%; threshold 100 allows it (rate not > threshold).
        self.assertEqual(
            main(
                [
                    self._write(ORIGINAL),
                    self._write(INFLATED),
                    "--threshold",
                    "100",
                ]
            ),
            0,
        )

    def test_json_output(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(
                [self._write(ORIGINAL), self._write(INFLATED), "--format", "json"]
            )
        self.assertEqual(code, 1)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["inflated"], 2)
        self.assertEqual(payload["inflation_rate_pct"], 100.0)

    def test_missing_file_exit_2(self):
        self.assertEqual(main(["/nonexistent/original.md", self._write(CLEAN)]), 2)

    def test_empty_original_exit_2(self):
        self.assertEqual(main([self._write(""), self._write(CLEAN)]), 2)


if __name__ == "__main__":
    unittest.main()
