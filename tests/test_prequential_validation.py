from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from strategies.coverage_completion import (
    CurrentCoverageState,
)
from strategies.prequential_validation import (
    build_forecast_document,
    default_forecast_path,
    document_sha256,
    normalize_horizons,
    write_forecast_document,
)


def state(
    wheel: str = "Bari",
    wheel_order: int = 1,
    *,
    latest_draw: int = 119,
    latest_date: str = "2026-07-26",
    synchronized: bool = True,
) -> CurrentCoverageState:
    return CurrentCoverageState(
        wheel=wheel,
        wheel_order=wheel_order,
        latest_draw=latest_draw,
        latest_date=latest_date,
        completed_cycles=10,
        draws_in_cycle=2,
        covered_digits=frozenset(
            {0, 1, 2, 3, 4, 5, 6, 7, 8}
        ),
        missing_digits=frozenset({9}),
        synchronized=synchronized,
    )


class PrequentialValidationTests(unittest.TestCase):
    def test_default_path_uses_padded_target(self) -> None:
        self.assertEqual(
            default_forecast_path(120),
            Path(
                "prequential/forecasts/draw-0120.json"
            ),
        )

    def test_normalizes_horizons(self) -> None:
        self.assertEqual(
            normalize_horizons((3, 1, 3, 2)),
            (1, 2, 3),
        )

    def test_builds_next_draw_forecast(self) -> None:
        document = build_forecast_document(
            (state(),),
            database_path=Path("data/test.sqlite3"),
            database_sha256="abc",
            repository_commit="deadbeef",
            generated_at_utc="2026-07-27T12:00:00Z",
        )

        self.assertEqual(
            document["source_latest_draw"],
            119,
        )
        self.assertEqual(
            document["target_draw"],
            120,
        )
        self.assertEqual(
            document["status"],
            "pending",
        )
        self.assertEqual(
            document["wheel_count"],
            1,
        )

    def test_forecast_contains_markov_metrics(self) -> None:
        document = build_forecast_document(
            (state(),),
            database_path=Path("data/test.sqlite3"),
            database_sha256="abc",
            repository_commit="deadbeef",
            generated_at_utc="2026-07-27T12:00:00Z",
        )

        wheel = document["wheels"][0]

        self.assertEqual(
            wheel["missing_digits"],
            [9],
        )
        self.assertAlmostEqual(
            wheel["completion_probability_within"]["1"],
            0.453,
            places=3,
        )
        self.assertGreater(
            wheel["expected_remaining_draws"],
            2.0,
        )

    def test_rejects_unsynchronized_state(self) -> None:
        with self.assertRaises(ValueError):
            build_forecast_document(
                (state(synchronized=False),),
                database_path=Path("data/test.sqlite3"),
                database_sha256="abc",
                repository_commit="deadbeef",
                generated_at_utc="2026-07-27T12:00:00Z",
            )

    def test_rejects_misaligned_draws(self) -> None:
        with self.assertRaises(ValueError):
            build_forecast_document(
                (
                    state("Bari", 1, latest_draw=119),
                    state("Roma", 2, latest_draw=118),
                ),
                database_path=Path("data/test.sqlite3"),
                database_sha256="abc",
                repository_commit="deadbeef",
                generated_at_utc="2026-07-27T12:00:00Z",
            )

    def test_write_is_immutable(self) -> None:
        document = build_forecast_document(
            (state(),),
            database_path=Path("data/test.sqlite3"),
            database_sha256="abc",
            repository_commit="deadbeef",
            generated_at_utc="2026-07-27T12:00:00Z",
        )

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "forecast.json"

            first_hash = write_forecast_document(
                document,
                path,
            )

            self.assertEqual(
                first_hash,
                document_sha256(document),
            )

            with self.assertRaises(FileExistsError):
                write_forecast_document(
                    document,
                    path,
                )

    def test_document_hash_is_deterministic(self) -> None:
        document = build_forecast_document(
            (state(),),
            database_path=Path("data/test.sqlite3"),
            database_sha256="abc",
            repository_commit="deadbeef",
            generated_at_utc="2026-07-27T12:00:00Z",
        )

        self.assertEqual(
            document_sha256(document),
            document_sha256(document),
        )


if __name__ == "__main__":
    unittest.main()
