from __future__ import annotations

import unittest

from analyze_prequential_replay import (
    observation_to_dict,
    summarize,
)
from strategies.prequential_replay import (
    PrequentialReplayObservation,
)


def observation(
    probability: float,
    completed: bool,
) -> PrequentialReplayObservation:
    return PrequentialReplayObservation(
        target_draw=101,
        target_date="2025-06-01",
        wheel="Bari",
        wheel_order=1,
        source_latest_draw=100,
        source_latest_date="2025-05-30",
        cycle_age=2,
        missing_digits=frozenset({9}),
        completion_probability_within=(
            (1, probability),
            (2, 0.75),
        ),
        expected_remaining_draws=2.0,
        target_numbers=(1, 2, 3, 4, 5),
        target_digits=frozenset({0, 1, 2, 3, 4, 5}),
        completed=completed,
        remaining_before_reset=(
            frozenset()
            if completed
            else frozenset({9})
        ),
    )


class AnalyzePrequentialReplayTests(unittest.TestCase):
    def test_summarize(self) -> None:
        result = summarize(
            (
                observation(0.25, False),
                observation(0.75, True),
            )
        )

        self.assertEqual(result["cases"], 2)
        self.assertEqual(
            result["observed_closures"],
            1,
        )
        self.assertEqual(
            result["expected_closures"],
            1.0,
        )
        self.assertEqual(
            result["delta_rate"],
            0.0,
        )
        self.assertAlmostEqual(
            result["brier_score"],
            0.0625,
        )

    def test_serializes_sets_and_probabilities(self) -> None:
        serialized = observation_to_dict(
            observation(0.45, False)
        )

        self.assertEqual(
            serialized["missing_digits"],
            [9],
        )
        self.assertEqual(
            serialized[
                "completion_probability_within"
            ]["1"],
            0.45,
        )
        self.assertEqual(
            serialized["remaining_before_reset"],
            [9],
        )


if __name__ == "__main__":
    unittest.main()
