from __future__ import annotations

import unittest

from analyze_coverage_completion import (
    age_bucket,
    completed_cycle_lengths,
    format_digits,
    summarize,
)
from strategies.coverage_completion import (
    CoverageCompletionObservation,
    exact_completion_probability,
)


def observation(
    *,
    cycle: int,
    draws_in_cycle: int,
    missing: frozenset[int],
    completed: bool,
) -> CoverageCompletionObservation:
    return CoverageCompletionObservation(
        wheel="Bari",
        wheel_order=1,
        cycle_number=cycle,
        draws_in_cycle=draws_in_cycle,
        current_draw=draws_in_cycle,
        current_date="2025-01-01",
        target_draw=draws_in_cycle + 1,
        target_date="2025-01-02",
        covered_digits=frozenset(range(10)).difference(missing),
        missing_digits=missing,
        completed_next=completed,
    )


class AnalyzeCoverageCompletionTests(unittest.TestCase):
    def test_formats_missing_state(self) -> None:
        self.assertEqual(
            format_digits(frozenset({9, 2, 5})),
            "{2,5,9}",
        )

    def test_cycle_age_bucket(self) -> None:
        self.assertEqual(age_bucket(1), "1")
        self.assertEqual(age_bucket(4), "4")
        self.assertEqual(age_bucket(5), "5+")
        self.assertEqual(age_bucket(20), "5+")

    def test_finds_completed_cycle_length(self) -> None:
        items = (
            observation(
                cycle=1,
                draws_in_cycle=1,
                missing=frozenset({9}),
                completed=False,
            ),
            observation(
                cycle=1,
                draws_in_cycle=2,
                missing=frozenset({9}),
                completed=True,
            ),
        )

        self.assertEqual(
            completed_cycle_lengths(items),
            {("Bari", 1): 3},
        )

    def test_summary_uses_exact_state_probability(self) -> None:
        items = (
            observation(
                cycle=1,
                draws_in_cycle=1,
                missing=frozenset({9}),
                completed=True,
            ),
        )

        total, hits, observed, expected, delta = summarize(items)

        self.assertEqual(total, 1)
        self.assertEqual(hits, 1)
        self.assertEqual(observed, 1.0)
        self.assertAlmostEqual(
            expected,
            exact_completion_probability((9,)),
        )
        self.assertAlmostEqual(
            delta,
            1.0 - expected,
        )


if __name__ == "__main__":
    unittest.main()
