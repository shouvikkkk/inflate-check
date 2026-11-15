"""Tests for the four inflation detectors in inflatecheck.classify."""

import unittest

from inflatecheck.classify import (
    audit,
    classify_pair,
    detect_modal_inflation,
    detect_oneoff_inflation,
    detect_scope_inflation,
    detect_stale_value,
    find_replacements,
)


class TestModalInflation(unittest.TestCase):
    def test_prefer_to_always(self):
        self.assertIsNotNone(
            detect_modal_inflation("Prefer tabs over spaces.", "Always use tabs.")
        )

    def test_try_to_must(self):
        self.assertIsNotNone(
            detect_modal_inflation("Try to keep functions short.", "Functions must be short.")
        )

    def test_should_to_must(self):
        self.assertIsNotNone(
            detect_modal_inflation(
                "You should review your own diff first.",
                "You must review your own diff first.",
            )
        )

    def test_already_strong_is_not_inflation(self):
        self.assertIsNone(
            detect_modal_inflation("Always run the linter.", "Always run the linter.")
        )

    def test_weak_to_weak_is_not_inflation(self):
        self.assertIsNone(
            detect_modal_inflation("Prefer pytest.", "Prefer pytest for new tests.")
        )


class TestOneOffInflation(unittest.TestCase):
    def test_just_this_once_dropped(self):
        self.assertIsNotNone(
            detect_oneoff_inflation("Just this once, skip the review.", "Skip the review.")
        )

    def test_today_only_dropped(self):
        self.assertIsNotNone(
            detect_oneoff_inflation(
                "Today only, the cache TTL is 5 minutes.",
                "The cache TTL is 5 minutes.",
            )
        )

    def test_scope_kept_is_not_inflation(self):
        self.assertIsNone(
            detect_oneoff_inflation(
                "Just this once, deploy without approval.",
                "Just this once, deploy without approval.",
            )
        )

    def test_no_scope_marker_no_flag(self):
        self.assertIsNone(
            detect_oneoff_inflation("Skip the review.", "Always skip the review.")
        )


class TestScopeInflation(unittest.TestCase):
    def test_some_to_all(self):
        self.assertIsNotNone(
            detect_scope_inflation(
                "Test some endpoints before release.",
                "Test all endpoints before release.",
            )
        )

    def test_this_to_every(self):
        self.assertIsNotNone(
            detect_scope_inflation("Refactor this module.", "Refactor every module.")
        )

    def test_already_broad_is_not_inflation(self):
        self.assertIsNone(
            detect_scope_inflation(
                "Test all endpoints before release.",
                "Test all endpoints before release.",
            )
        )

    def test_broad_word_without_narrow_counterpart(self):
        # "all" in the summary with no narrow quantifier in the original
        # is not inflation — the original never narrowed the scope.
        self.assertIsNone(
            detect_scope_inflation("Prefer pytest.", "Prefer pytest for all new tests.")
        )


class TestStaleValue(unittest.TestCase):
    def test_replacement_extraction(self):
        self.assertEqual(
            find_replacements("Use Postgres instead of MySQL."),
            [("mysql", "postgres")],
        )
        self.assertEqual(
            find_replacements("Replace SQLite with Postgres for storage."),
            [("sqlite", "postgres")],
        )
        self.assertEqual(
            find_replacements("Switch from npm to pnpm for the build."),
            [("npm", "pnpm")],
        )

    def test_old_value_still_current(self):
        self.assertIsNotNone(
            detect_stale_value(
                "Use Postgres instead of MySQL.",
                "MySQL is the database we use.",
            )
        )

    def test_new_value_mentioned_is_clean(self):
        self.assertIsNone(
            detect_stale_value(
                "Replace SQLite with Postgres for storage.",
                "Postgres is the storage database.",
            )
        )

    def test_negation_of_old_value_is_clean(self):
        self.assertIsNone(
            detect_stale_value(
                "Use Postgres instead of MySQL.",
                "Do not use MySQL anymore.",
            )
        )


class TestClassifyPair(unittest.TestCase):
    def test_preserved(self):
        result = classify_pair("Prefer pytest.", "Prefer pytest for new tests.")
        self.assertEqual(result["verdict"], "PRESERVED")

    def test_modal_inflation_type(self):
        result = classify_pair(
            "Prefer tabs over spaces for indentation.",
            "Always use tabs over spaces for indentation.",
        )
        self.assertEqual(result["verdict"], "INFLATED")
        self.assertEqual(result["inflation_type"], "preference-to-requirement")

    def test_oneoff_inflation_type(self):
        result = classify_pair(
            "Just this once, skip the review.", "Skip the review."
        )
        self.assertEqual(result["verdict"], "INFLATED")
        self.assertEqual(result["inflation_type"], "one-off-to-standing")

    def test_scope_inflation_type(self):
        result = classify_pair(
            "Test some endpoints before release.",
            "Test all endpoints before release.",
        )
        self.assertEqual(result["verdict"], "INFLATED")
        self.assertEqual(result["inflation_type"], "scope-broadening")

    def test_stale_value_type(self):
        result = classify_pair(
            "Use Postgres instead of MySQL.",
            "MySQL is the database we use.",
        )
        self.assertEqual(result["verdict"], "INFLATED")
        self.assertEqual(result["inflation_type"], "stale-value-retained")

    def test_weakening_is_not_inflation(self):
        # A summary that *weakens* a rule is a different failure (loss of
        # strength), not inflation — never flagged here.
        result = classify_pair(
            "Always use two-factor auth.", "Use two-factor auth."
        )
        self.assertEqual(result["verdict"], "PRESERVED")


class TestAudit(unittest.TestCase):
    def test_inflated_example(self):
        original = (
            "- Prefer pytest for new tests, but unittest is fine for quick checks.\n"
            "- Just this once, skip the lint step for the hotfix branch.\n"
            "- Run the migration on some staging databases before the release.\n"
            "- Use the new Redis cache instead of the old Memcached layer.\n"
            "- Keep the API response under 200ms where possible.\n"
            "- Write a changelog entry for every user-facing change.\n"
        )
        summary = (
            "- Always use pytest for new tests; unittest is never allowed.\n"
            "- Skip the lint step for the hotfix branch.\n"
            "- Run the migration on all staging databases before the release.\n"
            "- The Memcached layer is the current cache.\n"
            "- Keep the API response under 200ms where possible.\n"
        )
        report = audit(original, summary)
        self.assertEqual(report["original_items"], 6)
        self.assertEqual(report["aligned"], 5)
        self.assertEqual(report["lost"], 1)
        self.assertEqual(report["inflated"], 4)
        self.assertEqual(report["inflation_rate_pct"], 80.0)
        types = sorted(
            r["inflation_type"] for r in report["results"] if r["verdict"] == "INFLATED"
        )
        self.assertEqual(
            types,
            [
                "one-off-to-standing",
                "preference-to-requirement",
                "scope-broadening",
                "stale-value-retained",
            ],
        )

    def test_clean_example(self):
        original = "- Prefer pytest for new tests.\n- Just this once, skip the lint step.\n"
        summary = "- Prefer pytest for new tests.\n- Just this once, skip the lint step.\n"
        report = audit(original, summary)
        self.assertEqual(report["inflated"], 0)
        self.assertEqual(report["lost"], 0)
        self.assertEqual(report["inflation_rate_pct"], 0.0)

    def test_extra_summary_items_reported_not_counted(self):
        original = "- Always lint.\n"
        summary = "- Always lint.\n- Also deploy on Fridays.\n"
        report = audit(original, summary)
        self.assertEqual(report["inflated"], 0)
        self.assertEqual(len(report["extra"]), 1)


if __name__ == "__main__":
    unittest.main()
