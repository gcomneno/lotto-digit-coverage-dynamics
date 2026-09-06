from __future__ import annotations

import unittest

import view_lotto_database as legacy
from lotto_digit_coverage.interfaces.cli.database_command import _extract_language


class DatabaseLanguageSelectionTests(unittest.TestCase):
    def test_default_language_is_canonical_english(self) -> None:
        arguments, locale = _extract_language(("--latest-occurrences",))
        self.assertEqual(arguments, ["--latest-occurrences"])
        self.assertEqual(locale, "en")

    def test_explicit_italian_is_removed_from_legacy_arguments(self) -> None:
        arguments, locale = _extract_language(
            ("--latest-occurrences", "--language", "it")
        )
        self.assertEqual(arguments, ["--latest-occurrences"])
        self.assertEqual(locale, "it")

    def test_duplicate_language_is_rejected_even_when_first_is_english(self) -> None:
        with self.assertRaisesRegex(legacy.CliError, "specified only once"):
            _extract_language(("--language", "en", "--language", "it"))

    def test_invalid_language_is_same_validation_class(self) -> None:
        with self.assertRaises(legacy.CliError):
            _extract_language(("--language", "fr"))


if __name__ == "__main__":
    unittest.main()
