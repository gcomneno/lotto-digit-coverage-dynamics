from __future__ import annotations

import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from lotto_digit_coverage.application.natural_query import (
    DrawHistoryIntent,
    DrawHistoryRow,
    NaturalQueryError,
    execute_draw_history,
)
from lotto_digit_coverage.infrastructure.giadaware_ai_query import (
    INTENT_SCHEMA,
    LottoNaturalQueryCapability,
)
from lotto_digit_coverage.infrastructure.sqlite_draw_history import (
    SqliteDrawHistoryRepository,
)
from lotto_digit_coverage.interfaces.cli.natural_query_command import (
    build_parser,
    main,
)


VALID_INTENT = {
    "operation": "draw_history",
    "wheel": "Napoli",
    "numbers": [18, 81],
    "digits": [],
    "order": "descending",
    "highlight": True,
    "limit": None,
    "from_draw": None,
    "to_draw": None,
}


class FakeBackend:
    def __init__(self, response=None):
        self.response = dict(response or VALID_INTENT)
        self.calls = []

    def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
        self.calls.append((system_prompt, user_prompt, response_schema))
        return self.response


class FakeRepository:
    def load_wheel_history(self, wheel, *, from_draw, to_draw):
        self.call = (wheel, from_draw, to_draw)
        return (
            DrawHistoryRow(1, "2026-01-01", (1, 2, 3, 4, 5)),
            DrawHistoryRow(3, "2026-01-03", (6, 7, 8, 9, 10)),
            DrawHistoryRow(2, "2026-01-02", (11, 12, 13, 14, 15)),
        )


class NaturalQueryContractTests(unittest.TestCase):
    def test_capability_uses_schema_and_validates_result(self):
        backend = FakeBackend()
        intent = LottoNaturalQueryCapability(backend).execute(
            "accendi 18 e 81 su Napoli dalla più recente"
        )

        self.assertEqual(intent.wheel, "Napoli")
        self.assertEqual(intent.numbers, (18, 81))
        self.assertEqual(backend.calls[0][2], INTENT_SCHEMA)

    def test_rejects_extra_model_fields_including_sql(self):
        raw = dict(VALID_INTENT)
        raw["sql"] = "DROP TABLE draws"

        with self.assertRaises(NaturalQueryError):
            DrawHistoryIntent.from_mapping(raw)

    def test_rejects_invalid_ranges_and_numbers(self):
        invalid = dict(VALID_INTENT)
        invalid["numbers"] = [91]
        with self.assertRaises(NaturalQueryError):
            DrawHistoryIntent.from_mapping(invalid)

        invalid = dict(VALID_INTENT)
        invalid["from_draw"] = 20
        invalid["to_draw"] = 10
        with self.assertRaises(NaturalQueryError):
            DrawHistoryIntent.from_mapping(invalid)

    def test_application_service_owns_order_and_limit(self):
        raw = dict(VALID_INTENT)
        raw["limit"] = 2
        intent = DrawHistoryIntent.from_mapping(raw)
        repository = FakeRepository()

        rows = execute_draw_history(intent, repository)

        self.assertEqual([row.draw_number for row in rows], [3, 2])
        self.assertEqual(repository.call, ("Napoli", None, None))


class SqliteDrawHistoryRepositoryTests(unittest.TestCase):
    def test_reads_parameterized_wheel_history_from_read_only_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "lotto.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE v_draw_numbers ("
                    "draw_number INTEGER, draw_date TEXT, wheel TEXT, "
                    "position INTEGER, value INTEGER)"
                )
                for position, value in enumerate((73, 6, 80, 45, 18), 1):
                    connection.execute(
                        "INSERT INTO v_draw_numbers VALUES (?, ?, ?, ?, ?)",
                        (143, "2026-09-05", "Napoli", position, value),
                    )
                for position, value in enumerate((1, 2, 3, 4, 5), 1):
                    connection.execute(
                        "INSERT INTO v_draw_numbers VALUES (?, ?, ?, ?, ?)",
                        (143, "2026-09-05", "Roma", position, value),
                    )

            rows = SqliteDrawHistoryRepository(database).load_wheel_history(
                "Napoli", from_draw=143, to_draw=143
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].numbers, (73, 6, 80, 45, 18))


class NaturalQueryCliIntegrationTests(unittest.TestCase):
    def _database(self, directory: str) -> Path:
        database = Path(directory) / "lotto.sqlite3"
        with sqlite3.connect(database) as connection:
            connection.execute(
                "CREATE TABLE v_draw_numbers ("
                "draw_number INTEGER, draw_date TEXT, wheel TEXT, "
                "position INTEGER, value INTEGER)"
            )
            draws = {
                142: (81, 55, 23, 57, 88),
                143: (73, 6, 80, 45, 18),
            }
            for draw, values in draws.items():
                for position, value in enumerate(values, 1):
                    connection.execute(
                        "INSERT INTO v_draw_numbers VALUES (?, ?, ?, ?, ?)",
                        (draw, f"2026-09-{draw - 138:02d}", "Napoli", position, value),
                    )
        return database

    def test_cli_defaults_to_canonical_english(self):
        args = build_parser().parse_args(["hello"])
        self.assertEqual(args.language, "en")
        self.assertIn("Natural-language request", build_parser().format_help())

    def test_napoli_18_81_request_renders_newest_first(self):
        with tempfile.TemporaryDirectory() as directory:
            database = self._database(directory)
            output = io.StringIO()
            with redirect_stdout(output):
                status = main(
                    [
                        "--database",
                        str(database),
                        "accendi 18 e 81 solo su Napoli, dalla più recente alla più vecchia",
                    ],
                    backend=FakeBackend(),
                )

            rendered = output.getvalue()
            self.assertEqual(status, 0)
            self.assertIn("Wheel: Napoli", rendered)
            self.assertIn("Order: descending", rendered)
            self.assertLess(rendered.index(" 143  "), rendered.index(" 142  "))
            self.assertIn("\033[1;30;46m18\033[0m", rendered)
            self.assertIn("\033[1;30;46m81\033[0m", rendered)

    def test_english_and_italian_change_only_presentation(self):
        with tempfile.TemporaryDirectory() as directory:
            database = self._database(directory)
            outputs = {}
            statuses = {}
            for locale in ("en", "it"):
                output = io.StringIO()
                with redirect_stdout(output):
                    statuses[locale] = main(
                        [
                            "--database",
                            str(database),
                            "--language",
                            locale,
                            "accendi 18 e 81 solo su Napoli, dalla più recente alla più vecchia",
                        ],
                        backend=FakeBackend(),
                    )
                outputs[locale] = output.getvalue()

            self.assertEqual(statuses, {"en": 0, "it": 0})
            self.assertIn("Wheel: Napoli", outputs["en"])
            self.assertIn("Ruota: Napoli", outputs["it"])
            for locale in ("en", "it"):
                rendered = outputs[locale]
                self.assertIn("Order: descending" if locale == "en" else "Ordine: descending", rendered)
                self.assertLess(rendered.index(" 143  "), rendered.index(" 142  "))
                self.assertIn("\033[1;30;46m18\033[0m", rendered)
                self.assertIn("\033[1;30;46m81\033[0m", rendered)


if __name__ == "__main__":
    unittest.main()
