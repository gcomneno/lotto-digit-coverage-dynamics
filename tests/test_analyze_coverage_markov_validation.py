from __future__ import annotations

import unittest

from analyze_coverage_markov_validation import (
    band_sort_key,
    format_digits,
    grouped_calibration_error,
    probability_band,
    summarize,
)
from strategies.coverage_markov_validation import (
    MarkovCalibrationObservation,
)


def observation(
    probability: float,
    completed: bool,
) -> MarkovCalibrationObservation:
    return MarkovCalibrationObservation(
        wheel="Bari",
        wheel_order=1,
        current_draw=1,
        current_date="2025-01-01",
        draws_in_cycle=1,
        missing_digits=frozenset({9}),
        horizon=1,
        predicted_probability=probability,
        completed_within=completed,
    )


class AnalyzeCoverageMarkovValidationTests(unittest.TestCase):
    def test_probability_bands(self) -> None:
        self.assertEqual(
            probability_band(0.00),
            "0–10%",
        )
        self.assertEqual(
            probability_band(0.10),
            "10–25%",
        )
        self.assertEqual(
            probability_band(0.50),
            "50–75%",
        )
        self.assertEqual(
            probability_band(1.00),
            "90–100%",
        )

    def test_band_order(self) -> None:
        bands = [
            "90–100%",
            "0–10%",
            "50–75%",
        ]

        self.assertEqual(
            sorted(bands, key=band_sort_key),
            [
                "0–10%",
                "50–75%",
                "90–100%",
            ],
        )

    def test_summarize_calibration(self) -> None:
        items = (
            observation(0.25, False),
            observation(0.75, True),
        )

        (
            total,
            hits,
            observed,
            predicted,
            delta,
            brier,
        ) = summarize(items)

        self.assertEqual(total, 2)
        self.assertEqual(hits, 1)
        self.assertEqual(observed, 0.5)
        self.assertEqual(predicted, 0.5)
        self.assertEqual(delta, 0.0)
        self.assertAlmostEqual(brier, 0.0625)

    def test_perfect_predictions_have_zero_brier(self) -> None:
        items = (
            observation(0.0, False),
            observation(1.0, True),
        )

        self.assertEqual(
            summarize(items)[5],
            0.0,
        )

    def test_grouped_calibration_error(self) -> None:
        groups = {
            "low": [
                observation(0.25, False),
                observation(0.25, False),
            ],
            "high": [
                observation(0.75, True),
                observation(0.75, True),
            ],
        }

        self.assertAlmostEqual(
            grouped_calibration_error(groups),
            0.25,
        )

    def test_formats_state(self) -> None:
        self.assertEqual(
            format_digits(frozenset({9, 2, 5})),
            "{2,5,9}",
        )


if __name__ == "__main__":
    unittest.main()
