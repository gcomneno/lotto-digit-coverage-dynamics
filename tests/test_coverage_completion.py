from __future__ import annotations

import unittest

from strategies.coverage_completion import (
    build_completion_observations,
    digits_in_draw,
    exact_completion_probability,
)
from strategies.digit_return_times import (
    theoretical_hit_probability,
)
from strategies.lotto_repository import DrawSnapshot


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


class CoverageCompletionTests(unittest.TestCase):
    def test_leading_zero_contributes_to_coverage(self) -> None:
        current = draw(
            1,
            (1, 23, 45, 67, 88),
        )

        self.assertIn(0, digits_in_draw(current))

    def test_empty_missing_set_is_already_complete(self) -> None:
        self.assertEqual(
            exact_completion_probability(()),
            1.0,
        )

    def test_single_digit_matches_existing_baseline(self) -> None:
        for digit in range(10):
            self.assertAlmostEqual(
                exact_completion_probability((digit,)),
                theoretical_hit_probability(
                    digit,
                    "any",
                ),
            )

    def test_two_missing_digits_are_harder_than_one(self) -> None:
        pair_probability = exact_completion_probability(
            (3, 7)
        )

        self.assertLess(
            pair_probability,
            exact_completion_probability((3,)),
        )
        self.assertGreater(pair_probability, 0.0)

    def test_skips_initial_left_censored_cycle(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 89)),
            draw(2, (1, 23, 45, 67, 88)),
            draw(3, (9, 12, 34, 56, 78)),
        )

        observations = build_completion_observations(draws)

        self.assertEqual(len(observations), 1)
        self.assertEqual(
            observations[0].missing_digits,
            frozenset({9}),
        )
        self.assertTrue(
            observations[0].completed_next
        )

    def test_detects_failed_completion(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 89)),
            draw(2, (1, 23, 45, 67, 88)),
            draw(3, (1, 12, 34, 56, 78)),
        )

        observation = build_completion_observations(draws)[0]

        self.assertFalse(observation.completed_next)

    def test_rejects_mixed_wheels(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 89)),
            draw(
                2,
                (1, 23, 45, 67, 88),
                wheel="Roma",
            ),
        )

        with self.assertRaises(ValueError):
            build_completion_observations(draws)


if __name__ == "__main__":
    unittest.main()
