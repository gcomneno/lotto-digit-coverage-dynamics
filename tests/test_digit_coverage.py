from __future__ import annotations

import unittest
from pathlib import Path

from strategies.digit_coverage import (
    analyze_digit_coverage,
    build_coverage_windows,
    count_all_digits,
    load_draws_by_wheel,
)
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
)


DATABASE_PATH = Path("data/lotto-current.sqlite3")


def snapshot(
    draw_number: int,
    numbers: tuple[int, ...],
    wheel: str = "Bari",
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=draw_number,
        draw_date=f"2026-01-{draw_number:02d}",
        wheel=wheel,
        wheel_order=1,
        numbers=numbers,
    )


class DigitCoverageUnitTests(unittest.TestCase):
    def test_counts_zero_from_leading_zero(self) -> None:
        draws = (
            snapshot(
                1,
                (1, 90, 11, 22, 33),
            ),
        )

        counts = count_all_digits(draws)

        self.assertEqual(counts[0], 2)
        self.assertEqual(counts[1], 3)
        self.assertEqual(counts[2], 2)
        self.assertEqual(counts[3], 2)
        self.assertEqual(counts[9], 1)
        self.assertEqual(sum(counts), 10)

    def test_identifies_present_and_missing_digits(self) -> None:
        draws = (
            snapshot(
                1,
                (1, 23, 45, 67, 89),
            ),
        )

        window = build_coverage_windows(
            draws,
            window_size=1,
        )[0]

        self.assertEqual(
            window.present_digits,
            tuple(range(10)),
        )
        self.assertEqual(window.missing_digits, ())
        self.assertEqual(window.missing_count, 0)

    def test_builds_moving_windows(self) -> None:
        draws = (
            snapshot(1, (1, 2, 3, 4, 5)),
            snapshot(2, (6, 7, 8, 9, 10)),
            snapshot(3, (11, 12, 13, 14, 15)),
            snapshot(4, (16, 17, 18, 19, 20)),
        )

        windows = build_coverage_windows(
            draws,
            window_size=3,
        )

        self.assertEqual(len(windows), 2)
        self.assertEqual(
            windows[0].draw_numbers,
            (1, 2, 3),
        )
        self.assertEqual(
            windows[1].draw_numbers,
            (2, 3, 4),
        )
        self.assertEqual(
            windows[0].total_digit_slots,
            30,
        )

    def test_rejects_mixed_wheels(self) -> None:
        draws = (
            snapshot(1, (1, 2, 3, 4, 5)),
            snapshot(
                2,
                (6, 7, 8, 9, 10),
                wheel="Roma",
            ),
        )

        with self.assertRaises(ValueError):
            build_coverage_windows(
                draws,
                window_size=2,
            )


@unittest.skipUnless(
    DATABASE_PATH.is_file(),
    "Database di integrazione non disponibile.",
)
class DigitCoverageIntegrationTests(unittest.TestCase):
    def test_expected_window_totals(self) -> None:
        with LottoRepository(DATABASE_PATH) as repository:
            draws_by_wheel = load_draws_by_wheel(
                repository
            )
            analysis = analyze_digit_coverage(
                repository,
                max_window_size=3,
            )

        for window_size, windows in analysis.items():
            expected_count = sum(
                max(
                    0,
                    len(draws) - window_size + 1,
                )
                for draws in draws_by_wheel.values()
            )

            self.assertEqual(
                len(windows),
                expected_count,
            )

    def test_every_window_has_expected_digit_slots(self) -> None:
        with LottoRepository(DATABASE_PATH) as repository:
            analysis = analyze_digit_coverage(
                repository,
                max_window_size=3,
            )

        for window_size, windows in analysis.items():
            expected_slots = window_size * 10

            self.assertTrue(
                all(
                    window.total_digit_slots
                    == expected_slots
                    for window in windows
                )
            )


if __name__ == "__main__":
    unittest.main()
