"""Tests for inflatecheck.segment."""

import unittest

from inflatecheck.segment import segment


class TestSegment(unittest.TestCase):
    def test_bullets(self):
        text = "- Prefer pytest.\n- Always run the linter.\n"
        self.assertEqual(segment(text), ["Prefer pytest.", "Always run the linter."])

    def test_numbered_list(self):
        text = "1. First rule.\n2. Second rule.\n"
        self.assertEqual(segment(text), ["First rule.", "Second rule."])

    def test_paragraph_sentences(self):
        text = "Prefer pytest. Always run the linter before pushing."
        self.assertEqual(
            segment(text),
            ["Prefer pytest.", "Always run the linter before pushing."],
        )

    def test_heading_attaches_to_next_item(self):
        text = "## Testing\n- Prefer pytest.\n"
        self.assertEqual(segment(text), ["Testing: Prefer pytest."])

    def test_blank_lines_skipped(self):
        text = "\n\n- One.\n\n- Two.\n\n"
        self.assertEqual(segment(text), ["One.", "Two."])

    def test_abbreviations_not_split(self):
        text = "Use e.g. pytest for tests. Always lint."
        self.assertEqual(
            segment(text),
            ["Use e.g. pytest for tests.", "Always lint."],
        )


if __name__ == "__main__":
    unittest.main()
