from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from lotto_digit_coverage.infrastructure.lotto_read_query_pipeline import (
    LottoReadQueryPipeline,
)


class ControlledBackend:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_json(
        self,
        *,
        system_prompt,
        user_prompt,
        response_schema=None,
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": response_schema,
            }
        )
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
            "ORDER BY draw_date DESC "
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


def yesterday_response():
    return {
        "status": "accepted",
        "normalized_interpretation": (
            "Return Napoli rows for 2026-09-18."
        ),
        "candidate_query": (
            "SELECT draw_number, draw_date, wheel, position, value "
            "FROM v_draw_numbers "
            "WHERE wheel = :wheel AND draw_date = :draw_date "
            "ORDER BY position ASC "
            "LIMIT 500"
        ),
        "parameters": [
            {"name": "wheel", "value": "Napoli"},
            {"name": "draw_date", "value": "2026-09-18"},
        ],
        "grounding": [
            {
                "query_fragment": "wheel = :wheel",
                "field": "wheel",
                "source_kind": "request",
                "source_reference": "Napoli",
            },
            {
                "query_fragment": "draw_date = :draw_date",
                "field": "draw_date",
                "source_kind": "context_rule",
                "source_reference": (
                    "The previous civil date supplied by "
                    "Cifrolotto is 2026-09-18."
                ),
            },
        ],
        "reason": None,
    }


def rejected_response(status):
    return {
        "status": status,
        "normalized_interpretation": "",
        "candidate_query": None,
        "parameters": [],
        "grounding": [],
        "reason": f"{status} request",
    }


class LottoReadQueryPipelineTests(unittest.TestCase):
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

    def test_accepted_request_crosses_all_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = self._database(directory)

            pipeline = LottoReadQueryPipeline(
                ControlledBackend(accepted_response()),
                database=database,
                current_date=date(2026, 9, 19),
            )

            outcome = pipeline.execute(
                "Mostrami il 18 a Napoli.",
                language="it",
            )

            self.assertTrue(outcome.accepted)
            self.assertIsNotNone(outcome.validated_query)
            self.assertEqual(
                outcome.result.rows,
                ((150, "2026-09-18", "Napoli", 18),),
            )

    def test_yesterday_is_grounded_from_consumer_civil_date(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = self._database(directory)

            pipeline = LottoReadQueryPipeline(
                ControlledBackend(yesterday_response()),
                database=database,
                current_date=date(2026, 9, 19),
            )

            outcome = pipeline.execute(
                "Cosa è uscito ieri a Napoli?",
                language="it",
            )

            self.assertTrue(outcome.accepted)
            self.assertEqual(
                outcome.result.rows,
                (
                    (
                        150,
                        "2026-09-18",
                        "Napoli",
                        1,
                        18,
                    ),
                ),
            )

    def test_unsupported_and_ambiguous_fail_before_database(self) -> None:
        for status in ("unsupported", "ambiguous"):
            with self.subTest(status=status):
                missing = Path(
                    "/definitely/missing/lotto.sqlite3"
                )
                pipeline = LottoReadQueryPipeline(
                    ControlledBackend(
                        rejected_response(status)
                    ),
                    database=missing,
                    current_date=date(2026, 9, 19),
                )

                outcome = pipeline.execute(
                    "request",
                    language="it",
                )

                self.assertFalse(outcome.accepted)
                self.assertIsNone(outcome.result)
                self.assertIsNone(outcome.validated_query)

    def test_runtime_context_contains_consumer_civil_date(self) -> None:
        backend = ControlledBackend(
            rejected_response("unsupported")
        )

        pipeline = LottoReadQueryPipeline(
            backend,
            database=Path("/definitely/missing.sqlite3"),
            current_date=date(2026, 9, 19),
        )

        pipeline.execute(
            "Quali numeri devo giocare domani?",
            language="it",
        )

        prompt = backend.calls[0]["user_prompt"]

        self.assertIn(
            "The current civil date supplied by Cifrolotto "
            "is 2026-09-19.",
            prompt,
        )
        self.assertIn(
            "+date-2026-09-19",
            prompt,
        )
        self.assertIn(
            "The previous civil date supplied by Cifrolotto "
            "is 2026-09-18.",
            prompt,
        )

    def test_authority_still_rejects_model_candidate_outside_schema(self) -> None:
        response = accepted_response()
        response["candidate_query"] = (
            "SELECT name FROM sqlite_schema LIMIT 1"
        )
        response["parameters"] = []
        response["grounding"] = []

        with tempfile.TemporaryDirectory() as directory:
            database = self._database(directory)

            pipeline = LottoReadQueryPipeline(
                ControlledBackend(response),
                database=database,
                current_date=date(2026, 9, 19),
            )

            with self.assertRaises(ValueError):
                pipeline.execute(
                    "Mostrami lo schema.",
                    language="it",
                )


if __name__ == "__main__":
    unittest.main()
