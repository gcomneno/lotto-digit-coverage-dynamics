from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from analyze_coverage_hit_statistics import (
    build_parser,
    write_summary_csv,
)
from strategies.coverage_hit_statistics import (
    CoverageHitSummary,
)


class CoverageHitCsvTests(unittest.TestCase):
    def test_parser_accepts_csv_destination(
        self,
    ) -> None:
        arguments = build_parser().parse_args(
            (
                "--csv",
                "reports/coverage.csv",
            )
        )

        self.assertEqual(
            arguments.csv,
            Path("reports/coverage.csv"),
        )

    def test_writes_numeric_summary_csv(
        self,
    ) -> None:
        summary = CoverageHitSummary(
            most_present_count=3,
            missing_count=3,
            mean_completion_within_one=0.2354,
            mean_threshold_probability=0.7231,
            attempts=566,
            obtained=422,
            missed=144,
            hit_digit_count=1108,
        )

        with tempfile.TemporaryDirectory() as temporary:
            destination = (
                Path(temporary)
                / "nested"
                / "coverage.csv"
            )

            write_summary_csv(
                destination,
                (summary,),
            )

            with destination.open(
                encoding="utf-8",
                newline="",
            ) as stream:
                rows = list(
                    csv.DictReader(stream)
                )

        self.assertEqual(len(rows), 1)

        row = rows[0]

        self.assertEqual(row["top"], "3")
        self.assertEqual(row["missing"], "3")
        self.assertEqual(row["threshold"], "2")
        self.assertEqual(row["cases"], "566")
        self.assertEqual(row["obtained"], "422")
        self.assertEqual(row["missed"], "144")
        self.assertAlmostEqual(
            float(row["markov_probability"]),
            0.2354,
        )
        self.assertAlmostEqual(
            float(row["expected_probability"]),
            0.7231,
        )
        self.assertAlmostEqual(
            float(row["success_rate"]),
            422 / 566,
        )
        self.assertAlmostEqual(
            float(row["excess"]),
            (422 / 566) - 0.7231,
        )
        self.assertAlmostEqual(
            float(row["mean_hit_digits"]),
            1108 / 566,
        )


if __name__ == "__main__":
    unittest.main()
