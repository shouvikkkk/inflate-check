"""Fixture-based precision/recall self-test.

24 paired (original, summary) cases modelled on the Constraint Inflation
paper's templates. Each pair has an expected verdict; the classifier is
scored against all of them, and the test fails if precision or recall
drops below the bar. This is the honest-measurement half of the tool:
a detector that cannot beat its own fixtures is not shippable.
"""

import unittest

from inflatecheck.classify import classify_pair

# (original, summary, expected verdict, expected inflation type or None)
FIXTURES = [
    # --- preference -> requirement ---
    (
        "Prefer tabs over spaces for indentation.",
        "Always use tabs over spaces for indentation.",
        "INFLATED",
        "preference-to-requirement",
    ),
    (
        "Try to keep functions short.",
        "Functions must be short.",
        "INFLATED",
        "preference-to-requirement",
    ),
    (
        "Ideally run tests before pushing.",
        "You must run tests before pushing.",
        "INFLATED",
        "preference-to-requirement",
    ),
    (
        "You should review your own diff first.",
        "You must review your own diff first.",
        "INFLATED",
        "preference-to-requirement",
    ),
    ("Always run the linter.", "Always run the linter.", "PRESERVED", None),
    ("Prefer dark mode.", "Dark mode is preferred.", "PRESERVED", None),
    # --- one-off -> standing ---
    (
        "Just this once, skip the review.",
        "Skip the review.",
        "INFLATED",
        "one-off-to-standing",
    ),
    (
        "For this file only, allow the long line.",
        "Allow long lines.",
        "INFLATED",
        "one-off-to-standing",
    ),
    (
        "Today only, the cache TTL is 5 minutes.",
        "The cache TTL is 5 minutes.",
        "INFLATED",
        "one-off-to-standing",
    ),
    (
        "Just this once, deploy without approval.",
        "Just this once, deploy without approval.",
        "PRESERVED",
        None,
    ),
    # --- scope broadening ---
    (
        "Test some endpoints before release.",
        "Test all endpoints before release.",
        "INFLATED",
        "scope-broadening",
    ),
    (
        "Refactor this module.",
        "Refactor every module.",
        "INFLATED",
        "scope-broadening",
    ),
    (
        "Check a few logs.",
        "Check all logs.",
        "INFLATED",
        "scope-broadening",
    ),
    (
        "Test all endpoints before release.",
        "Test all endpoints before release.",
        "PRESERVED",
        None,
    ),
    # --- stale value retained ---
    (
        "Use Postgres instead of MySQL.",
        "MySQL is the database we use.",
        "INFLATED",
        "stale-value-retained",
    ),
    (
        "Replace SQLite with Postgres for storage.",
        "Postgres is the storage database.",
        "PRESERVED",
        None,
    ),
    (
        "Use Postgres instead of MySQL.",
        "Do not use MySQL anymore.",
        "PRESERVED",
        None,
    ),
    (
        "Switch from npm to pnpm for the build.",
        "npm is the package manager for the build.",
        "INFLATED",
        "stale-value-retained",
    ),
    # --- false-positive guards ---
    ("Never commit secrets.", "Never commit secrets.", "PRESERVED", None),
    (
        "Prefer pytest.",
        "Prefer pytest for all new tests.",
        "PRESERVED",
        None,
    ),
    (
        "Always use two-factor auth.",
        "Use two-factor auth.",
        "PRESERVED",
        None,
    ),
    ("For this file, use tabs.", "For this file, use tabs.", "PRESERVED", None),
    (
        "Use the new API key instead of the old one.",
        "The new API key is in use.",
        "PRESERVED",
        None,
    ),
    (
        "Write tests for the parser.",
        "Write tests for the parser and the lexer.",
        "PRESERVED",
        None,
    ),
]


class TestFixtures(unittest.TestCase):
    def test_all_fixtures(self):
        failures = []
        for original, summary, expected_verdict, expected_type in FIXTURES:
            result = classify_pair(original, summary)
            if (
                result["verdict"] != expected_verdict
                or result["inflation_type"] != expected_type
            ):
                failures.append(
                    "orig=%r summ=%r expected=%s/%s got=%s/%s"
                    % (
                        original,
                        summary,
                        expected_verdict,
                        expected_type,
                        result["verdict"],
                        result["inflation_type"],
                    )
                )
        self.assertEqual(failures, [], "\n".join(failures))

    def test_precision_and_recall(self):
        # Precision = flagged inflation that really is inflation.
        # Recall = real inflation that got flagged.
        true_pos = false_pos = false_neg = 0
        for original, summary, expected_verdict, _ in FIXTURES:
            result = classify_pair(original, summary)
            predicted = result["verdict"] == "INFLATED"
            actual = expected_verdict == "INFLATED"
            if predicted and actual:
                true_pos += 1
            elif predicted and not actual:
                false_pos += 1
            elif not predicted and actual:
                false_neg += 1
        precision = true_pos / (true_pos + false_pos) if true_pos + false_pos else 1.0
        recall = true_pos / (true_pos + false_neg) if true_pos + false_neg else 1.0
        self.assertGreaterEqual(precision, 0.9, "precision %.2f" % precision)
        self.assertGreaterEqual(recall, 0.9, "recall %.2f" % recall)


if __name__ == "__main__":
    unittest.main()
