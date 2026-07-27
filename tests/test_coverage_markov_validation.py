from __future__ import annotations

import unittest

from strategies.coverage_markov import (
    completion_probability_within,
)
from strategies.coverage_markov_validation import (
    build_calibration_observations,
    normalize_horizons,
)
from strategies.twin_digits import DrawSnapshot


def draw(
    number: int,
    values: tuple[int, ...],
    wheel: str = "Bari",
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=f"2025-01-{number:02d}",
        wheel=wheel,
        wheel_order=1,
        numbers=values,
    )


class CoverageMarkovValidationTests(unittest.TestCase):
    def test_normalizes_horizons(self) -> None:
        self.assertEqual(
            normalize_horizons((3, 1, 3, 2)),
            (1, 2, 3),
        )

    def test_rejects_invalid_horizon(self) -> None:
        with self.assertRaises(ValueError):
            normalize_horizons((0, 1))

    def test_includes_fresh_state_after_first_completion(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 89)),
            draw(2, (11, 22, 33, 44, 55)),
        )

        observations = build_calibration_observations(
            draws,
            horizons=(1,),
        )

        self.assertEqual(len(observations), 1)
        self.assertEqual(
            observations[0].missing_digits,
            frozenset(range(10)),
        )
        self.assertEqual(
            observations[0].draws_in_cycle,
            0,
        )

    def test_detects_completion_within_horizon(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 89)),
            draw(2, (11, 22, 33, 44, 55)),
            draw(3, (9, 12, 34, 56, 78)),
        )

        observations = build_calibration_observations(
            draws,
            horizons=(2,),
        )

        self.assertTrue(
            observations[0].completed_within
        )

    def test_excludes_right_censored_failure(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 89)),
            draw(2, (11, 22, 33, 44, 55)),
        )

        observations = build_calibration_observations(
            draws,
            horizons=(2,),
        )

        self.assertEqual(observations, ())

    def test_prediction_matches_markov_engine(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 89)),
            draw(2, (11, 22, 33, 44, 55)),
        )

        observation = build_calibration_observations(
            draws,
            horizons=(1,),
        )[0]

        self.assertAlmostEqual(
            observation.predicted_probability,
            completion_probability_within(
                range(10),
                1,
            ),
        )

    def test_rejects_mixed_wheels(self) -> None:
        with self.assertRaises(ValueError):
            build_calibration_observations(
                (
                    draw(1, (1, 23, 45, 67, 89)),
                    draw(
                        2,
                        (11, 22, 33, 44, 55),
                        wheel="Roma",
                    ),
                )
            )


if __name__ == "__main__":
    unittest.main()
