from __future__ import annotations

import unittest

from strategies.coverage_markov import (
    absorption_quantiles,
    completion_probability_within,
    expected_remaining_draws,
    variance_remaining_draws,
)
from strategies.coverage_monotonicity import (
    ALL_DIGITS_MASK,
    comparable_mask_pairs,
    cover_relation_pairs,
    is_subset_mask,
    next_missing_mask,
    verify_absorption_monotonicity,
    verify_update_monotonicity,
)


class CoverageMonotonicityTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.update_summary = (
            verify_update_monotonicity()
        )

        cls.absorption_summary = (
            verify_absorption_monotonicity()
        )

    def test_comparable_pair_counts(
        self,
    ) -> None:
        self.assertEqual(
            sum(
                1
                for _ in comparable_mask_pairs(
                    include_equal=True
                )
            ),
            3**10,
        )

        self.assertEqual(
            sum(
                1
                for _ in comparable_mask_pairs()
            ),
            3**10 - 2**10,
        )

    def test_cover_relation_count(
        self,
    ) -> None:
        self.assertEqual(
            sum(
                1
                for _ in cover_relation_pairs()
            ),
            10 * 2**9,
        )

    def test_update_is_exhaustively_monotone(
        self,
    ) -> None:
        summary = self.update_summary

        self.assertEqual(
            summary.state_count,
            1024,
        )

        self.assertEqual(
            summary.cover_relations_checked,
            5120,
        )

        self.assertEqual(
            summary.observed_masks_checked,
            1024,
        )

        self.assertEqual(
            summary.update_checks,
            5120 * 1024,
        )

        self.assertEqual(
            summary.violations,
            0,
        )

    def test_absorption_metrics_are_exhaustively_monotone(
        self,
    ) -> None:
        summary = self.absorption_summary

        self.assertEqual(
            summary.strict_comparable_pairs,
            58025,
        )

        self.assertEqual(
            summary.expected_time_checks,
            58025,
        )

        self.assertEqual(
            summary.completion_cdf_checks,
            58025 * 5,
        )

        self.assertEqual(
            summary.quantile_checks,
            58025 * 4,
        )

        self.assertLessEqual(
            summary
            .maximum_expected_time_violation,
            1e-12,
        )

        self.assertLessEqual(
            summary
            .maximum_completion_cdf_violation,
            1e-12,
        )

        self.assertEqual(
            summary.maximum_quantile_violation,
            0,
        )

    def test_representative_stochastic_order(
        self,
    ) -> None:
        lower = {9}
        upper = {0, 9}

        self.assertLessEqual(
            expected_remaining_draws(lower),
            expected_remaining_draws(upper),
        )

        for horizon in (1, 2, 3, 5, 10):
            self.assertGreaterEqual(
                completion_probability_within(
                    lower,
                    horizon,
                ),
                completion_probability_within(
                    upper,
                    horizon,
                ),
            )

        lower_quantiles = absorption_quantiles(
            lower
        )

        upper_quantiles = absorption_quantiles(
            upper
        )

        for probability in lower_quantiles:
            self.assertLessEqual(
                lower_quantiles[probability],
                upper_quantiles[probability],
            )

    def test_variance_is_not_a_monotone_consequence(
        self,
    ) -> None:
        self.assertTrue(
            {9}.issubset({0, 9})
        )

        self.assertGreater(
            variance_remaining_draws({9}),
            variance_remaining_draws(
                {0, 9}
            ),
        )

    def test_mask_validation_and_update(
        self,
    ) -> None:
        lower = (1 << 0) | (1 << 9)
        upper = lower | (1 << 4)
        observed = (1 << 0) | (1 << 4)

        lower_next = next_missing_mask(
            lower,
            observed,
        )

        upper_next = next_missing_mask(
            upper,
            observed,
        )

        self.assertEqual(
            lower_next,
            1 << 9,
        )

        self.assertEqual(
            upper_next,
            1 << 9,
        )

        self.assertTrue(
            is_subset_mask(
                lower_next,
                upper_next,
            )
        )

        with self.assertRaises(TypeError):
            next_missing_mask(
                1.5,
                0,
            )

        with self.assertRaises(ValueError):
            next_missing_mask(
                ALL_DIGITS_MASK + 1,
                0,
            )


if __name__ == "__main__":
    unittest.main()
