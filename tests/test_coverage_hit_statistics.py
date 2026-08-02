from __future__ import annotations

import unittest

from strategies.coverage_hit_statistics import (
    CoverageHitObservation,
    required_hit_count,
    select_latest_targets,
    summarize_coverage_hits,
    theoretical_threshold_probability,
)
from strategies.coverage_markov import (
    transition_distribution,
)


def observation(
    *,
    target_draw: int,
    wheel_order: int,
    top: frozenset[int],
    missing: frozenset[int],
    hit: frozenset[int],
    probability: float,
) -> CoverageHitObservation:
    return CoverageHitObservation(
        wheel=f"Ruota-{wheel_order}",
        wheel_order=wheel_order,
        history_draw=target_draw - 1,
        history_date=f"2026-01-{target_draw - 1:02d}",
        target_draw=target_draw,
        target_date=f"2026-01-{target_draw:02d}",
        draws_in_cycle=2,
        most_present_digits=top,
        missing_digits=missing,
        target_digits=frozenset({0, 1, 2, 3}),
        hit_digits=hit,
        completion_within_one=probability,
        threshold_probability=(
            theoretical_threshold_probability(
                missing
            )
        ),
    )


class CoverageHitObservationTests(unittest.TestCase):
    def test_single_missing_requires_one_hit(
        self,
    ) -> None:
        obtained = observation(
            target_draw=2,
            wheel_order=1,
            top=frozenset({1, 2}),
            missing=frozenset({7}),
            hit=frozenset({7}),
            probability=0.25,
        )
        missed = observation(
            target_draw=2,
            wheel_order=2,
            top=frozenset({1}),
            missing=frozenset({7}),
            hit=frozenset(),
            probability=0.25,
        )

        self.assertEqual(obtained.required_hit_count, 1)
        self.assertTrue(obtained.obtained)
        self.assertFalse(missed.obtained)

    def test_multiple_missing_require_n_minus_one_hits(
        self,
    ) -> None:
        obtained = observation(
            target_draw=2,
            wheel_order=1,
            top=frozenset({1}),
            missing=frozenset({4, 7, 8, 9}),
            hit=frozenset({4, 7, 9}),
            probability=0.25,
        )
        missed = observation(
            target_draw=2,
            wheel_order=2,
            top=frozenset({1}),
            missing=frozenset({4, 7, 8, 9}),
            hit=frozenset({4, 7}),
            probability=0.25,
        )

        self.assertEqual(obtained.required_hit_count, 3)
        self.assertTrue(obtained.obtained)
        self.assertFalse(missed.obtained)


class TheoreticalThresholdProbabilityTests(
    unittest.TestCase
):
    def test_required_hit_count_uses_n_minus_one(
        self,
    ) -> None:
        self.assertEqual(required_hit_count(1), 1)
        self.assertEqual(required_hit_count(2), 1)
        self.assertEqual(required_hit_count(3), 2)
        self.assertEqual(required_hit_count(5), 4)

    def test_rejects_empty_missing_state(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            theoretical_threshold_probability(
                frozenset()
            )

    def test_single_missing_matches_full_completion(
        self,
    ) -> None:
        missing = frozenset({7})
        distribution = transition_distribution(
            missing
        )

        self.assertAlmostEqual(
            theoretical_threshold_probability(
                missing
            ),
            distribution[frozenset()],
        )

    def test_two_missing_requires_at_least_one_hit(
        self,
    ) -> None:
        missing = frozenset({4, 7})
        distribution = transition_distribution(
            missing
        )

        self.assertAlmostEqual(
            theoretical_threshold_probability(
                missing
            ),
            1.0 - distribution[missing],
        )

    def test_three_missing_sums_two_or_more_hits(
        self,
    ) -> None:
        missing = frozenset({1, 4, 7})
        distribution = transition_distribution(
            missing
        )
        expected = sum(
            probability
            for next_missing, probability
            in distribution.items()
            if len(next_missing) <= 1
        )

        self.assertAlmostEqual(
            theoretical_threshold_probability(
                missing
            ),
            expected,
        )


class LatestTargetSelectionTests(unittest.TestCase):
    def test_selects_last_distinct_targets_across_wheels(
        self,
    ) -> None:
        observations = tuple(
            observation(
                target_draw=target,
                wheel_order=wheel,
                top=frozenset({1}),
                missing=frozenset({7}),
                hit=frozenset(),
                probability=0.68,
            )
            for target in (2, 3, 4)
            for wheel in (1, 2)
        )

        selected = select_latest_targets(
            observations,
            target_count=2,
        )

        self.assertEqual(
            {
                item.target_draw
                for item in selected
            },
            {3, 4},
        )
        self.assertEqual(len(selected), 4)

    def test_rejects_non_positive_target_count(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            select_latest_targets(
                (),
                target_count=0,
            )


class CoverageHitSummaryTests(unittest.TestCase):
    def test_groups_by_top_and_missing_counts(
        self,
    ) -> None:
        observations = (
            observation(
                target_draw=2,
                wheel_order=1,
                top=frozenset({1, 2}),
                missing=frozenset({7}),
                hit=frozenset({7}),
                probability=0.6816,
            ),
            observation(
                target_draw=3,
                wheel_order=1,
                top=frozenset({3, 4}),
                missing=frozenset({9}),
                hit=frozenset(),
                probability=0.6816,
            ),
        )

        summaries = summarize_coverage_hits(
            observations
        )

        self.assertEqual(len(summaries), 1)

        summary = summaries[0]

        self.assertEqual(summary.most_present_count, 2)
        self.assertEqual(summary.missing_count, 1)
        self.assertAlmostEqual(
            summary.mean_completion_within_one,
            0.6816,
        )
        self.assertAlmostEqual(
            summary.mean_threshold_probability,
            (
                theoretical_threshold_probability(
                    frozenset({7})
                )
                + theoretical_threshold_probability(
                    frozenset({9})
                )
            )
            / 2,
        )
        self.assertEqual(summary.attempts, 2)
        self.assertEqual(summary.obtained, 1)
        self.assertEqual(summary.missed, 1)
        self.assertEqual(summary.success_rate, 0.5)
        self.assertEqual(summary.hit_digit_count, 1)
        self.assertAlmostEqual(
            summary.success_excess,
            (
                0.5
                - summary.mean_threshold_probability
            ),
        )


if __name__ == "__main__":
    unittest.main()
