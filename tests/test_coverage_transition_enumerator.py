from __future__ import annotations

import unittest

from strategies.coverage_markov import (
    transition_distribution,
)
from strategies.coverage_transition_enumerator import (
    ALL_DIGITS_MASK,
    TOTAL_DRAW_COMBINATIONS,
    all_digit_states,
    draw_digit_mask_counts,
    mask_to_state,
    number_digit_mask,
    transition_count_distribution,
    transition_probability_distribution,
)


class CoverageTransitionEnumeratorTests(
    unittest.TestCase
):
    def test_number_masks_preserve_leading_zero(
        self,
    ) -> None:
        self.assertEqual(
            number_digit_mask(1),
            (1 << 0) | (1 << 1),
        )

        self.assertEqual(
            number_digit_mask(9),
            (1 << 0) | (1 << 9),
        )

        self.assertEqual(
            number_digit_mask(11),
            1 << 1,
        )

        self.assertEqual(
            number_digit_mask(90),
            (1 << 9) | (1 << 0),
        )

    def test_draw_mask_counts_cover_sample_space(
        self,
    ) -> None:
        distribution = draw_digit_mask_counts()

        self.assertEqual(
            sum(
                count
                for _, count in distribution
            ),
            TOTAL_DRAW_COMBINATIONS,
        )

        self.assertTrue(
            all(
                0 <= mask <= ALL_DIGITS_MASK
                for mask, _ in distribution
            )
        )

        self.assertTrue(
            all(
                count > 0
                for _, count in distribution
            )
        )

    def test_state_space_contains_1024_states(
        self,
    ) -> None:
        states = all_digit_states()

        self.assertEqual(
            len(states),
            1024,
        )

        self.assertEqual(
            len(set(states)),
            1024,
        )

        self.assertEqual(
            states[0],
            frozenset(),
        )

        self.assertEqual(
            states[-1],
            frozenset(range(10)),
        )

    def test_complete_state_is_absorbing(
        self,
    ) -> None:
        counts = (
            transition_count_distribution(())
        )

        self.assertEqual(
            counts,
            {
                frozenset():
                TOTAL_DRAW_COMBINATIONS,
            },
        )

    def test_transitions_only_remove_digits(
        self,
    ) -> None:
        current = frozenset(
            {2, 5, 9}
        )

        distribution = (
            transition_probability_distribution(
                current
            )
        )

        self.assertAlmostEqual(
            sum(distribution.values()),
            1.0,
            places=15,
        )

        for next_state in distribution:
            self.assertTrue(
                next_state.issubset(current)
            )

    def test_all_states_match_markov_kernel(
        self,
    ) -> None:
        tolerance = 1e-12

        for mask in range(
            ALL_DIGITS_MASK + 1
        ):
            state = mask_to_state(mask)

            enumerated = (
                transition_probability_distribution(
                    state
                )
            )

            modelled = transition_distribution(
                state
            )

            self.assertEqual(
                set(enumerated),
                set(modelled),
                msg=(
                    "Supporto diverso per lo stato "
                    f"{sorted(state)}."
                ),
            )

            for next_state in enumerated:
                self.assertAlmostEqual(
                    enumerated[next_state],
                    modelled[next_state],
                    delta=tolerance,
                    msg=(
                        "Probabilità diversa per "
                        f"{sorted(state)} -> "
                        f"{sorted(next_state)}."
                    ),
                )


if __name__ == "__main__":
    unittest.main()
