"""Tests for inflatecheck.align."""

import unittest

from inflatecheck.align import align, jaccard, tokenize


class TestAlign(unittest.TestCase):
    def test_tokenize_drops_stopwords(self):
        self.assertEqual(tokenize("Prefer pytest for new tests"), {"prefer", "pytest", "new", "tests"})

    def test_jaccard(self):
        self.assertAlmostEqual(jaccard({"a", "b"}, {"b", "c"}), 1 / 3)
        self.assertEqual(jaccard(set(), {"a"}), 0.0)
        self.assertEqual(jaccard({"a"}, {"a"}), 1.0)

    def test_greedy_best_match(self):
        original = ["Prefer pytest for tests.", "Always run the linter."]
        summary = ["Always run the linter.", "Prefer pytest for tests."]
        pairs, lost, extra = align(original, summary)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(lost, [])
        self.assertEqual(extra, [])
        self.assertEqual(pairs[0][0], 0)
        self.assertEqual(pairs[0][1], 1)

    def test_lost_and_extra(self):
        original = ["Write tests for the parser.", "Always lint."]
        summary = ["Always lint.", "Do something else entirely."]
        pairs, lost, extra = align(original, summary)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(lost, [0])
        self.assertEqual(extra, [1])

    def test_low_overlap_is_lost(self):
        original = ["Use Postgres instead of MySQL."]
        summary = ["MySQL is the database."]
        pairs, lost, extra = align(original, summary)
        self.assertEqual(pairs, [])
        self.assertEqual(lost, [0])


if __name__ == "__main__":
    unittest.main()
