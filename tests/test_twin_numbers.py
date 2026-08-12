from __future__ import annotations

import unittest

from strategies.lotto_repository import DrawSnapshot
from strategies.twin_numbers import (
    NULL_TWIN_PROBABILITY,
    TWIN_NUMBERS,
    benjamini_hochberg,
    binomial_two_sided_p_value,
    build_twin_observations,
    wilson_interval,
)


def draw(number: int, values: tuple[int, ...]) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=f"2026-01-{number:02d}",
        wheel="Bari",
        wheel_order=1,
        numbers=values,
    )


class TwinNumberTests(unittest.TestCase):
    def test_null_and_twin_family_are_exact(self) -> None:
        self.assertEqual(
            TWIN_NUMBERS,
            {
                1: 11,
                2: 22,
                3: 33,
                4: 44,
                5: 55,
                6: 66,
                7: 77,
                8: 88,
            },
        )
        self.assertAlmostEqual(NULL_TWIN_PROBABILITY, 1.0 / 18.0)

    def test_conditions_are_built_ex_ante_after_synchronization(self) -> None:
        observations = build_twin_observations(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (11, 22, 33, 44, 55)),
                draw(3, (66, 12, 34, 57, 80)),
                draw(4, (19, 29, 39, 49, 59)),
            )
        )

        target_two = {
            observation.digit: observation
            for observation in observations
            if observation.target_draw == 2
        }
        target_three = {
            observation.digit: observation
            for observation in observations
            if observation.target_draw == 3
        }

        self.assertEqual(target_two[6].conditions, ("baseline",))
        self.assertIn("missing", target_three[6].conditions)
        self.assertNotIn("top", target_three[6].conditions)
        self.assertTrue(target_three[6].hit)
        self.assertIn("top", target_three[1].conditions)
        self.assertFalse(target_three[1].hit)

    def test_last_missing_condition_is_evaluated_before_target(self) -> None:
        observations = build_twin_observations(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (1, 23, 45, 67, 79)),
                draw(3, (88, 12, 34, 56, 70)),
            )
        )
        target_three = {
            observation.digit: observation
            for observation in observations
            if observation.target_draw == 3
        }

        self.assertIn("missing", target_three[8].conditions)
        self.assertIn("last-missing", target_three[8].conditions)
        self.assertTrue(target_three[8].hit)

    def test_wilson_interval_contains_observed_rate(self) -> None:
        low, high = wilson_interval(12, 200)

        self.assertLess(low, 12 / 200)
        self.assertGreater(high, 12 / 200)

    def test_exact_binomial_p_value_is_bounded(self) -> None:
        value = binomial_two_sided_p_value(12, 200)

        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

    def test_benjamini_hochberg_is_monotone_in_rank(self) -> None:
        adjusted = benjamini_hochberg((0.01, 0.04, 0.03))

        self.assertAlmostEqual(adjusted[0], 0.03)
        self.assertAlmostEqual(adjusted[1], 0.04)
        self.assertAlmostEqual(adjusted[2], 0.04)


if __name__ == "__main__":
    unittest.main()
