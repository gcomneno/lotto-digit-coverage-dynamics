from __future__ import annotations

import io
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

from lotto_digit_coverage.interfaces.cli.natural_query_command import (
    build_parser,
    main,
)


class ControlledBackend:
    def __init__(self, response):
        self.response = response

    def generate_json(
        self,
        *,
        system_prompt,
        user_prompt,
        response_schema=None,
    ):
        return self.response


def accepted_response():
    return {
        "status": "accepted",
        "normalized_interpretation": (
            "Return Napoli rows containing number 18."
        ),
        "candidate_query": (
            "SELECT draw_number, draw_date, wheel, value "
            "FROM v_draw_numbers "
            "WHERE wheel = :wheel AND value = :value "
            "LIMIT 500"
        ),
        "parameters": [
            {"name": "wheel", "value": "Napoli"},
            {"name": "value", "value": 18},
        ],
        "grounding": [
            {
                "query_fragment": "wheel = :wheel",
                "field": "wheel",
                "source_kind": "request",
                "source_reference": "Napoli",
            },
            {
                "query_fragment": "value = :value",
                "field": "value",
                "source_kind": "request",
                "source_reference": "18",
            },
        ],
        "reason": None,
    }


class DbAskCliTests(unittest.TestCase):
    def _database(self, directory: str) -> Path:
        database = Path(directory) / "lotto.sqlite3"

        with sqlite3.connect(database) as connection:
            connection.execute(
                """
                CREATE TABLE v_draw_numbers (
                    draw_number INTEGER,
                    draw_date TEXT,
                    wheel TEXT,
                    wheel_order INTEGER,
                    position INTEGER,
                    value INTEGER
                )
                """
            )
            connection.execute(
                """
                INSERT INTO v_draw_numbers
                VALUES (150, '2026-09-18', 'Napoli', 6, 1, 18)
                """
            )

        return database

    def test_db_ask_defaults_to_italian_only(self) -> None:
        args = build_parser().parse_args(["ciao"])
        self.assertEqual(args.language, "it")

    def test_default_italian_and_explicit_english_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = self._database(directory)

            italian = io.StringIO()
            with redirect_stdout(italian):
                status_it = main(
                    [
                        "--database",
                        str(database),
                        "Mostrami il 18 a Napoli.",
                    ],
                    backend=ControlledBackend(
                        accepted_response()
                    ),
                    current_date=date(2026, 9, 19),
                )

            english = io.StringIO()
            with redirect_stdout(english):
                status_en = main(
                    [
                        "--database",
                        str(database),
                        "--language",
                        "en",
                        "Mostrami il 18 a Napoli.",
                    ],
                    backend=ControlledBackend(
                        accepted_response()
                    ),
                    current_date=date(2026, 9, 19),
                )

            self.assertEqual(status_it, 0)
            self.assertEqual(status_en, 0)

            self.assertIn(
                "Interpretazione normalizzata:",
                italian.getvalue(),
            )
            self.assertIn(
                "Query validata:",
                italian.getvalue(),
            )
            self.assertIn(
                "Normalized interpretation:",
                english.getvalue(),
            )
            self.assertIn(
                "Validated query:",
                english.getvalue(),
            )

    def test_unsupported_is_not_reported_as_success(self) -> None:
        response = {
            "status": "unsupported",
            "normalized_interpretation": "",
            "candidate_query": None,
            "parameters": [],
            "grounding": [],
            "reason": "Predictive request.",
        }

        error = io.StringIO()

        with redirect_stderr(error):
            status = main(
                ["Quali numeri devo giocare domani?"],
                backend=ControlledBackend(response),
                current_date=date(2026, 9, 19),
            )

        self.assertEqual(status, 2)
        self.assertIn("Stato: unsupported", error.getvalue())
        self.assertIn("Motivo:", error.getvalue())

    def test_top_level_discovery_exposes_db_ask(self) -> None:
        listed = subprocess.run(
            [sys.executable, "lotto.py", "list"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(listed.returncode, 0)
        self.assertIn("db ask", listed.stdout)

        db_help = subprocess.run(
            [sys.executable, "lotto.py", "help", "db"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(db_help.returncode, 0)
        self.assertIn("db ask", db_help.stdout)

        nested_help = subprocess.run(
            [sys.executable, "lotto.py", "help", "db", "ask"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(nested_help.returncode, 0)
        self.assertIn("lotto.py db ask", nested_help.stdout)

        direct_help = subprocess.run(
            [sys.executable, "lotto.py", "db", "ask", "--help"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(direct_help.returncode, 0)
        self.assertIn("lotto.py db ask", direct_help.stdout)


if __name__ == "__main__":
    unittest.main()
