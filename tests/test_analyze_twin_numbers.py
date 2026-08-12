from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from analyze_twin_numbers import (
    build_parser,
    filter_observations,
    render_rows,
    write_json,
)
from strategies.twin_numbers import TwinObservation, TwinStatisticsRow


class AnalyzeTwinNumbersTests(unittest.TestCase):
    def test_parser_accepts_gemelli_filters(self) -> None:
        args = build_parser().parse_args(
            [
                "--wheel",
                "Milano",
                "--from-date",
                "2020-01-01",
                "--to-date",
                "2025-12-31",
            ]
        )

        self.assertEqual(args.wheel, ["Milano"])
        self.assertEqual(args.from_date, "2020-01-01")
        self.assertEqual(args.to_date, "2025-12-31")

    def test_filter_is_case_insensitive_and_date_inclusive(self) -> None:
        observations = (
            TwinObservation(
                wheel="Milano",
                wheel_order=1,
                target_draw=1,
                target_date="2025-01-01",
                digit=6,
                twin_number=66,
                conditions=("baseline", "missing"),
                hit=False,
            ),
            TwinObservation(
                wheel="Roma",
                wheel_order=2,
                target_draw=2,
                target_date="2025-01-02",
                digit=6,
                twin_number=66,
                conditions=("baseline",),
                hit=True,
            ),
        )

        selected = filter_observations(
            observations,
            wheels=("MILANO",),
            from_date="2025-01-01",
            to_date="2025-01-01",
        )

        self.assertEqual(selected, (observations[0],))

    def test_render_does_not_promote_non_candidate(self) -> None:
        row = TwinStatisticsRow(
            condition="missing",
            digit=6,
            twin_number=66,
            cases=300,
            hits=17,
            expected_hits=300 / 18,
            null_probability=1 / 18,
            observed_probability=17 / 300,
            lift_probability=17 / 300 - 1 / 18,
            wilson_low=0.03,
            wilson_high=0.09,
            p_value=0.9,
            q_value=0.9,
            candidate=False,
        )

        rendered = render_rows((row,))

        self.assertIn("66", rendered)
        self.assertNotIn("CANDIDATO", rendered)

    def test_json_records_exploratory_interpretation(self) -> None:
        observation = TwinObservation(
            wheel="Milano",
            wheel_order=1,
            target_draw=1,
            target_date="2025-01-01",
            digit=6,
            twin_number=66,
            conditions=("baseline",),
            hit=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            write_json(
                (),
                (observation,),
                database=Path("archive.sqlite3"),
                wheels=(),
                from_date=None,
                to_date=None,
                output=output,
            )
            rendered = output.read_text(encoding="utf-8")

        self.assertIn("Exploratory screen only", rendered)
        self.assertIn("not a validated predictive trigger", rendered)


if __name__ == "__main__":
    unittest.main()
