from __future__ import annotations

import unittest

from analyze_frozen_coverage_rule import (
    poisson_binomial_upper_tail,
    wilson_interval,
)


class FrozenCoverageRuleTests(unittest.TestCase):
    def test_poisson_binomial_tail(self) -> None:
        probability = poisson_binomial_upper_tail(
            (0.5, 0.5),
            observed_hits=1,
        )

        self.assertAlmostEqual(
            probability,
            0.75,
            places=12,
        )

    def test_poisson_binomial_all_hits(self) -> None:
        probability = poisson_binomial_upper_tail(
            (0.5, 0.5),
            observed_hits=2,
        )

        self.assertAlmostEqual(
            probability,
            0.25,
            places=12,
        )

    def test_wilson_interval_contains_observed_rate(self) -> None:
        lower, upper = wilson_interval(
            hits=60,
            total=100,
        )

        self.assertLess(lower, 0.60)
        self.assertGreater(upper, 0.60)


if __name__ == "__main__":
    unittest.main()
