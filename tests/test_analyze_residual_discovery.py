from __future__ import annotations

import unittest
from dataclasses import replace

from analyze_residual_discovery import (
    GroupResult,
    age_bucket,
    apply_family_q_values,
    benjamini_hochberg,
    build_family_groups,
    compute_group_result,
    observation_features,
    same_nonzero_direction,
    split_target_sets,
)


def observation(
    target: int,
    completed: bool,
    *,
    probability: float = 0.5,
    wheel: str = "Bari",
    missing_digits: list[int] | None = None,
    cycle_age: int = 2,
) -> dict[str, object]:
    if missing_digits is None:
        missing_digits = [2, 5]

    return {
        "target_draw": target,
        "target_date": f"2023-01-{target:02d}",
        "source_latest_draw": target - 1,
        "source_latest_date": (
            f"2023-01-{target - 1:02d}"
        ),
        "wheel": wheel,
        "wheel_order": 1,
        "cycle_age": cycle_age,
        "missing_digits": missing_digits,
        "completion_probability_within": {
            "1": probability,
        },
        "expected_remaining_draws": 2.0,
        "target_numbers": [1, 2, 3, 4, 5],
        "target_digits": [0, 1, 2, 3, 4, 5],
        "completed": completed,
        "remaining_before_reset": (
            []
            if completed
            else missing_digits
        ),
    }


def result(
    *,
    cases: int = 30,
    q_value: float = 0.01,
    stable: bool = True,
) -> GroupResult:
    return GroupResult(
        family="wheel",
        group="Bari",
        cases=cases,
        expected=10.0,
        observed=12,
        expected_rate=1 / 3,
        observed_rate=0.4,
        delta_rate=0.4 - 1 / 3,
        residual_sum=2.0,
        variance_sum=5.0,
        z_score=0.9,
        p_two_sided=0.01,
        q_value=q_value,
        first_cases=15,
        first_residual=1.0,
        second_cases=15,
        second_residual=1.0,
        stable_direction=stable,
        qualifies_for_promotion=False,
    )


class ResidualDiscoveryTests(unittest.TestCase):
    def test_observation_features_follow_protocol(
        self,
    ) -> None:
        features = observation_features(
            observation(
                20,
                False,
                wheel="Milano",
                missing_digits=[9],
                cycle_age=6,
            )
        )

        self.assertEqual(
            features["wheel"],
            "Milano",
        )
        self.assertEqual(
            features["missing_count"],
            "1",
        )
        self.assertEqual(
            features["single_missing_digit"],
            "9",
        )
        self.assertEqual(
            features["contains_nine"],
            "yes",
        )
        self.assertEqual(
            features["cycle_age"],
            "5+",
        )
        self.assertEqual(
            features["exact_missing_state"],
            "{9}",
        )

    def test_age_bucket_is_predefined(
        self,
    ) -> None:
        self.assertEqual(age_bucket(0), "0")
        self.assertEqual(age_bucket(4), "4")
        self.assertEqual(age_bucket(5), "5+")
        self.assertEqual(age_bucket(20), "5+")

        with self.assertRaises(ValueError):
            age_bucket(-1)

    def test_temporal_split_uses_unique_targets(
        self,
    ) -> None:
        rows = [
            observation(20, False, wheel="Bari"),
            observation(20, True, wheel="Roma"),
            observation(21, False, wheel="Bari"),
            observation(22, True, wheel="Bari"),
            observation(23, False, wheel="Bari"),
        ]

        first, second = split_target_sets(rows)

        self.assertEqual(first, {20, 21})
        self.assertEqual(second, {22, 23})

    def test_exact_states_require_thirty_cases(
        self,
    ) -> None:
        rows = [
            observation(
                index,
                False,
                missing_digits=[1],
            )
            for index in range(1, 30)
        ]

        rows.extend(
            observation(
                index,
                False,
                missing_digits=[2],
            )
            for index in range(30, 60)
        )

        groups = build_family_groups(
            rows,
            "exact_missing_state",
        )

        self.assertNotIn("{1}", groups)
        self.assertEqual(
            len(groups["{2}"]),
            30,
        )

    def test_benjamini_hochberg_is_monotonic(
        self,
    ) -> None:
        adjusted = benjamini_hochberg(
            (0.01, 0.04, 0.03)
        )

        self.assertAlmostEqual(
            adjusted[0],
            0.03,
        )
        self.assertAlmostEqual(
            adjusted[1],
            0.04,
        )
        self.assertAlmostEqual(
            adjusted[2],
            0.04,
        )

    def test_group_result_uses_expected_probability(
        self,
    ) -> None:
        rows = [
            observation(
                20,
                False,
                probability=0.25,
            ),
            observation(
                21,
                True,
                probability=0.75,
            ),
        ]

        computed = compute_group_result(
            family="wheel",
            group="Bari",
            observations=rows,
            first_targets={20},
            second_targets={21},
        )

        self.assertEqual(computed.cases, 2)
        self.assertEqual(computed.expected, 1.0)
        self.assertEqual(computed.observed, 1)
        self.assertAlmostEqual(
            computed.residual_sum,
            0.0,
        )
        self.assertAlmostEqual(
            computed.z_score,
            0.0,
        )

    def test_stability_requires_same_nonzero_sign(
        self,
    ) -> None:
        self.assertTrue(
            same_nonzero_direction(
                1.0,
                2.0,
            )
        )
        self.assertTrue(
            same_nonzero_direction(
                -1.0,
                -0.5,
            )
        )
        self.assertFalse(
            same_nonzero_direction(
                1.0,
                -1.0,
            )
        )
        self.assertFalse(
            same_nonzero_direction(
                0.0,
                1.0,
            )
        )

    def test_promotion_requires_all_conditions(
        self,
    ) -> None:
        base = result()

        qualified = apply_family_q_values(
            (
                replace(
                    base,
                    p_two_sided=0.01,
                ),
            )
        )[0]

        self.assertTrue(
            qualified.qualifies_for_promotion
        )

        too_small = apply_family_q_values(
            (
                replace(
                    base,
                    cases=29,
                    p_two_sided=0.01,
                ),
            )
        )[0]

        unstable = apply_family_q_values(
            (
                replace(
                    base,
                    stable_direction=False,
                    p_two_sided=0.01,
                ),
            )
        )[0]

        not_significant = apply_family_q_values(
            (
                replace(
                    base,
                    p_two_sided=0.10,
                ),
            )
        )[0]

        self.assertFalse(
            too_small.qualifies_for_promotion
        )
        self.assertFalse(
            unstable.qualifies_for_promotion
        )
        self.assertFalse(
            not_significant.qualifies_for_promotion
        )


if __name__ == "__main__":
    unittest.main()
