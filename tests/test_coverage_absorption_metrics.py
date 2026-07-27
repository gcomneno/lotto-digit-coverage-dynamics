from __future__ import annotations

import math
import unittest

from strategies.coverage_completion import (
    exact_completion_probability,
)
from strategies.coverage_markov import (
    absorption_probability_mass,
    absorption_quantiles,
    completion_probability_within,
    expected_remaining_draws,
    maturity_metrics,
    second_moment_remaining_draws,
    variance_remaining_draws,
)


class CoverageAbsorptionMetricsTests(
    unittest.TestCase
):
    def test_complete_state_has_zero_time(
        self,
    ) -> None:
        self.assertEqual(
            expected_remaining_draws(()),
            0.0,
        )
        self.assertEqual(
            second_moment_remaining_draws(()),
            0.0,
        )
        self.assertEqual(
            variance_remaining_draws(()),
            0.0,
        )
        self.assertEqual(
            absorption_probability_mass(
                (),
                10,
            ),
            {0: 1.0},
        )
        self.assertEqual(
            absorption_quantiles(
                (),
                (0.50, 0.95),
            ),
            {
                0.50: 0,
                0.95: 0,
            },
        )

    def test_single_digit_matches_geometric_moments(
        self,
    ) -> None:
        probability = (
            exact_completion_probability({9})
        )

        expected_second_moment = (
            2.0 - probability
        ) / probability**2

        expected_variance = (
            1.0 - probability
        ) / probability**2

        self.assertAlmostEqual(
            second_moment_remaining_draws({9}),
            expected_second_moment,
            places=10,
        )

        self.assertAlmostEqual(
            variance_remaining_draws({9}),
            expected_variance,
            places=10,
        )

    def test_probability_mass_matches_cdf(
        self,
    ) -> None:
        state = {3, 9}
        mass = absorption_probability_mass(
            state,
            25,
        )

        self.assertAlmostEqual(
            sum(mass.values()),
            completion_probability_within(
                state,
                25,
            ),
            places=12,
        )

        self.assertTrue(
            all(
                probability >= 0.0
                for probability in mass.values()
            )
        )

    def test_truncated_mass_recovers_moments(
        self,
    ) -> None:
        state = {3, 9}
        mass = absorption_probability_mass(
            state,
            250,
        )

        mean = sum(
            draw * probability
            for draw, probability in mass.items()
        )

        second_moment = sum(
            draw**2 * probability
            for draw, probability in mass.items()
        )

        self.assertAlmostEqual(
            mean,
            expected_remaining_draws(state),
            places=9,
        )

        self.assertAlmostEqual(
            second_moment,
            second_moment_remaining_draws(
                state
            ),
            places=8,
        )

    def test_quantiles_are_minimal_horizons(
        self,
    ) -> None:
        state = {2, 5, 9}
        probabilities = (
            0.50,
            0.90,
            0.95,
            0.99,
        )

        quantiles = absorption_quantiles(
            state,
            probabilities,
        )

        self.assertEqual(
            list(quantiles.values()),
            sorted(quantiles.values()),
        )

        for probability, draw in (
            quantiles.items()
        ):
            self.assertGreaterEqual(
                completion_probability_within(
                    state,
                    draw,
                ),
                probability,
            )

            self.assertLess(
                completion_probability_within(
                    state,
                    draw - 1,
                ),
                probability,
            )

    def test_geometric_quantile_matches_formula(
        self,
    ) -> None:
        state = {9}
        probability = (
            exact_completion_probability(state)
        )

        quantile_probability = 0.95

        expected = math.ceil(
            math.log(
                1.0 - quantile_probability
            )
            / math.log(
                1.0 - probability
            )
        )

        actual = absorption_quantiles(
            state,
            (quantile_probability,),
        )

        self.assertEqual(
            actual[quantile_probability],
            expected,
        )

    def test_maturity_metrics_include_absorption_data(
        self,
    ) -> None:
        metrics = maturity_metrics(
            {3, 9},
            horizons=(1, 3, 5),
            quantiles=(0.50, 0.95),
        )

        self.assertGreater(
            metrics[
                "second_moment_remaining_draws"
            ],
            0.0,
        )

        self.assertGreaterEqual(
            metrics[
                "variance_remaining_draws"
            ],
            0.0,
        )

        self.assertEqual(
            set(
                metrics[
                    "absorption_quantiles"
                ]
            ),
            {0.50, 0.95},
        )

    def test_invalid_arguments_are_rejected(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            absorption_probability_mass(
                {9},
                -1,
            )

        with self.assertRaises(ValueError):
            absorption_quantiles(
                {9},
                (0.0,),
            )

        with self.assertRaises(ValueError):
            absorption_quantiles(
                {9},
                (1.0,),
            )

        with self.assertRaises(ValueError):
            absorption_quantiles(
                {9},
                (0.50,),
                max_draws=0,
            )


if __name__ == "__main__":
    unittest.main()
