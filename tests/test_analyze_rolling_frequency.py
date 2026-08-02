from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analyze_rolling_frequency import (
    DEFAULT_CSV_OUTPUT,
    DEFAULT_DATABASES,
    DEFAULT_JSON_OUTPUT,
    DEFAULT_PERIODS,
    DEFAULT_REPETITIONS,
    DEFAULT_SEED,
    DEFAULT_WINDOW_SIZES,
    build_parser,
    build_result_rows,
    render_table,
    write_csv,
    write_json,
)
from strategies.rolling_frequency import (
    WalkForwardObservation,
)


def observation(
    *,
    target_draw: int,
    target_date: str,
    candidate_numbers: tuple[int, ...],
    hit_numbers: tuple[int, ...],
    ambo_hits: tuple[tuple[int, int], ...],
    window_size: int = 6,
) -> WalkForwardObservation:
    return WalkForwardObservation(
        wheel="Bari",
        wheel_order=1,
        window_size=window_size,
        history_draw_numbers=tuple(
            range(
                target_draw - window_size,
                target_draw,
            )
        ),
        history_start_draw=target_draw - window_size,
        history_end_draw=target_draw - 1,
        target_draw=target_draw,
        target_date=target_date,
        target_numbers=(
            11,
            22,
            33,
            44,
            55,
        ),
        most_frequent_digits=frozenset({1}),
        missing_digits=frozenset({0, 6}),
        candidate_numbers=candidate_numbers,
        hit_numbers=hit_numbers,
        ambo_hits=ambo_hits,
        covered_ambo_count=(
            len(candidate_numbers)
            * (len(candidate_numbers) - 1)
            // 2
        ),
        hit_ambo_count=len(ambo_hits),
    )


class RollingFrequencyCliTests(unittest.TestCase):
    def test_parser_has_reproducible_defaults(
        self,
    ) -> None:
        args = build_parser().parse_args([])

        self.assertIsNone(args.databases)
        self.assertIsNone(args.window_sizes)
        self.assertEqual(
            DEFAULT_DATABASES,
            (
                Path("data/lotto-2023.sqlite3"),
                Path("data/lotto-2024.sqlite3"),
                Path("data/lotto-2025.sqlite3"),
                Path("data/lotto-current.sqlite3"),
            ),
        )
        self.assertEqual(
            DEFAULT_WINDOW_SIZES,
            (3, 6, 8, 12),
        )
        self.assertEqual(
            args.repetitions,
            DEFAULT_REPETITIONS,
        )
        self.assertEqual(
            args.seed,
            DEFAULT_SEED,
        )
        self.assertEqual(
            args.csv_output,
            DEFAULT_CSV_OUTPUT,
        )
        self.assertEqual(
            args.json_output,
            DEFAULT_JSON_OUTPUT,
        )

    def test_builds_deterministic_period_rows(
        self,
    ) -> None:
        experiment = {
            6: (
                observation(
                    target_draw=100,
                    target_date="2025-12-30",
                    candidate_numbers=(
                        11,
                        16,
                        61,
                        66,
                    ),
                    hit_numbers=(11, 61),
                    ambo_hits=((11, 61),),
                ),
                observation(
                    target_draw=1,
                    target_date="2026-01-02",
                    candidate_numbers=(
                        44,
                        47,
                        74,
                        77,
                    ),
                    hit_numbers=(44,),
                    ambo_hits=(),
                ),
            ),
        }

        first = build_result_rows(
            experiment,
            window_sizes=(6,),
            periods=DEFAULT_PERIODS,
            repetitions=10,
            base_seed=123,
        )
        second = build_result_rows(
            experiment,
            window_sizes=(6,),
            periods=DEFAULT_PERIODS,
            repetitions=10,
            base_seed=123,
        )

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(row.period for row in first),
            (
                "development",
                "held-out",
            ),
        )
        self.assertEqual(
            tuple(row.seed for row in first),
            (723, 724),
        )
        self.assertEqual(
            first[0].observed_hit_ambo_count,
            1,
        )
        self.assertEqual(
            first[1].observed_hit_ambo_count,
            0,
        )
        self.assertEqual(
            first[0].observation_count,
            1,
        )
        self.assertEqual(
            first[1].observation_count,
            1,
        )

    def test_outputs_are_deterministic_and_lf_only(
        self,
    ) -> None:
        rows = build_result_rows(
            {
                6: (
                    observation(
                        target_draw=100,
                        target_date="2025-12-30",
                        candidate_numbers=(
                            11,
                            16,
                            61,
                            66,
                        ),
                        hit_numbers=(11, 61),
                        ambo_hits=((11, 61),),
                    ),
                ),
            },
            window_sizes=(6,),
            periods=DEFAULT_PERIODS,
            repetitions=10,
            base_seed=123,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_csv = root / "first.csv"
            second_csv = root / "second.csv"
            first_json = root / "first.json"
            second_json = root / "second.json"

            for csv_path, json_path in (
                (first_csv, first_json),
                (second_csv, second_json),
            ):
                write_csv(
                    rows,
                    csv_path,
                )
                write_json(
                    rows,
                    databases=(
                        Path("data/lotto-2025.sqlite3"),
                    ),
                    repetitions=10,
                    base_seed=123,
                    output=json_path,
                )

            self.assertEqual(
                first_csv.read_bytes(),
                second_csv.read_bytes(),
            )
            self.assertEqual(
                first_json.read_bytes(),
                second_json.read_bytes(),
            )
            self.assertNotIn(
                b"\r",
                first_csv.read_bytes(),
            )

            document = json.loads(
                first_json.read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                document["row_count"],
                2,
            )
            self.assertEqual(
                document["repetitions"],
                10,
            )
            self.assertEqual(
                document["base_seed"],
                123,
            )
            self.assertEqual(
                document["database_paths"],
                [
                    "data/lotto-2025.sqlite3",
                ],
            )

    def test_render_table_exposes_random_comparison(
        self,
    ) -> None:
        rows = build_result_rows(
            {
                6: (
                    observation(
                        target_draw=100,
                        target_date="2025-12-30",
                        candidate_numbers=(
                            11,
                            16,
                            61,
                            66,
                        ),
                        hit_numbers=(11, 61),
                        ambo_hits=((11, 61),),
                    ),
                ),
            },
            window_sizes=(6,),
            periods=DEFAULT_PERIODS,
            repetitions=10,
            base_seed=123,
        )

        rendered = render_table(rows)

        self.assertIn(
            "N",
            rendered,
        )
        self.assertIn(
            "Periodo",
            rendered,
        )
        self.assertIn(
            "development",
            rendered,
        )
        self.assertIn(
            "held-out",
            rendered,
        )
        self.assertIn(
            "p ambo",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
