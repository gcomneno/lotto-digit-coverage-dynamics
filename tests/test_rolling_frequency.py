from __future__ import annotations

import unittest
from unittest.mock import patch

from strategies.lotto_repository import DrawSnapshot
from strategies.rolling_frequency import (
    WalkForwardObservation,
    build_walk_forward_experiment,
    build_walk_forward_observation,
    build_walk_forward_observations,
    evaluate_candidate_numbers,
    generate_candidate_numbers,
    merge_draw_histories,
    rolling_digit_frequency,
    simulate_equal_size_random_baseline,
    summarize_walk_forward_observations,
)


def draw(
    number: int,
    values: tuple[int, ...],
    *,
    wheel: str = "Venezia",
    wheel_order: int = 10,
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=f"2026-01-{number:02d}",
        wheel=wheel,
        wheel_order=wheel_order,
        numbers=values,
    )



def observation(
    *,
    target_draw: int,
    target_date: str,
    candidate_numbers: tuple[int, ...],
    hit_numbers: tuple[int, ...],
    ambo_hits: tuple[tuple[int, int], ...],
    window_size: int = 6,
    target_numbers: tuple[int, ...] = (
        11,
        22,
        33,
        44,
        55,
    ),
) -> WalkForwardObservation:
    return WalkForwardObservation(
        wheel="Venezia",
        wheel_order=10,
        window_size=window_size,
        history_draw_numbers=tuple(
            range(
                target_draw - window_size,
                target_draw,
            )
        ),
        history_start_draw=target_draw - window_size,
        history_end_draw=target_draw - 1,
        target_draw=target_draw,
        target_date=target_date,
        target_numbers=target_numbers,
        most_frequent_digits=frozenset({8}),
        missing_digits=frozenset({5, 7}),
        candidate_numbers=candidate_numbers,
        hit_numbers=hit_numbers,
        ambo_hits=ambo_hits,
        covered_ambo_count=(
            len(candidate_numbers)
            * (len(candidate_numbers) - 1)
            // 2
        ),
        hit_ambo_count=len(ambo_hits),
    )


class RollingDigitFrequencyTests(unittest.TestCase):
    def test_uses_only_the_last_requested_draws(self) -> None:
        analysis = rolling_digit_frequency(
            (
                draw(1, (66, 67, 68, 69, 76)),
                draw(2, (11, 22, 33, 44, 55)),
            ),
            window_size=1,
        )

        self.assertEqual(analysis.draw_numbers, (2,))
        self.assertEqual(
            analysis.most_frequent_digits,
            frozenset({1, 2, 3, 4, 5}),
        )
        self.assertEqual(analysis.maximum_count, 2)

    def test_leading_zero_is_counted(self) -> None:
        analysis = rolling_digit_frequency(
            (
                draw(1, (1, 23, 45, 67, 89)),
            ),
            window_size=1,
        )

        self.assertEqual(
            analysis.digit_counts,
            (1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        )
        self.assertEqual(
            analysis.most_frequent_digits,
            frozenset(range(10)),
        )

    def test_retains_every_digit_tied_for_maximum(self) -> None:
        analysis = rolling_digit_frequency(
            (
                draw(1, (11, 22, 34, 56, 78)),
            ),
            window_size=1,
        )

        self.assertEqual(
            analysis.most_frequent_digits,
            frozenset({1, 2}),
        )

    def test_rejects_non_positive_window(self) -> None:
        with self.assertRaises(ValueError):
            rolling_digit_frequency(
                (draw(1, (11, 22, 33, 44, 55)),),
                window_size=0,
            )

    def test_rejects_window_larger_than_history(self) -> None:
        with self.assertRaises(ValueError):
            rolling_digit_frequency(
                (draw(1, (11, 22, 33, 44, 55)),),
                window_size=2,
            )

    def test_rejects_mixed_wheels(self) -> None:
        with self.assertRaises(ValueError):
            rolling_digit_frequency(
                (
                    draw(1, (11, 22, 33, 44, 55)),
                    draw(
                        2,
                        (11, 22, 33, 44, 55),
                        wheel="Roma",
                        wheel_order=8,
                    ),
                ),
                window_size=2,
            )


class CandidateNumberTests(unittest.TestCase):
    def test_generates_present_missing_pairs_and_gemello(self) -> None:
        self.assertEqual(
            generate_candidate_numbers(
                most_frequent_digits=frozenset({6}),
                missing_digits=frozenset({0, 1, 3, 7}),
            ),
            (6, 16, 36, 60, 61, 63, 66, 67, 76),
        )

    def test_excludes_zero_and_values_above_ninety(self) -> None:
        self.assertEqual(
            generate_candidate_numbers(
                most_frequent_digits=frozenset({0, 9}),
                missing_digits=frozenset({5, 6}),
            ),
            (5, 6, 50, 59, 60, 69),
        )

    def test_deduplicates_overlapping_rules(self) -> None:
        self.assertEqual(
            generate_candidate_numbers(
                most_frequent_digits=frozenset({1}),
                missing_digits=frozenset({1}),
            ),
            (11,),
        )

    def test_rejects_invalid_digits(self) -> None:
        with self.assertRaises(ValueError):
            generate_candidate_numbers(
                most_frequent_digits=frozenset({10}),
                missing_digits=frozenset({1}),
            )


class CandidateOutcomeTests(unittest.TestCase):
    def test_counts_hits_and_ambi_on_the_target_wheel(self) -> None:
        outcome = evaluate_candidate_numbers(
            candidate_numbers=(11, 16, 61, 66),
            target=draw(
                3,
                (61, 22, 11, 33, 44),
            ),
        )

        self.assertEqual(
            outcome.candidate_numbers,
            (11, 16, 61, 66),
        )
        self.assertEqual(
            outcome.hit_numbers,
            (11, 61),
        )
        self.assertEqual(
            outcome.ambo_hits,
            ((11, 61),),
        )
        self.assertEqual(outcome.covered_ambo_count, 6)
        self.assertEqual(outcome.hit_ambo_count, 1)

    def test_deduplicates_candidate_input(self) -> None:
        outcome = evaluate_candidate_numbers(
            candidate_numbers=(11, 11, 61),
            target=draw(
                3,
                (61, 22, 11, 33, 44),
            ),
        )

        self.assertEqual(
            outcome.candidate_numbers,
            (11, 61),
        )
        self.assertEqual(outcome.covered_ambo_count, 1)

    def test_rejects_invalid_candidate_numbers(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_candidate_numbers(
                candidate_numbers=(0, 11),
                target=draw(
                    3,
                    (61, 22, 11, 33, 44),
                ),
            )


class WalkForwardObservationTests(unittest.TestCase):
    def test_builds_selection_only_from_pre_target_history(
        self,
    ) -> None:
        observation = build_walk_forward_observation(
            (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
                draw(
                    2,
                    (11, 12, 13, 14, 15),
                ),
                draw(
                    3,
                    (61, 11, 22, 33, 44),
                ),
            ),
            target_index=2,
            window_size=1,
        )

        self.assertIsNotNone(observation)

        assert observation is not None

        self.assertEqual(
            observation.history_draw_numbers,
            (2,),
        )
        self.assertEqual(
            observation.history_end_draw,
            2,
        )
        self.assertEqual(
            observation.target_draw,
            3,
        )
        self.assertEqual(
            observation.target_numbers,
            (61, 11, 22, 33, 44),
        )
        self.assertEqual(
            observation.most_frequent_digits,
            frozenset({1}),
        )
        self.assertEqual(
            observation.missing_digits,
            frozenset({0, 6, 7, 8, 9}),
        )
        self.assertEqual(
            observation.candidate_numbers,
            (
                1,
                10,
                11,
                16,
                17,
                18,
                19,
                61,
                71,
                81,
            ),
        )
        self.assertEqual(
            observation.hit_numbers,
            (11, 61),
        )
        self.assertEqual(
            observation.ambo_hits,
            ((11, 61),),
        )

    def test_target_values_cannot_change_the_selection(
        self,
    ) -> None:
        common_history = (
            draw(
                1,
                (1, 23, 45, 67, 89),
            ),
            draw(
                2,
                (11, 12, 13, 14, 15),
            ),
        )

        first = build_walk_forward_observation(
            common_history
            + (
                draw(
                    3,
                    (61, 11, 22, 33, 44),
                ),
            ),
            target_index=2,
            window_size=1,
        )
        second = build_walk_forward_observation(
            common_history
            + (
                draw(
                    3,
                    (20, 30, 40, 50, 60),
                ),
            ),
            target_index=2,
            window_size=1,
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)

        assert first is not None
        assert second is not None

        self.assertEqual(
            first.most_frequent_digits,
            second.most_frequent_digits,
        )
        self.assertEqual(
            first.missing_digits,
            second.missing_digits,
        )
        self.assertEqual(
            first.candidate_numbers,
            second.candidate_numbers,
        )
        self.assertNotEqual(
            first.hit_numbers,
            second.hit_numbers,
        )

    def test_skips_left_censored_pre_target_state(
        self,
    ) -> None:
        observation = build_walk_forward_observation(
            (
                draw(
                    1,
                    (11, 22, 33, 44, 55),
                ),
                draw(
                    2,
                    (61, 11, 22, 33, 44),
                ),
            ),
            target_index=1,
            window_size=1,
        )

        self.assertIsNone(observation)

    def test_skips_just_completed_zero_age_state(
        self,
    ) -> None:
        observation = build_walk_forward_observation(
            (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
                draw(
                    2,
                    (61, 11, 22, 33, 44),
                ),
            ),
            target_index=1,
            window_size=1,
        )

        self.assertIsNone(observation)

    def test_skips_history_shorter_than_window(
        self,
    ) -> None:
        observation = build_walk_forward_observation(
            (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
                draw(
                    2,
                    (61, 11, 22, 33, 44),
                ),
            ),
            target_index=1,
            window_size=2,
        )

        self.assertIsNone(observation)

    def test_rejects_target_index_outside_sequence(
        self,
    ) -> None:
        draws = (
            draw(
                1,
                (1, 23, 45, 67, 89),
            ),
        )

        with self.assertRaises(IndexError):
            build_walk_forward_observation(
                draws,
                target_index=-1,
                window_size=1,
            )

        with self.assertRaises(IndexError):
            build_walk_forward_observation(
                draws,
                target_index=1,
                window_size=1,
            )


class WalkForwardSeriesTests(unittest.TestCase):
    def test_builds_every_eligible_target_in_order(
        self,
    ) -> None:
        observations = build_walk_forward_observations(
            (
                draw(1, (1, 23, 45, 67, 89)),
                draw(2, (11, 12, 13, 14, 15)),
                draw(3, (61, 11, 22, 33, 44)),
                draw(4, (10, 16, 17, 18, 19)),
            ),
            window_size=1,
        )

        self.assertEqual(
            tuple(
                observation.target_draw
                for observation in observations
            ),
            (3, 4),
        )
        self.assertEqual(
            tuple(
                observation.history_end_draw
                for observation in observations
            ),
            (2, 3),
        )

    def test_skips_non_synchronized_and_zero_age_targets(
        self,
    ) -> None:
        observations = build_walk_forward_observations(
            (
                draw(1, (11, 22, 33, 44, 55)),
                draw(2, (1, 23, 45, 67, 89)),
                draw(3, (11, 12, 13, 14, 15)),
                draw(4, (61, 11, 22, 33, 44)),
            ),
            window_size=1,
        )

        self.assertEqual(
            tuple(
                observation.target_draw
                for observation in observations
            ),
            (4,),
        )

    def test_returns_empty_when_no_target_is_eligible(
        self,
    ) -> None:
        observations = build_walk_forward_observations(
            (
                draw(1, (11, 22, 33, 44, 55)),
            ),
            window_size=3,
        )

        self.assertEqual(observations, ())

    def test_rejects_non_positive_window(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            build_walk_forward_observations(
                (
                    draw(1, (1, 23, 45, 67, 89)),
                ),
                window_size=0,
            )

    def test_series_does_not_rebuild_full_state_per_target(
        self,
    ) -> None:
        draws = (
            draw(
                1,
                (1, 23, 45, 67, 89),
            ),
            draw(
                2,
                (11, 12, 13, 14, 15),
            ),
            draw(
                3,
                (61, 11, 22, 33, 44),
            ),
        )

        with patch(
            "strategies.rolling_frequency."
            "current_coverage_state",
            side_effect=AssertionError(
                "ricostruzione completa non ammessa"
            ),
        ):
            observations = (
                build_walk_forward_observations(
                    draws,
                    window_size=1,
                )
            )

        self.assertEqual(
            tuple(
                observation.target_draw
                for observation in observations
            ),
            (3,),
        )

    def test_rejects_mixed_wheels_before_iteration(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            build_walk_forward_observations(
                (
                    draw(1, (1, 23, 45, 67, 89)),
                    draw(
                        2,
                        (11, 22, 33, 44, 55),
                        wheel="Roma",
                        wheel_order=8,
                    ),
                ),
                window_size=1,
            )


class WalkForwardExperimentTests(unittest.TestCase):
    def test_aggregates_windows_and_wheels_deterministically(
        self,
    ) -> None:
        draws_by_wheel = {
            "Roma": (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                    wheel="Roma",
                    wheel_order=8,
                ),
                draw(
                    2,
                    (11, 12, 13, 14, 15),
                    wheel="Roma",
                    wheel_order=8,
                ),
                draw(
                    3,
                    (61, 11, 22, 33, 44),
                    wheel="Roma",
                    wheel_order=8,
                ),
            ),
            "Bari": (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                    wheel="Bari",
                    wheel_order=1,
                ),
                draw(
                    2,
                    (11, 12, 13, 14, 15),
                    wheel="Bari",
                    wheel_order=1,
                ),
                draw(
                    3,
                    (61, 11, 22, 33, 44),
                    wheel="Bari",
                    wheel_order=1,
                ),
            ),
        }

        experiment = build_walk_forward_experiment(
            draws_by_wheel,
            window_sizes=(2, 1),
        )

        self.assertEqual(
            tuple(experiment),
            (1, 2),
        )
        self.assertEqual(
            tuple(
                (
                    observation.target_draw,
                    observation.wheel,
                )
                for observation in experiment[1]
            ),
            (
                (3, "Bari"),
                (3, "Roma"),
            ),
        )
        self.assertEqual(
            tuple(
                (
                    observation.target_draw,
                    observation.wheel,
                )
                for observation in experiment[2]
            ),
            (
                (3, "Bari"),
                (3, "Roma"),
            ),
        )

    def test_deduplicates_and_sorts_window_sizes(
        self,
    ) -> None:
        experiment = build_walk_forward_experiment(
            {
                "Bari": (
                    draw(
                        1,
                        (1, 23, 45, 67, 89),
                        wheel="Bari",
                        wheel_order=1,
                    ),
                    draw(
                        2,
                        (11, 12, 13, 14, 15),
                        wheel="Bari",
                        wheel_order=1,
                    ),
                    draw(
                        3,
                        (61, 11, 22, 33, 44),
                        wheel="Bari",
                        wheel_order=1,
                    ),
                ),
            },
            window_sizes=(2, 1, 2),
        )

        self.assertEqual(
            tuple(experiment),
            (1, 2),
        )

    def test_rejects_invalid_window_sizes(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            build_walk_forward_experiment(
                {},
                window_sizes=(),
            )

        with self.assertRaises(ValueError):
            build_walk_forward_experiment(
                {},
                window_sizes=(3, 0, 6),
            )

        with self.assertRaises(ValueError):
            build_walk_forward_experiment(
                {},
                window_sizes=(True,),
            )

    def test_returns_empty_series_for_empty_wheel_map(
        self,
    ) -> None:
        experiment = build_walk_forward_experiment(
            {},
            window_sizes=(3, 6),
        )

        self.assertEqual(
            experiment,
            {
                3: (),
                6: (),
            },
        )


class WalkForwardSummaryTests(unittest.TestCase):
    def test_summarizes_exposure_and_hits_in_period(
        self,
    ) -> None:
        summary = summarize_walk_forward_observations(
            (
                observation(
                    target_draw=100,
                    target_date="2025-01-01",
                    candidate_numbers=(11, 16, 61, 66),
                    hit_numbers=(11, 61),
                    ambo_hits=((11, 61),),
                ),
                observation(
                    target_draw=101,
                    target_date="2025-12-31",
                    candidate_numbers=(15, 51),
                    hit_numbers=(15,),
                    ambo_hits=(),
                ),
                observation(
                    target_draw=102,
                    target_date="2026-01-01",
                    candidate_numbers=(44, 47, 74, 77),
                    hit_numbers=(44, 47, 74),
                    ambo_hits=(
                        (44, 47),
                        (44, 74),
                        (47, 74),
                    ),
                ),
            ),
            window_size=6,
            period="development",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )

        self.assertEqual(summary.period, "development")
        self.assertEqual(summary.window_size, 6)
        self.assertEqual(summary.observation_count, 2)
        self.assertEqual(summary.candidate_number_count, 6)
        self.assertEqual(summary.covered_ambo_count, 7)
        self.assertEqual(summary.observations_with_number_hit, 2)
        self.assertEqual(summary.observations_with_ambo_hit, 1)
        self.assertEqual(summary.hit_number_count, 3)
        self.assertEqual(summary.hit_ambo_count, 1)
        self.assertEqual(
            summary.mean_candidate_number_count,
            3.0,
        )
        self.assertEqual(
            summary.mean_covered_ambo_count,
            3.5,
        )

    def test_period_boundaries_are_inclusive(
        self,
    ) -> None:
        observations = (
            observation(
                target_draw=100,
                target_date="2026-01-01",
                candidate_numbers=(11, 16),
                hit_numbers=(),
                ambo_hits=(),
            ),
            observation(
                target_draw=101,
                target_date="2026-12-31",
                candidate_numbers=(11, 16),
                hit_numbers=(),
                ambo_hits=(),
            ),
        )

        summary = summarize_walk_forward_observations(
            observations,
            window_size=6,
            period="held-out",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )

        self.assertEqual(summary.observation_count, 2)

    def test_empty_period_has_zero_safe_means(
        self,
    ) -> None:
        summary = summarize_walk_forward_observations(
            (),
            window_size=6,
            period="held-out",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )

        self.assertEqual(summary.observation_count, 0)
        self.assertEqual(
            summary.mean_candidate_number_count,
            0.0,
        )
        self.assertEqual(
            summary.mean_covered_ambo_count,
            0.0,
        )

    def test_rejects_mixed_window_series(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            summarize_walk_forward_observations(
                (
                    observation(
                        target_draw=100,
                        target_date="2025-01-01",
                        candidate_numbers=(11, 16),
                        hit_numbers=(),
                        ambo_hits=(),
                        window_size=3,
                    ),
                ),
                window_size=6,
                period="development",
                start_date="2025-01-01",
                end_date="2025-12-31",
            )

    def test_rejects_invalid_period_boundaries(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            summarize_walk_forward_observations(
                (),
                window_size=6,
                period="development",
                start_date="2025-12-31",
                end_date="2025-01-01",
            )

        with self.assertRaises(ValueError):
            summarize_walk_forward_observations(
                (),
                window_size=6,
                period="development",
                start_date="2025-02-30",
                end_date="2025-12-31",
            )


class MergeDrawHistoriesTests(unittest.TestCase):
    def test_merges_years_chronologically_with_reset_draw_numbers(
        self,
    ) -> None:
        merged = merge_draw_histories(
            (
                {
                    "Bari": (
                        DrawSnapshot(
                            draw_number=208,
                            draw_date="2025-12-30",
                            wheel="Bari",
                            wheel_order=1,
                            numbers=(11, 22, 33, 44, 55),
                        ),
                    ),
                },
                {
                    "Bari": (
                        DrawSnapshot(
                            draw_number=1,
                            draw_date="2026-01-02",
                            wheel="Bari",
                            wheel_order=1,
                            numbers=(12, 23, 34, 45, 56),
                        ),
                    ),
                },
            )
        )

        self.assertEqual(
            tuple(
                (draw.draw_date, draw.draw_number)
                for draw in merged["Bari"]
            ),
            (
                ("2025-12-30", 208),
                ("2026-01-02", 1),
            ),
        )

    def test_orders_wheels_by_official_order(
        self,
    ) -> None:
        merged = merge_draw_histories(
            (
                {
                    "Roma": (
                        DrawSnapshot(
                            draw_number=1,
                            draw_date="2026-01-02",
                            wheel="Roma",
                            wheel_order=8,
                            numbers=(11, 22, 33, 44, 55),
                        ),
                    ),
                    "Bari": (
                        DrawSnapshot(
                            draw_number=1,
                            draw_date="2026-01-02",
                            wheel="Bari",
                            wheel_order=1,
                            numbers=(12, 23, 34, 45, 56),
                        ),
                    ),
                },
            )
        )

        self.assertEqual(
            tuple(merged),
            ("Bari", "Roma"),
        )

    def test_rejects_duplicate_draw_key_on_same_wheel(
        self,
    ) -> None:
        duplicate = DrawSnapshot(
            draw_number=1,
            draw_date="2026-01-02",
            wheel="Bari",
            wheel_order=1,
            numbers=(11, 22, 33, 44, 55),
        )

        with self.assertRaises(ValueError):
            merge_draw_histories(
                (
                    {"Bari": (duplicate,)},
                    {"Bari": (duplicate,)},
                )
            )

    def test_rejects_inconsistent_wheel_order(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            merge_draw_histories(
                (
                    {
                        "Bari": (
                            DrawSnapshot(
                                draw_number=1,
                                draw_date="2025-01-02",
                                wheel="Bari",
                                wheel_order=1,
                                numbers=(11, 22, 33, 44, 55),
                            ),
                        ),
                    },
                    {
                        "Bari": (
                            DrawSnapshot(
                                draw_number=1,
                                draw_date="2026-01-02",
                                wheel="Bari",
                                wheel_order=2,
                                numbers=(12, 23, 34, 45, 56),
                            ),
                        ),
                    },
                )
            )

    def test_rejects_archive_with_missing_wheel(
        self,
    ) -> None:
        first = {
            "Bari": (
                DrawSnapshot(
                    draw_number=1,
                    draw_date="2025-01-02",
                    wheel="Bari",
                    wheel_order=1,
                    numbers=(11, 22, 33, 44, 55),
                ),
            ),
            "Roma": (
                DrawSnapshot(
                    draw_number=1,
                    draw_date="2025-01-02",
                    wheel="Roma",
                    wheel_order=8,
                    numbers=(12, 23, 34, 45, 56),
                ),
            ),
        }
        second = {
            "Bari": (
                DrawSnapshot(
                    draw_number=1,
                    draw_date="2026-01-02",
                    wheel="Bari",
                    wheel_order=1,
                    numbers=(13, 24, 35, 46, 57),
                ),
            ),
        }

        with self.assertRaises(ValueError):
            merge_draw_histories((first, second))

    def test_empty_archive_sequence_returns_empty_mapping(
        self,
    ) -> None:
        self.assertEqual(
            merge_draw_histories(()),
            {},
        )


class EqualSizeRandomBaselineTests(unittest.TestCase):
    def test_is_reproducible_with_the_same_seed(
        self,
    ) -> None:
        observations = (
            observation(
                target_draw=100,
                target_date="2025-01-01",
                candidate_numbers=(11, 22),
                hit_numbers=(11, 22),
                ambo_hits=((11, 22),),
                target_numbers=(11, 22, 33, 44, 55),
            ),
            observation(
                target_draw=101,
                target_date="2025-01-02",
                candidate_numbers=(1, 2, 3),
                hit_numbers=(1,),
                ambo_hits=(),
                target_numbers=(1, 20, 30, 40, 50),
            ),
        )

        first = simulate_equal_size_random_baseline(
            observations,
            window_size=6,
            period="development",
            start_date="2025-01-01",
            end_date="2025-12-31",
            repetitions=25,
            seed=20260731,
        )
        second = simulate_equal_size_random_baseline(
            observations,
            window_size=6,
            period="development",
            start_date="2025-01-01",
            end_date="2025-12-31",
            repetitions=25,
            seed=20260731,
        )

        self.assertEqual(first, second)
        self.assertEqual(first.observation_count, 2)
        self.assertEqual(first.repetitions, 25)
        self.assertEqual(
            len(first.replicate_hit_number_counts),
            25,
        )
        self.assertEqual(
            len(first.replicate_hit_ambo_counts),
            25,
        )
        self.assertEqual(first.covered_ambo_count, 4)
        self.assertEqual(first.observed_hit_number_count, 3)
        self.assertEqual(first.observed_hit_ambo_count, 1)
        self.assertGreaterEqual(
            first.empirical_p_value_hit_ambo,
            0.0,
        )
        self.assertLessEqual(
            first.empirical_p_value_hit_ambo,
            1.0,
        )

    def test_baseline_depends_on_size_not_candidate_identity(
        self,
    ) -> None:
        first_observation = observation(
            target_draw=100,
            target_date="2025-01-01",
            candidate_numbers=(11, 22, 33, 44),
            hit_numbers=(11, 22, 33, 44),
            ambo_hits=(
                (11, 22),
                (11, 33),
                (11, 44),
                (22, 33),
                (22, 44),
                (33, 44),
            ),
            target_numbers=(11, 22, 33, 44, 55),
        )
        second_observation = observation(
            target_draw=100,
            target_date="2025-01-01",
            candidate_numbers=(60, 70, 80, 90),
            hit_numbers=(),
            ambo_hits=(),
            target_numbers=(11, 22, 33, 44, 55),
        )

        first = simulate_equal_size_random_baseline(
            (first_observation,),
            window_size=6,
            period="development",
            start_date="2025-01-01",
            end_date="2025-12-31",
            repetitions=40,
            seed=1234,
        )
        second = simulate_equal_size_random_baseline(
            (second_observation,),
            window_size=6,
            period="development",
            start_date="2025-01-01",
            end_date="2025-12-31",
            repetitions=40,
            seed=1234,
        )

        self.assertEqual(
            first.replicate_hit_number_counts,
            second.replicate_hit_number_counts,
        )
        self.assertEqual(
            first.replicate_hit_ambo_counts,
            second.replicate_hit_ambo_counts,
        )
        self.assertNotEqual(
            first.observed_hit_ambo_count,
            second.observed_hit_ambo_count,
        )

    def test_applies_inclusive_period_boundaries(
        self,
    ) -> None:
        observations = (
            observation(
                target_draw=100,
                target_date="2026-01-01",
                candidate_numbers=(11, 22),
                hit_numbers=(),
                ambo_hits=(),
            ),
            observation(
                target_draw=101,
                target_date="2026-12-31",
                candidate_numbers=(11, 22),
                hit_numbers=(),
                ambo_hits=(),
            ),
            observation(
                target_draw=102,
                target_date="2027-01-01",
                candidate_numbers=(11, 22),
                hit_numbers=(),
                ambo_hits=(),
            ),
        )

        baseline = simulate_equal_size_random_baseline(
            observations,
            window_size=6,
            period="held-out",
            start_date="2026-01-01",
            end_date="2026-12-31",
            repetitions=5,
            seed=1,
        )

        self.assertEqual(baseline.observation_count, 2)
        self.assertEqual(baseline.covered_ambo_count, 2)

    def test_empty_period_has_zero_safe_distribution(
        self,
    ) -> None:
        baseline = simulate_equal_size_random_baseline(
            (),
            window_size=6,
            period="held-out",
            start_date="2026-01-01",
            end_date="2026-12-31",
            repetitions=5,
            seed=1,
        )

        self.assertEqual(baseline.observation_count, 0)
        self.assertEqual(
            baseline.replicate_hit_number_counts,
            (0, 0, 0, 0, 0),
        )
        self.assertEqual(
            baseline.replicate_hit_ambo_counts,
            (0, 0, 0, 0, 0),
        )
        self.assertEqual(
            baseline.mean_hit_number_count,
            0.0,
        )
        self.assertEqual(
            baseline.mean_hit_ambo_count,
            0.0,
        )
        self.assertEqual(
            baseline.empirical_p_value_hit_ambo,
            1.0,
        )

    def test_rejects_invalid_simulation_parameters(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            simulate_equal_size_random_baseline(
                (),
                window_size=6,
                period="development",
                start_date="2025-01-01",
                end_date="2025-12-31",
                repetitions=0,
                seed=1,
            )

        with self.assertRaises(ValueError):
            simulate_equal_size_random_baseline(
                (),
                window_size=6,
                period="development",
                start_date="2025-01-01",
                end_date="2025-12-31",
                repetitions=5,
                seed=True,
            )

    def test_rejects_mixed_window_series(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            simulate_equal_size_random_baseline(
                (
                    observation(
                        target_draw=100,
                        target_date="2025-01-01",
                        candidate_numbers=(11, 22),
                        hit_numbers=(),
                        ambo_hits=(),
                        window_size=3,
                    ),
                ),
                window_size=6,
                period="development",
                start_date="2025-01-01",
                end_date="2025-12-31",
                repetitions=5,
                seed=1,
            )


if __name__ == "__main__":
    unittest.main()
