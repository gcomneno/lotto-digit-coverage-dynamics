from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from generate_state_atlas import (
    ALL_DIGITS_MASK,
    build_atlas,
    render_summary,
    write_outputs,
)


class GenerateStateAtlasTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_atlas()

    def test_contains_all_non_empty_states(
        self,
    ) -> None:
        self.assertEqual(
            len(self.rows),
            1023,
        )

        masks = {
            row.state_mask
            for row in self.rows
        }

        self.assertEqual(
            masks,
            set(
                range(
                    1,
                    ALL_DIGITS_MASK + 1,
                )
            ),
        )

    def test_ranking_is_contiguous_and_monotone(
        self,
    ) -> None:
        self.assertEqual(
            [
                row.difficulty_rank
                for row in self.rows
            ],
            list(range(1, 1024)),
        )

        expected = [
            row.expected_remaining_draws
            for row in self.rows
        ]

        self.assertEqual(
            expected,
            sorted(expected),
        )

    def test_completion_probabilities_are_monotone(
        self,
    ) -> None:
        for row in self.rows:
            values = [
                row.completion_probability_within_1,
                row.completion_probability_within_2,
                row.completion_probability_within_3,
                row.completion_probability_within_5,
                row.completion_probability_within_10,
            ]

            self.assertEqual(
                values,
                sorted(values),
                msg=row.state,
            )

    def test_quantiles_are_ordered(
        self,
    ) -> None:
        for row in self.rows:
            quantiles = [
                row.quantile_50_draws,
                row.quantile_90_draws,
                row.quantile_95_draws,
                row.quantile_99_draws,
            ]

            self.assertEqual(
                quantiles,
                sorted(quantiles),
                msg=row.state,
            )

    def test_expected_time_is_monotone_by_inclusion(
        self,
    ) -> None:
        by_mask = {
            row.state_mask: row
            for row in self.rows
        }

        for row in self.rows:
            for digit in range(10):
                bit = 1 << digit

                if row.state_mask & bit:
                    continue

                superset = by_mask[
                    row.state_mask | bit
                ]

                self.assertLessEqual(
                    row.expected_remaining_draws,
                    (
                        superset
                        .expected_remaining_draws
                        + 1e-12
                    ),
                    msg=(
                        f"{row.state} -> "
                        f"{superset.state}"
                    ),
                )

    def test_outputs_are_deterministic_and_valid(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            csv_path = root / "atlas.csv"
            json_path = root / "atlas.json"
            summary_path = root / "summary.md"

            write_outputs(
                self.rows,
                csv_output=csv_path,
                json_output=json_path,
                summary_output=summary_path,
            )

            first_bytes = {
                "csv": csv_path.read_bytes(),
                "json": json_path.read_bytes(),
                "summary": summary_path.read_bytes(),
            }

            write_outputs(
                self.rows,
                csv_output=csv_path,
                json_output=json_path,
                summary_output=summary_path,
            )

            self.assertEqual(
                csv_path.read_bytes(),
                first_bytes["csv"],
            )
            self.assertEqual(
                json_path.read_bytes(),
                first_bytes["json"],
            )
            self.assertEqual(
                summary_path.read_bytes(),
                first_bytes["summary"],
            )

            with csv_path.open(
                encoding="utf-8",
                newline="",
            ) as stream:
                csv_rows = list(
                    csv.DictReader(stream)
                )

            self.assertEqual(
                len(csv_rows),
                1023,
            )

            document = json.loads(
                json_path.read_text()
            )

            self.assertEqual(
                document["state_space"][
                    "non_empty_states"
                ],
                1023,
            )
            self.assertEqual(
                len(document["rows"]),
                1023,
            )

            summary = render_summary(
                self.rows
            )

            self.assertIn(
                "not a betting recommendation",
                summary,
            )
            self.assertIn(
                "Ten easiest states",
                summary,
            )
            self.assertIn(
                "Ten hardest states",
                summary,
            )


if __name__ == "__main__":
    unittest.main()
