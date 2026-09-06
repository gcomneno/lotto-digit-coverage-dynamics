from __future__ import annotations

import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from lotto_digit_coverage.application.natural_query import (
    DrawHistoryIntent,
    DrawHistoryRow,
    NaturalQueryError,
    execute_draw_history,
)
from lotto_digit_coverage.interfaces.cli.natural_query_command import main as natural_query_main
from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    DEFAULT_PRESENTATION_CATALOG,
    SUPPORTED_LOCALES,
    PresentationCatalog,
)


VALID_INTENT = {
    "operation": "draw_history",
    "wheel": "Napoli",
    "numbers": [18, 81],
    "digits": [],
    "order": "descending",
    "highlight": True,
    "limit": 2,
    "from_draw": None,
    "to_draw": None,
}


class RecordingRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int | None, int | None]] = []

    def load_wheel_history(self, wheel, *, from_draw, to_draw):
        self.calls.append((wheel, from_draw, to_draw))
        return (
            DrawHistoryRow(1, "2026-01-01", (1, 2, 3, 4, 5)),
            DrawHistoryRow(3, "2026-01-03", (6, 7, 8, 9, 10)),
            DrawHistoryRow(2, "2026-01-02", (11, 12, 13, 14, 15)),
        )


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

    def test_locale_resolution_does_not_enter_application_semantics(self):
        intent = DrawHistoryIntent.from_mapping(VALID_INTENT)
        outcomes = []
        repository_calls = []

        for locale in SUPPORTED_LOCALES:
            presentation = DEFAULT_PRESENTATION_CATALOG.resolve(
                "common.error_prefix", locale
            )
            repository = RecordingRepository()
            rows = execute_draw_history(intent, repository)
            outcomes.append(
                (
                    [row.draw_number for row in rows],
                    intent,
                    presentation.requested_locale,
                )
            )
            repository_calls.append(repository.calls)

        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertEqual(outcomes[0][1], outcomes[1][1])
        self.assertEqual(repository_calls[0], repository_calls[1])
        self.assertEqual(repository_calls[0], [("Napoli", None, None)])
        self.assertNotEqual(outcomes[0][2], outcomes[1][2])

    def test_locale_resolution_cannot_change_validation_or_cli_exit_status(self):
        invalid_intent = dict(VALID_INTENT)
        invalid_intent["numbers"] = [91]
        validation_outcomes = []
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

                try:
                    DrawHistoryIntent.from_mapping(invalid_intent)
                except NaturalQueryError as error:
                    validation_outcomes.append((type(error), str(error)))
                else:
                    self.fail("invalid intent unexpectedly passed validation")

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    success_status = natural_query_main(
                        ["--database", str(database), "show Napoli"],
                        backend=FakeBackend(VALID_INTENT),
                    )
                    failure_status = natural_query_main(
                        ["--database", str(database), "invalid request"],
                        backend=FakeBackend(invalid_intent),
                    )
                exit_statuses.append((success_status, failure_status))

        self.assertEqual(validation_outcomes[0], validation_outcomes[1])
        self.assertEqual(exit_statuses, [(0, 1), (0, 1)])


if __name__ == "__main__":
    unittest.main()
