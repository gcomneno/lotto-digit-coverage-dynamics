from __future__ import annotations

import unittest

from strategies.coverage_completion import (
    exact_completion_probability,
)
from strategies.coverage_markov import (
    COMPLETE_STATE,
    completion_probability_within,
    expected_remaining_draws,
    maturity_metrics,
    transition_distribution,
    transition_probability,
)


class CoverageMarkovTests(unittest.TestCase):
    def test_complete_state_is_absorbing(self) -> None:
        self.assertEqual(
            transition_distribution(()),
            {COMPLETE_STATE: 1.0},
        )

        self.assertEqual(
            expected_remaining_draws(()),
            0.0,
        )

    def test_transition_distribution_sums_to_one(self) -> None:
        for state in (
            {9},
            {3, 9},
            {2, 5, 9},
            {0, 1, 2, 3},
        ):
            distribution = transition_distribution(state)

            self.assertAlmostEqual(
                sum(distribution.values()),
                1.0,
                places=10,
            )

    def test_transitions_only_remove_missing_digits(self) -> None:
        current = frozenset({2, 5, 9})

        for next_state in transition_distribution(current):
            self.assertTrue(
                next_state.issubset(current)
            )

    def test_one_step_completion_matches_exact_probability(self) -> None:
        for state in (
            {9},
            {3, 9},
            {2, 5, 9},
        ):
            expected = exact_completion_probability(state)

            self.assertAlmostEqual(
                transition_probability(
                    state,
                    COMPLETE_STATE,
                ),
                expected,
            )

            self.assertAlmostEqual(
                completion_probability_within(
                    state,
                    1,
                ),
                expected,
            )

    def test_single_digit_has_geometric_expectation(self) -> None:
        probability = exact_completion_probability({9})

        self.assertAlmostEqual(
            expected_remaining_draws({9}),
            1.0 / probability,
            places=10,
        )

    def test_completion_probability_is_non_decreasing(self) -> None:
        values = [
            completion_probability_within(
                {3, 9},
                horizon,
            )
            for horizon in range(1, 6)
        ]

        self.assertEqual(
            values,
            sorted(values),
        )

        self.assertLess(values[-1], 1.0)

    def test_rejects_impossible_transition(self) -> None:
        with self.assertRaises(ValueError):
            transition_probability(
                {3, 9},
                {2, 3, 9},
            )

    def test_maturity_metrics_are_consistent(self) -> None:
        metrics = maturity_metrics(
            {3, 9},
            horizons=(1, 2, 3),
        )

        self.assertEqual(
            metrics["missing_digits"],
            frozenset({3, 9}),
        )

        completion = metrics["completion_within"]

        self.assertAlmostEqual(
            metrics["one_step_probability"],
            completion[1],
        )

        self.assertGreater(
            completion[3],
            completion[2],
        )

        self.assertGreater(
            metrics["expected_remaining_draws"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
