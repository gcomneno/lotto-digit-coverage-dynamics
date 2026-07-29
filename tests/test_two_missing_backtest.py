from __future__ import annotations

import unittest

from analyze_two_missing_backtest import (
    build_signals_for_wheel,
    theoretical_pair_probabilities,
)
from strategies.lotto_repository import DrawSnapshot


def draw(
    number: int,
    values: tuple[int, ...],
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=f"2026-01-{number:02d}",
        wheel="Bari",
        wheel_order=1,
        numbers=values,
    )


class TwoMissingBacktestTests(unittest.TestCase):
    def test_pair_has_high_probability_of_any_hit(self) -> None:
        probability_any, probability_both = (
            theoretical_pair_probabilities(1, 2)
        )

        self.assertAlmostEqual(
            probability_any,
            0.9130857879,
            places=9,
        )

        self.assertAlmostEqual(
            probability_both,
            0.4502008088,
            places=9,
        )

    def test_pair_with_nine_has_lower_probability(self) -> None:
        ordinary_any, ordinary_both = (
            theoretical_pair_probabilities(1, 2)
        )

        nine_any, nine_both = (
            theoretical_pair_probabilities(1, 9)
        )

        self.assertLess(nine_any, ordinary_any)
        self.assertLess(nine_both, ordinary_both)

    def test_detects_any_without_both(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 60, 77)),
            draw(2, (8, 11, 22, 33, 44)),
        )

        signals = build_signals_for_wheel(
            draws,
            window_size=1,
        )

        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].missing_digits,
            (8, 9),
        )
        self.assertTrue(signals[0].hit_any)
        self.assertFalse(signals[0].hit_both)

    def test_detects_complete_coverage(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 60, 77)),
            draw(2, (89, 11, 22, 33, 44)),
        )

        signals = build_signals_for_wheel(
            draws,
            window_size=1,
        )

        self.assertEqual(len(signals), 1)
        self.assertTrue(signals[0].hit_any)
        self.assertTrue(signals[0].hit_both)


if __name__ == "__main__":
    unittest.main()
