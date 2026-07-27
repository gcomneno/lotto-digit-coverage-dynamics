from __future__ import annotations

import unittest

from analyze_current_coverage import (
    format_digits,
    maturity_sort_key,
)
from strategies.coverage_completion import (
    ALL_DIGITS,
    CurrentCoverageState,
    current_coverage_state,
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


class CurrentCoverageStateTests(unittest.TestCase):
    def test_latest_completion_starts_empty_new_cycle(self) -> None:
        state = current_coverage_state(
            (
                draw(1, (1, 23, 45, 67, 89)),
            )
        )

        self.assertTrue(state.synchronized)
        self.assertEqual(state.draws_in_cycle, 0)
        self.assertEqual(
            state.missing_digits,
            ALL_DIGITS,
        )

    def test_tracks_state_after_completed_cycle(self) -> None:
        state = current_coverage_state(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (11, 22, 33, 44, 55)),
            )
        )

        self.assertTrue(state.synchronized)
        self.assertEqual(state.completed_cycles, 1)
        self.assertEqual(state.draws_in_cycle, 1)
        self.assertEqual(
            state.covered_digits,
            frozenset({1, 2, 3, 4, 5}),
        )
        self.assertEqual(
            state.missing_digits,
            frozenset({0, 6, 7, 8, 9}),
        )

    def test_marks_unobserved_initial_cycle(self) -> None:
        state = current_coverage_state(
            (
                draw(1, (11, 22, 33, 44, 55)),
            )
        )

        self.assertFalse(state.synchronized)

    def test_rejects_mixed_wheels(self) -> None:
        with self.assertRaises(ValueError):
            current_coverage_state(
                (
                    draw(1, (1, 23, 45, 67, 89)),
                    draw(
                        2,
                        (11, 22, 33, 44, 55),
                        wheel="Roma",
                    ),
                )
            )

    def test_formats_state(self) -> None:
        self.assertEqual(
            format_digits(frozenset({9, 2, 5})),
            "{2,5,9}",
        )

    def test_ranking_prefers_lower_expected_time(self) -> None:
        state = CurrentCoverageState(
            wheel="Bari",
            wheel_order=1,
            latest_draw=1,
            latest_date="2025-01-01",
            completed_cycles=1,
            draws_in_cycle=1,
            covered_digits=frozenset(),
            missing_digits=frozenset({9}),
            synchronized=True,
        )

        slower = (
            state,
            {
                "expected_remaining_draws": 3.0,
                "completion_within": {1: 0.5},
            },
        )

        faster = (
            state,
            {
                "expected_remaining_draws": 2.0,
                "completion_within": {1: 0.4},
            },
        )

        self.assertLess(
            maturity_sort_key(faster),
            maturity_sort_key(slower),
        )


if __name__ == "__main__":
    unittest.main()
