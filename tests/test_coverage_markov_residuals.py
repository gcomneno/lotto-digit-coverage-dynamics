from __future__ import annotations

import unittest

from strategies.coverage_markov import expected_remaining_draws
from strategies.coverage_markov_residuals import (
    build_residual_observations,
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


class CoverageMarkovResidualTests(unittest.TestCase):
    def test_empty_archive_has_no_observations(self) -> None:
        self.assertEqual(
            build_residual_observations(()),
            (),
        )

    def test_includes_fresh_state_after_completion(self) -> None:
        observations = build_residual_observations(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (11, 22, 33, 44, 55)),
                draw(3, (60, 67, 78, 89, 90)),
            )
        )

        self.assertEqual(
            observations[0].missing_digits,
            frozenset(range(10)),
        )
        self.assertEqual(
            observations[0].actual_remaining,
            2,
        )

    def test_actual_residual_decreases_inside_cycle(self) -> None:
        observations = build_residual_observations(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (11, 22, 33, 44, 55)),
                draw(3, (60, 67, 78, 89, 90)),
            )
        )

        self.assertEqual(
            [
                observation.actual_remaining
                for observation in observations
            ],
            [2, 1],
        )

    def test_excludes_right_censored_states(self) -> None:
        observations = build_residual_observations(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (11, 22, 33, 44, 55)),
            )
        )

        self.assertEqual(observations, ())

    def test_prediction_matches_markov_engine(self) -> None:
        observation = build_residual_observations(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (11, 22, 33, 44, 55)),
                draw(3, (60, 67, 78, 89, 90)),
            )
        )[0]

        self.assertAlmostEqual(
            observation.predicted_remaining,
            expected_remaining_draws(range(10)),
        )

    def test_rejects_mixed_wheels(self) -> None:
        with self.assertRaises(ValueError):
            build_residual_observations(
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
