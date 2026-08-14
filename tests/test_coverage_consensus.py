from __future__ import annotations

import unittest

from strategies.coverage_completion import ALL_DIGITS, CurrentCoverageState
from strategies.coverage_consensus import build_digit_consensus


def state(
    wheel: str,
    wheel_order: int,
    *,
    age: int,
    missing: frozenset[int],
    top: frozenset[int],
) -> CurrentCoverageState:
    return CurrentCoverageState(
        wheel=wheel,
        wheel_order=wheel_order,
        latest_draw=128,
        latest_date="2026-08-11",
        completed_cycles=10,
        draws_in_cycle=age,
        covered_digits=ALL_DIGITS.difference(missing),
        missing_digits=missing,
        synchronized=True,
        most_present_digits=top,
    )


class CoverageConsensusTests(unittest.TestCase):
    def test_counts_only_active_cycles_and_preserves_wheels(self) -> None:
        rows = build_digit_consensus(
            (
                state(
                    "Milano",
                    1,
                    age=2,
                    missing=frozenset({6, 8}),
                    top=frozenset({1}),
                ),
                state(
                    "Roma",
                    2,
                    age=3,
                    missing=frozenset({6}),
                    top=frozenset({8}),
                ),
                state(
                    "Torino",
                    3,
                    age=1,
                    missing=frozenset({9}),
                    top=frozenset({6}),
                ),
                state(
                    "Bari",
                    4,
                    age=0,
                    missing=ALL_DIGITS,
                    top=frozenset(),
                ),
            )
        )

        by_digit = {row.digit: row for row in rows}

        self.assertEqual(
            by_digit[6].missing_wheels,
            ("Milano", "Roma"),
        )
        self.assertEqual(
            by_digit[6].top_wheels,
            ("Torino",),
        )
        self.assertNotIn("Bari", by_digit[6].involved_wheels)
        self.assertEqual(by_digit[6].missing_count, 2)
        self.assertEqual(by_digit[6].top_count, 1)


if __name__ == "__main__":
    unittest.main()
