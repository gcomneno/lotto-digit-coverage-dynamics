from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from analyze_coverage_hit_statistics import (
    build_parser,
    format_sort_specification,
    resolve_sort_specification,
    sort_summaries,
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
        self.assertEqual(
            row["evidence_level"],
            "strong",
        )


def make_summary(
    *,
    top: int,
    missing: int,
    attempts: int,
    obtained: int,
) -> CoverageHitSummary:
    return CoverageHitSummary(
        most_present_count=top,
        missing_count=missing,
        mean_completion_within_one=0.25,
        mean_threshold_probability=0.50,
        attempts=attempts,
        obtained=obtained,
        missed=attempts - obtained,
        hit_digit_count=obtained,
    )


class CoverageHitSortTests(unittest.TestCase):
    def test_parser_accepts_sort_specifications(
        self,
    ) -> None:
        descending = build_parser().parse_args(
            ("--sort=-cases",)
        )
        mixed = build_parser().parse_args(
            ("--sort=missing,-success_rate",)
        )

        self.assertEqual(
            descending.sort,
            "-cases",
        )
        self.assertEqual(
            mixed.sort,
            "missing,-success_rate",
        )

    def test_sorts_by_multiple_columns_with_directions(
        self,
    ) -> None:
        summaries = (
            make_summary(
                top=1,
                missing=2,
                attempts=10,
                obtained=5,
            ),
            make_summary(
                top=2,
                missing=1,
                attempts=10,
                obtained=5,
            ),
            make_summary(
                top=3,
                missing=1,
                attempts=10,
                obtained=9,
            ),
        )

        result = sort_summaries(
            summaries,
            "missing,-success_rate",
        )

        self.assertEqual(
            [
                summary.most_present_count
                for summary in result
            ],
            [3, 2, 1],
        )

    def test_evidence_uses_sample_size_order(
        self,
    ) -> None:
        summaries = tuple(
            make_summary(
                top=index,
                missing=1,
                attempts=attempts,
                obtained=attempts,
            )
            for index, attempts in enumerate(
                (9, 10, 30, 100, 500),
                start=1,
            )
        )

        result = sort_summaries(
            summaries,
            "-evidence",
        )

        self.assertEqual(
            [
                summary.attempts
                for summary in result
            ],
            [500, 100, 30, 10, 9],
        )

    def test_rejects_empty_sort_specification(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "non può essere vuota",
        ):
            resolve_sort_specification(" , ")

    def test_rejects_unknown_sort_column(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "sconosciuta: banana",
        ):
            resolve_sort_specification(
                "missing,-banana"
            )

    def test_formats_active_sort_order(
        self,
    ) -> None:
        self.assertEqual(
            format_sort_specification(
                "missing,-success_rate"
            ),
            "Manc. ↑, Successo ↓",
        )

    def test_csv_preserves_sorted_order(
        self,
    ) -> None:
        summaries = sort_summaries(
            (
                make_summary(
                    top=1,
                    missing=1,
                    attempts=10,
                    obtained=5,
                ),
                make_summary(
                    top=2,
                    missing=1,
                    attempts=20,
                    obtained=10,
                ),
            ),
            "-cases",
        )

        with tempfile.TemporaryDirectory() as temporary:
            destination = (
                Path(temporary)
                / "coverage.csv"
            )

            write_summary_csv(
                destination,
                summaries,
            )

            with destination.open(
                encoding="utf-8",
                newline="",
            ) as stream:
                rows = list(
                    csv.DictReader(stream)
                )

        self.assertEqual(
            [
                row["cases"]
                for row in rows
            ],
            ["20", "10"],
        )


if __name__ == "__main__":
    unittest.main()
