from __future__ import annotations

import unittest
from unittest.mock import patch

from lotto_digit_coverage.application.historical_signals import (
    build_coverage_hit_report,
    build_digit_coverage_report,
    build_digit_return_report,
)
from strategies.coverage_hit_statistics import CoverageHitObservation
from strategies.digit_coverage import DigitCoverageWindow
from strategies.digit_return_times import DigitReturnObservation


class HistoricalSignalsApplicationTests(unittest.TestCase):
    def test_coverage_hit_report_preserves_selected_target_order_and_summary(self) -> None:
        observations = (
            CoverageHitObservation(
                wheel="Bari",
                wheel_order=1,
                history_draw=10,
                history_date="2026-01-10",
                target_draw=11,
                target_date="2026-01-11",
                draws_in_cycle=2,
                most_present_digits=frozenset({1}),
                missing_digits=frozenset({8, 9}),
                target_digits=frozenset({8}),
                hit_digits=frozenset({8}),
                completion_within_one=0.40,
                threshold_probability=0.84,
            ),
            CoverageHitObservation(
                wheel="Roma",
                wheel_order=8,
                history_draw=11,
                history_date="2026-01-11",
                target_draw=12,
                target_date="2026-01-12",
                draws_in_cycle=3,
                most_present_digits=frozenset({2, 3}),
                missing_digits=frozenset({7}),
                target_digits=frozenset({7}),
                hit_digits=frozenset({7}),
                completion_within_one=0.68,
                threshold_probability=0.68,
            ),
        )

        with patch(
            "lotto_digit_coverage.application.historical_signals.load_draws_by_wheel",
            return_value={"Bari": ()},
        ), patch(
            "lotto_digit_coverage.application.historical_signals.build_coverage_hit_experiment",
            return_value=observations,
        ), patch(
            "lotto_digit_coverage.application.historical_signals.select_latest_targets",
            return_value=observations,
        ) as select_targets:
            report = build_coverage_hit_report(object(), target_count=2)

        select_targets.assert_called_once_with(observations, target_count=2)
        self.assertEqual(report.observations, observations)
        self.assertEqual(
            report.target_keys,
            (("2026-01-11", 11), ("2026-01-12", 12)),
        )
        self.assertEqual(sum(summary.attempts for summary in report.summaries), 2)

    def test_return_report_builds_hazards_digits_and_long_absences(self) -> None:
        observations = (
            DigitReturnObservation(
                wheel="Bari",
                wheel_order=1,
                digit=4,
                position="any",
                absence_streak=5,
                target_draw=20,
                target_date="2026-02-01",
                hit=True,
            ),
            DigitReturnObservation(
                wheel="Bari",
                wheel_order=1,
                digit=4,
                position="any",
                absence_streak=9,
                target_draw=21,
                target_date="2026-02-02",
                hit=False,
            ),
            DigitReturnObservation(
                wheel="Bari",
                wheel_order=1,
                digit=4,
                position="tens",
                absence_streak=2,
                target_draw=20,
                target_date="2026-02-01",
                hit=False,
            ),
            DigitReturnObservation(
                wheel="Bari",
                wheel_order=1,
                digit=4,
                position="units",
                absence_streak=1,
                target_draw=20,
                target_date="2026-02-01",
                hit=True,
            ),
        )

        with patch(
            "lotto_digit_coverage.application.historical_signals.collect_return_observations",
            return_value=observations,
        ):
            report = build_digit_return_report(object())

        self.assertEqual(
            [table.position for table in report.hazard_tables],
            ["any", "tens", "units"],
        )
        any_table = report.hazard_tables[0]
        self.assertEqual([group.key for group in any_table.groups], ["5", "9+"])
        digit_four = report.any_position_by_digit[4]
        self.assertEqual(digit_four.summary.cases, 2)
        self.assertEqual(digit_four.maximum_absence, 9)
        self.assertEqual(
            [(group.key, group.summary.cases) for group in report.long_absences_by_digit],
            [(4, 2)],
        )

    def test_digit_coverage_report_selects_latest_chronologically(self) -> None:
        older = DigitCoverageWindow(
            wheel="Bari",
            wheel_order=1,
            window_size=1,
            draw_numbers=(10,),
            start_date="2026-01-10",
            end_date="2026-01-10",
            digit_counts=(1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
        )
        latest = DigitCoverageWindow(
            wheel="Bari",
            wheel_order=1,
            window_size=1,
            draw_numbers=(11,),
            start_date="2026-01-11",
            end_date="2026-01-11",
            digit_counts=(1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        )
        roma = DigitCoverageWindow(
            wheel="Roma",
            wheel_order=8,
            window_size=1,
            draw_numbers=(11,),
            start_date="2026-01-11",
            end_date="2026-01-11",
            digit_counts=(0, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        )

        with patch(
            "lotto_digit_coverage.application.historical_signals.analyze_digit_coverage",
            return_value={1: (latest, roma, older)},
        ):
            report = build_digit_coverage_report(object(), max_window_size=1)

        self.assertEqual(report.global_summary[0].windows, 3)
        self.assertEqual(report.global_summary[0].complete, 1)
        self.assertEqual(
            [(row.wheel, row.window.draw_numbers) for row in report.latest_windows],
            [("Bari", (11,)), ("Roma", (11,))],
        )
        self.assertEqual(report.digit_absence[0].window_size, 1)
        self.assertIn(report.digit_absence[0].digit, {0, 9})


if __name__ == "__main__":
    unittest.main()
