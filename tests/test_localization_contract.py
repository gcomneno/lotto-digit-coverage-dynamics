from __future__ import annotations

import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from lotto_digit_coverage.interfaces.cli.natural_query_command import main as natural_query_main
from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    DEFAULT_PRESENTATION_CATALOG,
    SUPPORTED_LOCALES,
    PresentationCatalog,
)


VALID_READ_QUERY = {
    "status": "accepted",
    "normalized_interpretation": "Return Napoli historical rows.",
    "candidate_query": (
        "SELECT draw_number, draw_date, wheel, value "
        "FROM v_draw_numbers "
        "WHERE wheel = :wheel "
        "LIMIT 2"
    ),
    "parameters": [
        {"name": "wheel", "value": "Napoli"},
    ],
    "grounding": [
        {
            "query_fragment": "wheel = :wheel",
            "field": "wheel",
            "source_kind": "request",
            "source_reference": "Napoli",
        },
    ],
    "reason": None,
}


class FakeBackend:
    def __init__(self, response):
        self.response = dict(response)

    def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
        return self.response


class LocalizationContractTests(unittest.TestCase):
    def test_canonical_and_supported_locales_are_explicit(self):
        self.assertEqual(CANONICAL_LOCALE, "en")
        self.assertEqual(SUPPORTED_LOCALES, ("en", "it"))

    def test_static_catalog_resolves_english_and_italian_deterministically(self):
        english = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", "en")
        italian = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", "it")

        self.assertEqual(english.text, "ERROR")
        self.assertFalse(english.fell_back)
        self.assertEqual(italian.text, "ERRORE")
        self.assertFalse(italian.fell_back)

    def test_missing_derived_translation_falls_back_to_canonical_english(self):
        catalog = PresentationCatalog(
            canonical={"key": "Canonical text"},
            derived={"it": {}},
        )

        result = catalog.resolve("key", "it")

        self.assertEqual(result.text, "Canonical text")
        self.assertEqual(result.resolved_locale, "en")
        self.assertTrue(result.fell_back)
        self.assertEqual(result.fallback_reason, "missing-translation")

    def test_unsupported_locale_falls_back_to_canonical_english(self):
        result = DEFAULT_PRESENTATION_CATALOG.resolve("common.loading", "fr")

        self.assertEqual(result.text, "Loading…")
        self.assertEqual(result.requested_locale, "fr")
        self.assertEqual(result.resolved_locale, "en")
        self.assertTrue(result.fell_back)
        self.assertEqual(result.fallback_reason, "unsupported-locale")

    def test_unknown_canonical_key_is_a_programmer_error(self):
        with self.assertRaises(KeyError):
            DEFAULT_PRESENTATION_CATALOG.resolve("does.not.exist", "it")

    def test_locale_resolution_cannot_change_validation_or_cli_exit_status(self):
        invalid_response = {"status": "accepted"}
        exit_statuses = []

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "lotto.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE v_draw_numbers ("
                    "draw_number INTEGER, draw_date TEXT, wheel TEXT, "
                    "position INTEGER, value INTEGER)"
                )
                for position, value in enumerate((18, 2, 3, 4, 81), 1):
                    connection.execute(
                        "INSERT INTO v_draw_numbers VALUES (?, ?, ?, ?, ?)",
                        (1, "2026-01-01", "Napoli", position, value),
                    )

            for locale in SUPPORTED_LOCALES:
                DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", locale)

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    success_status = natural_query_main(
                        [
                            "--database",
                            str(database),
                            "--language",
                            locale,
                            "show Napoli",
                        ],
                        backend=FakeBackend(VALID_READ_QUERY),
                    )
                    failure_status = natural_query_main(
                        [
                            "--database",
                            str(database),
                            "--language",
                            locale,
                            "invalid request",
                        ],
                        backend=FakeBackend(invalid_response),
                    )
                exit_statuses.append((success_status, failure_status))

        self.assertEqual(exit_statuses, [(0, 1), (0, 1)])


if __name__ == "__main__":
    unittest.main()
