from __future__ import annotations

import unittest

from strategies.coverage_cycle_history import (
    build_wheel_cycle_history,
    flatten_completed_cycles,
    merge_draws_by_wheel,
)
from strategies.lotto_repository import DrawSnapshot


COMPLETE_DRAW = (1, 23, 45, 67, 89)
LOW_DIGITS_DRAW = (1, 2, 3, 4, 5)
HIGH_DIGITS_DRAW = (67, 68, 69, 78, 89)


def make_draw(
    draw_number: int,
    draw_date: str,
    numbers: tuple[int, ...],
    *,
    wheel: str = "Bari",
    wheel_order: int = 1,
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=draw_number,
        draw_date=draw_date,
        wheel=wheel,
        wheel_order=wheel_order,
        numbers=numbers,
    )


class CoverageCycleHistoryTests(
    unittest.TestCase
):
    def test_skips_initial_partial_and_records_cycles(
        self,
    ) -> None:
        draws = (
            make_draw(
                208,
                "2025-12-30",
                COMPLETE_DRAW,
            ),
            make_draw(
                209,
                "2025-12-31",
                LOW_DIGITS_DRAW,
            ),
            make_draw(
                1,
                "2026-01-02",
                HIGH_DIGITS_DRAW,
            ),
            make_draw(
                2,
                "2026-01-04",
                COMPLETE_DRAW,
            ),
            make_draw(
                3,
                "2026-01-06",
                LOW_DIGITS_DRAW,
            ),
        )

        history = build_wheel_cycle_history(
            draws
        )

        self.assertTrue(history.synchronized)
        self.assertEqual(
            history.initial_left_censored_draws,
            1,
        )
        self.assertEqual(
            [
                cycle.draws_in_cycle
                for cycle
                in history.completed_cycles
            ],
            [2, 1],
        )
        self.assertEqual(
            [
                cycle.cycle_number
                for cycle
                in history.completed_cycles
            ],
            [1, 2],
        )
        self.assertEqual(
            history.completed_cycles[0].start_date,
            "2025-12-31",
        )
        self.assertEqual(
            history.completed_cycles[0].end_date,
            "2026-01-02",
        )
        self.assertEqual(
            history.right_censored_draws,
            1,
        )
        self.assertEqual(
            history.right_censored_missing_digits,
            frozenset({6, 7, 8, 9}),
        )

    def test_unsynchronized_archive_has_no_cycles(
        self,
    ) -> None:
        history = build_wheel_cycle_history(
            (
                make_draw(
                    1,
                    "2026-01-02",
                    LOW_DIGITS_DRAW,
                ),
                make_draw(
                    2,
                    "2026-01-04",
                    LOW_DIGITS_DRAW,
                ),
            )
        )

        self.assertFalse(history.synchronized)
        self.assertEqual(
            history.initial_left_censored_draws,
            2,
        )
        self.assertEqual(
            history.completed_cycles,
            (),
        )
        self.assertEqual(
            history.right_censored_draws,
            0,
        )
        self.assertEqual(
            history.right_censored_missing_digits,
            frozenset(),
        )

    def test_completion_on_last_draw_has_empty_tail(
        self,
    ) -> None:
        history = build_wheel_cycle_history(
            (
                make_draw(
                    1,
                    "2026-01-02",
                    COMPLETE_DRAW,
                ),
                make_draw(
                    2,
                    "2026-01-04",
                    COMPLETE_DRAW,
                ),
            )
        )

        self.assertEqual(
            len(history.completed_cycles),
            1,
        )
        self.assertEqual(
            history.completed_cycles[
                0
            ].draws_in_cycle,
            1,
        )
        self.assertEqual(
            history.right_censored_draws,
            0,
        )
        self.assertEqual(
            history.right_censored_missing_digits,
            frozenset(),
        )

    def test_merges_years_by_date_despite_reset_number(
        self,
    ) -> None:
        first = {
            "Bari": (
                make_draw(
                    208,
                    "2025-12-30",
                    LOW_DIGITS_DRAW,
                ),
                make_draw(
                    209,
                    "2025-12-31",
                    LOW_DIGITS_DRAW,
                ),
            )
        }

        second = {
            "Bari": (
                make_draw(
                    1,
                    "2026-01-02",
                    HIGH_DIGITS_DRAW,
                ),
            )
        }

        merged = merge_draws_by_wheel(
            (second, first)
        )

        self.assertEqual(
            [
                draw.draw_number
                for draw in merged["Bari"]
            ],
            [208, 209, 1],
        )
        self.assertEqual(
            [
                draw.draw_date
                for draw in merged["Bari"]
            ],
            [
                "2025-12-30",
                "2025-12-31",
                "2026-01-02",
            ],
        )

    def test_rejects_duplicate_historical_draw(
        self,
    ) -> None:
        duplicate = make_draw(
            1,
            "2026-01-02",
            COMPLETE_DRAW,
        )

        with self.assertRaises(ValueError):
            merge_draws_by_wheel(
                (
                    {"Bari": (duplicate,)},
                    {"Bari": (duplicate,)},
                )
            )

    def test_rejects_inconsistent_wheel_metadata(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            build_wheel_cycle_history(
                (
                    make_draw(
                        1,
                        "2026-01-02",
                        COMPLETE_DRAW,
                    ),
                    make_draw(
                        2,
                        "2026-01-04",
                        COMPLETE_DRAW,
                        wheel="Cagliari",
                        wheel_order=2,
                    ),
                )
            )

        with self.assertRaises(ValueError):
            merge_draws_by_wheel(
                (
                    {
                        "Bari": (
                            make_draw(
                                1,
                                "2025-12-30",
                                COMPLETE_DRAW,
                                wheel_order=1,
                            ),
                        )
                    },
                    {
                        "Bari": (
                            make_draw(
                                1,
                                "2026-01-02",
                                COMPLETE_DRAW,
                                wheel_order=2,
                            ),
                        )
                    },
                )
            )

    def test_flattens_cycles_in_historical_order(
        self,
    ) -> None:
        bari = build_wheel_cycle_history(
            (
                make_draw(
                    1,
                    "2026-01-02",
                    COMPLETE_DRAW,
                ),
                make_draw(
                    2,
                    "2026-01-06",
                    COMPLETE_DRAW,
                ),
            )
        )

        cagliari = build_wheel_cycle_history(
            (
                make_draw(
                    1,
                    "2026-01-02",
                    COMPLETE_DRAW,
                    wheel="Cagliari",
                    wheel_order=2,
                ),
                make_draw(
                    2,
                    "2026-01-04",
                    COMPLETE_DRAW,
                    wheel="Cagliari",
                    wheel_order=2,
                ),
            )
        )

        cycles = flatten_completed_cycles(
            (bari, cagliari)
        )

        self.assertEqual(
            [
                cycle.wheel
                for cycle in cycles
            ],
            ["Cagliari", "Bari"],
        )


if __name__ == "__main__":
    unittest.main()
