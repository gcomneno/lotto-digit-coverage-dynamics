from __future__ import annotations

import unittest
from unittest.mock import patch

from lotto_digit_coverage.application.historical_markov import (
    build_coverage_completion_report,
    build_markov_residual_report,
    build_markov_validation_report,
)
from strategies.coverage_completion import CoverageCompletionObservation
from strategies.coverage_markov_residuals import MarkovResidualObservation
from strategies.coverage_markov_validation import MarkovCalibrationObservation


class HistoricalMarkovApplicationTests(unittest.TestCase):
    def test_completion_report_owns_grouping_and_censoring(self) -> None:
        observations = (
            CoverageCompletionObservation(
                wheel="Bari",
                wheel_order=1,
                cycle_number=1,
                draws_in_cycle=2,
                current_draw=10,
                current_date="2026-01-10",
                target_draw=11,
                target_date="2026-01-11",
                covered_digits=frozenset(range(9)),
                missing_digits=frozenset({9}),
                completed_next=False,
            ),
            CoverageCompletionObservation(
                wheel="Bari",
                wheel_order=1,
                cycle_number=1,
                draws_in_cycle=3,
                current_draw=11,
                current_date="2026-01-11",
                target_draw=12,
                target_date="2026-01-12",
                covered_digits=frozenset(range(9)),
                missing_digits=frozenset({9}),
                completed_next=True,
            ),
            CoverageCompletionObservation(
                wheel="Bari",
                wheel_order=1,
                cycle_number=2,
                draws_in_cycle=1,
                current_draw=13,
                current_date="2026-01-13",
                target_draw=14,
                target_date="2026-01-14",
                covered_digits=frozenset(range(8)),
                missing_digits=frozenset({8, 9}),
                completed_next=False,
            ),
        )

        with patch(
            "lotto_digit_coverage.application.historical_markov.collect_completion_observations",
            return_value=observations,
        ):
            report = build_coverage_completion_report(
                object(),
                minimum_state_cases=1,
            )

        self.assertEqual(len(report.observations), 3)
        self.assertEqual(
            [(group.key, group.summary.cases) for group in report.by_missing_count],
            [(1, 2), (2, 1)],
        )
        self.assertEqual(report.right_censored_states, 1)
        self.assertEqual(
            [
                (
                    row.missing_count,
                    row.states,
                    row.minimum_remaining,
                    row.maximum_remaining,
                )
                for row in report.residual_rows
            ],
            [(1, 2, 1, 2)],
        )
        self.assertEqual(report.exact_states[0].key, frozenset({9}))

    def test_validation_report_owns_horizon_and_band_grouping(self) -> None:
        observations = (
            MarkovCalibrationObservation(
                wheel="Bari",
                wheel_order=1,
                current_draw=10,
                current_date="2026-01-10",
                draws_in_cycle=2,
                missing_digits=frozenset({9}),
                horizon=1,
                predicted_probability=0.68,
                completed_within=True,
            ),
            MarkovCalibrationObservation(
                wheel="Bari",
                wheel_order=1,
                current_draw=11,
                current_date="2026-01-11",
                draws_in_cycle=3,
                missing_digits=frozenset({9}),
                horizon=1,
                predicted_probability=0.68,
                completed_within=False,
            ),
            MarkovCalibrationObservation(
                wheel="Bari",
                wheel_order=1,
                current_draw=10,
                current_date="2026-01-10",
                draws_in_cycle=2,
                missing_digits=frozenset({9}),
                horizon=3,
                predicted_probability=0.95,
                completed_within=True,
            ),
        )

        with patch(
            "lotto_digit_coverage.application.historical_markov.collect_calibration_observations",
            return_value=observations,
        ):
            report = build_markov_validation_report(
                object(),
                horizons=(3, 1, 3),
                minimum_state_cases=1,
            )

        self.assertEqual(report.horizons, (1, 3))
        self.assertEqual(
            [(group.key, group.summary.cases) for group in report.overall],
            [(1, 2), (3, 1)],
        )
        self.assertEqual(
            [item.horizon for item in report.probability_bands],
            [1, 3],
        )
        self.assertEqual(report.exact_states_h1[0].key, frozenset({9}))
        self.assertEqual(report.exact_states_h3[0].key, frozenset({9}))

    def test_residual_report_owns_error_and_state_grouping(self) -> None:
        observations = (
            MarkovResidualObservation(
                wheel="Roma",
                wheel_order=8,
                current_draw=20,
                current_date="2026-02-01",
                cycle_number=2,
                draws_in_cycle=2,
                missing_digits=frozenset({1}),
                predicted_remaining=1.5,
                actual_remaining=2,
            ),
            MarkovResidualObservation(
                wheel="Roma",
                wheel_order=8,
                current_draw=21,
                current_date="2026-02-02",
                cycle_number=2,
                draws_in_cycle=3,
                missing_digits=frozenset({1}),
                predicted_remaining=1.5,
                actual_remaining=1,
            ),
        )

        with patch(
            "lotto_digit_coverage.application.historical_markov.collect_residual_observations",
            return_value=observations,
        ):
            report = build_markov_residual_report(
                object(),
                minimum_state_cases=1,
            )

        self.assertEqual(report.overall.states, 2)
        self.assertAlmostEqual(report.overall.actual_mean, 1.5)
        self.assertAlmostEqual(report.overall.predicted_mean, 1.5)
        self.assertAlmostEqual(report.overall.bias, 0.0)
        self.assertEqual(report.by_missing_count[0].key, 1)
        self.assertEqual(report.by_expectation_band[0].key, "<1.75")
        self.assertEqual(report.exact_states[0].key, frozenset({1}))


if __name__ == "__main__":
    unittest.main()
