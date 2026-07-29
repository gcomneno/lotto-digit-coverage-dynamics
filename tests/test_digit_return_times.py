from __future__ import annotations

import unittest

from strategies.digit_return_times import (
    build_return_observations,
    draw_contains_digit,
    matching_numbers,
    theoretical_hit_probability,
)
from strategies.lotto_repository import DrawSnapshot


def draw(
    number: int,
    values: tuple[int, ...],
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=f"2025-01-{number:02d}",
        wheel="Bari",
        wheel_order=1,
        numbers=values,
    )


class DigitReturnTimesTests(unittest.TestCase):
    def test_position_is_respected(self) -> None:
        current = draw(
            1,
            (90, 11, 22, 33, 44),
        )

        self.assertTrue(
            draw_contains_digit(
                current,
                digit=9,
                position="tens",
            )
        )

        self.assertFalse(
            draw_contains_digit(
                current,
                digit=9,
                position="units",
            )
        )

    def test_units_have_equal_number_counts(self) -> None:
        self.assertEqual(
            len(matching_numbers(0, "units")),
            9,
        )

        self.assertEqual(
            len(matching_numbers(9, "units")),
            9,
        )

    def test_nine_has_rare_tens_position(self) -> None:
        self.assertEqual(
            matching_numbers(9, "tens"),
            (90,),
        )

        self.assertLess(
            theoretical_hit_probability(9, "tens"),
            theoretical_hit_probability(1, "tens"),
        )

    def test_any_position_nine_has_lower_baseline(self) -> None:
        self.assertLess(
            theoretical_hit_probability(9, "any"),
            theoretical_hit_probability(1, "any"),
        )

    def test_builds_hazard_observations(self) -> None:
        draws = (
            draw(1, (10, 20, 30, 40, 50)),
            draw(2, (11, 22, 33, 44, 55)),
            draw(3, (9, 12, 34, 56, 78)),
        )

        observations = tuple(
            observation
            for observation in build_return_observations(
                draws,
                position="any",
            )
            if observation.digit == 9
        )

        self.assertEqual(len(observations), 2)

        self.assertEqual(
            observations[0].absence_streak,
            1,
        )
        self.assertFalse(observations[0].hit)

        self.assertEqual(
            observations[1].absence_streak,
            2,
        )
        self.assertTrue(observations[1].hit)


if __name__ == "__main__":
    unittest.main()
