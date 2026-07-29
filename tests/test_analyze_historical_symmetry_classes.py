from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analyze_historical_symmetry_classes import (
    build_class_observations,
    build_empirical_rows,
    validate_rows,
    write_csv,
    write_json,
)
from strategies.coverage_completion import (
    ALL_DIGITS,
    exact_completion_probability,
)
from strategies.lotto_repository import (
    DrawSnapshot,
)


def draw(
    number: int,
    date: str,
    numbers: tuple[int, ...],
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=date,
        wheel="Bari",
        wheel_order=1,
        numbers=numbers,
    )


SYNCHRONIZING_DRAW = (
    12,
    34,
    56,
    78,
    90,
)


class HistoricalSymmetryClassTests(
    unittest.TestCase
):
    def test_skips_initial_left_censored_segment(
        self,
    ) -> None:
        observations = build_class_observations(
            (
                draw(
                    1,
                    "2023-01-01",
                    (11, 22, 33, 44, 55),
                ),
                draw(
                    2,
                    "2023-01-02",
                    SYNCHRONIZING_DRAW,
                ),
                draw(
                    3,
                    "2023-01-03",
                    (11, 22, 33, 44, 55),
                ),
            )
        )

        self.assertEqual(
            len(observations),
            1,
        )

        self.assertEqual(
            observations[0].target_draw,
            3,
        )

    def test_records_pre_draw_state_and_completion(
        self,
    ) -> None:
        observations = build_class_observations(
            (
                draw(
                    1,
                    "2023-01-01",
                    SYNCHRONIZING_DRAW,
                ),
                draw(
                    2,
                    "2023-01-02",
                    (11, 22, 33, 44, 55),
                ),
                draw(
                    3,
                    "2023-01-03",
                    (60, 67, 78, 89, 90),
                ),
            )
        )

        self.assertEqual(
            len(observations),
            2,
        )

        first, second = observations

        self.assertEqual(
            first.missing_digits,
            tuple(range(10)),
        )

        self.assertEqual(
            first.class_id,
            "zero-nine:8",
        )

        self.assertFalse(
            first.completed_next
        )

        self.assertEqual(
            second.missing_digits,
            (0, 6, 7, 8, 9),
        )

        self.assertEqual(
            second.class_id,
            "zero-nine:3",
        )

        self.assertTrue(
            second.completed_next
        )

    def test_aggregation_contains_all_classes(
        self,
    ) -> None:
        observations = build_class_observations(
            (
                draw(
                    1,
                    "2023-01-01",
                    SYNCHRONIZING_DRAW,
                ),
                draw(
                    2,
                    "2023-01-02",
                    SYNCHRONIZING_DRAW,
                ),
            )
        )

        rows = build_empirical_rows(
            observations
        )

        validate_rows(
            rows,
            observations,
        )

        self.assertEqual(len(rows), 27)

        self.assertEqual(
            sum(
                row.observations
                for row in rows
            ),
            1,
        )

        full = next(
            row
            for row in rows
            if row.class_id
            == "zero-nine:8"
        )

        self.assertEqual(
            full.observations,
            1,
        )

        self.assertEqual(
            full.observed_completions,
            1,
        )

        self.assertEqual(
            full.observed_frequency,
            1.0,
        )

    def test_theoretical_probability_is_exact(
        self,
    ) -> None:
        rows = build_empirical_rows(())

        full = next(
            row
            for row in rows
            if row.class_id
            == "zero-nine:8"
        )

        self.assertAlmostEqual(
            full.theoretical_probability,
            exact_completion_probability(
                ALL_DIGITS
            ),
            places=15,
        )

    def test_outputs_are_local_and_lf_only(
        self,
    ) -> None:
        rows = build_empirical_rows(())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "table.csv"
            json_path = root / "table.json"

            write_csv(
                rows,
                csv_path,
            )

            write_json(
                rows,
                (),
                (Path("archive.sqlite3"),),
                json_path,
            )

            csv_content = csv_path.read_bytes()

            self.assertNotIn(
                b"\r",
                csv_content,
            )

            document = json.loads(
                json_path.read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                document["class_count"],
                27,
            )

            self.assertEqual(
                document["observation_count"],
                0,
            )


if __name__ == "__main__":
    unittest.main()
