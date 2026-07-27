from __future__ import annotations

import unittest

from analyze_missing_pair_numbers import (
    candidate_hit_probability,
    enrich,
    pair_numbers,
    select_observations,
    summarize,
)


def observation(
    *,
    target: int = 101,
    pair: tuple[int, int] = (2, 5),
    probability: float = 0.4502,
    numbers: tuple[int, ...] = (1, 3, 4, 6, 7),
    completed: bool = False,
) -> dict[str, object]:
    return {
        "target_draw": target,
        "target_date": "2025-06-26",
        "wheel": "Bari",
        "wheel_order": 1,
        "missing_digits": list(pair),
        "completion_probability_within": {
            "1": probability,
        },
        "target_numbers": list(numbers),
        "completed": completed,
    }


class AnalyzeMissingPairNumbersTests(unittest.TestCase):
    def test_pair_numbers_in_both_orders(self) -> None:
        self.assertEqual(
            pair_numbers((2, 5)),
            (25, 52),
        )

    def test_pair_with_leading_zero(self) -> None:
        self.assertEqual(
            pair_numbers((0, 5)),
            (5, 50),
        )

    def test_invalid_number_above_ninety_is_removed(self) -> None:
        self.assertEqual(
            pair_numbers((8, 9)),
            (89,),
        )

    def test_two_candidate_probability(self) -> None:
        self.assertAlmostEqual(
            candidate_hit_probability(2),
            0.10861423220973787,
        )

    def test_one_candidate_probability(self) -> None:
        self.assertAlmostEqual(
            candidate_hit_probability(1),
            5 / 90,
        )

    def test_enrich_detects_pair_number(self) -> None:
        result = enrich(
            observation(
                numbers=(7, 25, 40, 63, 81),
                completed=True,
            )
        )

        self.assertEqual(
            result["candidate_hits"],
            (25,),
        )

    def test_pair_number_requires_completed_cycle(self) -> None:
        with self.assertRaises(ValueError):
            enrich(
                observation(
                    numbers=(7, 52, 40, 63, 81),
                    completed=False,
                )
            )

    def test_selects_only_visible_4502_group(self) -> None:
        selected = select_observations(
            (
                observation(
                    target=101,
                    probability=0.4502,
                ),
                observation(
                    target=102,
                    probability=0.2946,
                ),
            ),
            group="45.02",
            pair_filter=None,
            wheel=None,
            start_target=None,
            end_target=None,
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(
            selected[0]["target_draw"],
            101,
        )

    def test_summary_compares_expected_and_observed_hits(
        self,
    ) -> None:
        rows = [
            enrich(
                observation(
                    target=101,
                    numbers=(25, 7, 8, 9, 10),
                    completed=True,
                )
            ),
            enrich(
                observation(
                    target=102,
                    numbers=(1, 3, 4, 6, 7),
                    completed=False,
                )
            ),
        ]

        result = summarize(rows)

        self.assertEqual(result["cases"], 2)
        self.assertEqual(
            result["observed_pair_hits"],
            1,
        )
        self.assertAlmostEqual(
            result["expected_pair_hits"],
            2 * candidate_hit_probability(2),
        )


if __name__ == "__main__":
    unittest.main()
