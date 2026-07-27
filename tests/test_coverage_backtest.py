from __future__ import annotations

import unittest

from analyze_coverage_backtest import (
    build_signals_for_wheel,
    theoretical_hit_probability,
)
from strategies.twin_digits import DrawSnapshot


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


class CoverageBacktestTests(unittest.TestCase):
    def test_digit_nine_has_lower_baseline(self) -> None:
        self.assertLess(
            theoretical_hit_probability(9),
            theoretical_hit_probability(5),
        )

    def test_signal_hits_on_next_draw(self) -> None:
        draws = (
            draw(1, (1, 23, 45, 67, 80)),
            draw(2, (12, 34, 56, 78, 10)),
            draw(3, (9, 11, 22, 33, 44)),
        )

        signals = build_signals_for_wheel(
            draws,
            window_size=2,
        )

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].missing_digit, 9)
        self.assertTrue(signals[0].hit)
        self.assertEqual(signals[0].target_draw, 3)

    def test_no_signal_when_multiple_digits_are_missing(self) -> None:
        draws = (
            draw(1, (11, 22, 33, 44, 55)),
            draw(2, (11, 22, 33, 44, 55)),
            draw(3, (66, 77, 88, 89, 90)),
        )

        signals = build_signals_for_wheel(
            draws,
            window_size=2,
        )

        self.assertEqual(signals, ())


if __name__ == "__main__":
    unittest.main()
