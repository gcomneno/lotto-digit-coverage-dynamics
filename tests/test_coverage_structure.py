from __future__ import annotations

import math
import unittest

from strategies.coverage_markov import (
    expected_remaining_draws,
)
from strategies.coverage_structure import (
    StateSymmetryClass,
    all_digit_states,
    allowed_number_count_closed_form,
    allowed_number_count_enumerated,
    canonical_relabeling,
    group_nonempty_states_by_symmetry,
    relabel_state,
    state_symmetry_class,
    verify_structural_symmetry,
)


class CoverageStructureTests(
    unittest.TestCase
):
    def test_closed_form_matches_all_forbidden_states(
        self,
    ) -> None:
        for forbidden in all_digit_states():
            with self.subTest(
                forbidden=sorted(forbidden)
            ):
                self.assertEqual(
                    allowed_number_count_closed_form(
                        forbidden
                    ),
                    allowed_number_count_enumerated(
                        forbidden
                    ),
                )

    def test_zero_becomes_distinct_when_nine_is_forbidden(
        self,
    ) -> None:
        self.assertEqual(
            allowed_number_count_closed_form(
                {0, 1}
            ),
            56,
        )

        self.assertEqual(
            allowed_number_count_closed_form(
                {2, 3}
            ),
            56,
        )

        self.assertEqual(
            allowed_number_count_closed_form(
                {0, 9}
            ),
            64,
        )

        self.assertEqual(
            allowed_number_count_closed_form(
                {1, 9}
            ),
            63,
        )

    def test_nonempty_states_form_twenty_seven_classes(
        self,
    ) -> None:
        groups = (
            group_nonempty_states_by_symmetry()
        )

        self.assertEqual(len(groups), 27)

        expected_classes = {
            *(
                StateSymmetryClass(
                    "no-nine",
                    count,
                )
                for count in range(1, 10)
            ),
            *(
                StateSymmetryClass(
                    "nine-no-zero",
                    count,
                )
                for count in range(9)
            ),
            *(
                StateSymmetryClass(
                    "zero-nine",
                    count,
                )
                for count in range(9)
            ),
        }

        self.assertEqual(
            set(groups),
            expected_classes,
        )

        self.assertEqual(
            sum(
                len(states)
                for states in groups.values()
            ),
            1023,
        )

    def test_class_multiplicities_match_combinatorics(
        self,
    ) -> None:
        groups = (
            group_nonempty_states_by_symmetry()
        )

        for symmetry_class, states in groups.items():
            if (
                symmetry_class.family
                == "no-nine"
            ):
                expected = math.comb(
                    9,
                    symmetry_class
                    .exchangeable_count,
                )
            else:
                expected = math.comb(
                    8,
                    symmetry_class
                    .exchangeable_count,
                )

            with self.subTest(
                symmetry_class=symmetry_class
            ):
                self.assertEqual(
                    len(states),
                    expected,
                )

    def test_canonical_relabeling_covers_every_state(
        self,
    ) -> None:
        for state in all_digit_states():
            mapping = canonical_relabeling(
                state
            )

            symmetry_class = (
                state_symmetry_class(state)
            )

            self.assertEqual(
                set(mapping),
                set(state),
            )

            self.assertEqual(
                len(set(mapping.values())),
                len(mapping),
            )

            self.assertEqual(
                relabel_state(
                    state,
                    mapping,
                ),
                symmetry_class.canonical_state,
            )

    def test_transition_kernel_is_exhaustively_equivariant(
        self,
    ) -> None:
        summary = verify_structural_symmetry()

        self.assertEqual(
            summary.forbidden_states_checked,
            1024,
        )

        self.assertEqual(
            summary.markov_states_checked,
            1024,
        )

        self.assertEqual(
            summary.nonempty_symmetry_classes,
            27,
        )

        self.assertGreater(
            summary.transition_entries_compared,
            0,
        )

        self.assertLessEqual(
            summary.maximum_transition_error,
            1e-12,
        )

    def test_absorption_metrics_follow_classes_but_not_count_alone(
        self,
    ) -> None:
        self.assertAlmostEqual(
            expected_remaining_draws(
                {0, 1}
            ),
            expected_remaining_draws(
                {2, 3}
            ),
            places=12,
        )

        self.assertAlmostEqual(
            expected_remaining_draws(
                {1, 9}
            ),
            expected_remaining_draws(
                {8, 9}
            ),
            places=12,
        )

        self.assertNotAlmostEqual(
            expected_remaining_draws(
                {0, 9}
            ),
            expected_remaining_draws(
                {1, 9}
            ),
            places=12,
        )


if __name__ == "__main__":
    unittest.main()
