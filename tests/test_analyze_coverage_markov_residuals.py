from __future__ import annotations

import unittest

from analyze_coverage_markov_residuals import (
    band_sort_key,
    expectation_band,
    format_digits,
    summarize,
)
from strategies.coverage_markov_residuals import (
    MarkovResidualObservation,
)


def observation(
    predicted: float,
    actual: int,
) -> MarkovResidualObservation:
    return MarkovResidualObservation(
        wheel="Bari",
        wheel_order=1,
        current_draw=1,
        current_date="2025-01-01",
        cycle_number=1,
        draws_in_cycle=1,
        missing_digits=frozenset({9}),
        predicted_remaining=predicted,
        actual_remaining=actual,
    )


class AnalyzeCoverageMarkovResidualTests(unittest.TestCase):
    def test_expectation_bands(self) -> None:
        self.assertEqual(expectation_band(1.50), "<1.75")
        self.assertEqual(expectation_band(2.00), "1.75–2.25")
        self.assertEqual(expectation_band(3.50), "3.25+")

    def test_band_order(self) -> None:
        labels = ["3.25+", "<1.75", "2.25–2.75"]

        self.assertEqual(
            sorted(labels, key=band_sort_key),
            ["<1.75", "2.25–2.75", "3.25+"],
        )

    def test_summarize(self) -> None:
        items = (
            observation(1.5, 1),
            observation(2.5, 3),
        )

        result = summarize(items)

        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], 2.0)
        self.assertEqual(result[2], 2.0)
        self.assertEqual(result[3], 0.0)
        self.assertEqual(result[4], 0.5)
        self.assertEqual(result[5], 0.5)

    def test_formats_state(self) -> None:
        self.assertEqual(
            format_digits(frozenset({9, 2, 5})),
            "{2,5,9}",
        )


if __name__ == "__main__":
    unittest.main()
