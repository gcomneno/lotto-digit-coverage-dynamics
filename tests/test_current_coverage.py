from __future__ import annotations

import argparse
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date

from analyze_coverage_anomalies import AnomalyEvent
from analyze_current_coverage import (
    active_anomalies,
    build_parser,
    format_digits,
    format_next_draw_number,
    format_numbers,
    latest_target,
    limit_draws_to_date,
    limit_draws_to_number,
    maturity_sort_key,
    next_draws_after_target,
    parse_draw_number,
    parse_iso_date,
    print_markov_summary,
    transversal_convergence,
)
from strategies.coverage_completion import (
    ALL_DIGITS,
    CurrentCoverageState,
    current_coverage_state,
)
from strategies.lotto_repository import DrawSnapshot


def draw(
    number: int,
    values: tuple[int, ...],
    wheel: str = "Bari",
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=f"2025-01-{number:02d}",
        wheel=wheel,
        wheel_order=1,
        numbers=values,
    )


def current_state(
    *,
    wheel: str = "Bari",
    wheel_order: int = 1,
    latest_draw: int = 119,
    latest_date: str = "2026-07-25",
) -> CurrentCoverageState:
    return CurrentCoverageState(
        wheel=wheel,
        wheel_order=wheel_order,
        latest_draw=latest_draw,
        latest_date=latest_date,
        completed_cycles=1,
        draws_in_cycle=1,
        covered_digits=frozenset(),
        missing_digits=ALL_DIGITS,
        synchronized=True,
    )


def anomaly_event(
    *,
    category: str,
    target_draw: int,
    target_date: str,
    right_censored: bool = False,
    wheel: str = "Bari",
    wheel_order: int = 1,
) -> AnomalyEvent:
    return AnomalyEvent(
        category=category,
        signature=f"{category}:test",
        recurrence_key=f"{category}:test",
        wheel=wheel,
        wheel_order=wheel_order,
        cycle_number=1,
        event_index=target_draw,
        target_draw=target_draw,
        target_date=target_date,
        source_state="{0}",
        target_state="{}",
        horizon=1,
        conditional_probability=0.001,
        atom_probability=0.001,
        previous_conditional_probability=None,
        pair_probability=None,
        surprisal=3.0,
        severity="extreme",
        right_censored=right_censored,
        previous_target_draw=None,
        previous_target_date=None,
        recurrence_gap=None,
    )


class CurrentCoverageStateTests(unittest.TestCase):
    def test_formats_colored_next_draw_number(
        self,
    ) -> None:
        self.assertEqual(
            format_next_draw_number(
                2,
                top_digits=frozenset({0}),
                missing_digits=frozenset({2}),
                use_color=True,
            ),
            (
                "\033[1;30;46m0\033[0m"
                "\033[1;30;43m2\033[0m"
            ),
        )

    def test_formats_plain_next_draw_number(
        self,
    ) -> None:
        self.assertEqual(
            format_next_draw_number(
                12,
                top_digits=frozenset({1}),
                missing_digits=frozenset({2}),
                use_color=False,
            ),
            "12",
        )

    def test_latest_completion_starts_empty_new_cycle(
        self,
    ) -> None:
        state = current_coverage_state(
            (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
            )
        )

        self.assertTrue(state.synchronized)
        self.assertEqual(
            state.draws_in_cycle,
            0,
        )
        self.assertEqual(
            state.missing_digits,
            ALL_DIGITS,
        )
        self.assertEqual(
            state.most_present_digits,
            frozenset(),
        )

    def test_tracks_state_after_completed_cycle(
        self,
    ) -> None:
        state = current_coverage_state(
            (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
                draw(
                    2,
                    (11, 22, 33, 44, 55),
                ),
            )
        )

        self.assertTrue(state.synchronized)
        self.assertEqual(
            state.completed_cycles,
            1,
        )
        self.assertEqual(
            state.draws_in_cycle,
            1,
        )
        self.assertEqual(
            state.covered_digits,
            frozenset({
                1,
                2,
                3,
                4,
                5,
            }),
        )
        self.assertEqual(
            state.missing_digits,
            frozenset({
                0,
                6,
                7,
                8,
                9,
            }),
        )
        self.assertEqual(
            state.most_present_digits,
            frozenset({
                1,
                2,
                3,
                4,
                5,
            }),
        )

    def test_marks_unobserved_initial_cycle(
        self,
    ) -> None:
        state = current_coverage_state(
            (
                draw(
                    1,
                    (11, 22, 33, 44, 55),
                ),
            )
        )

        self.assertFalse(
            state.synchronized
        )

    def test_rejects_mixed_wheels(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            current_coverage_state(
                (
                    draw(
                        1,
                        (1, 23, 45, 67, 89),
                    ),
                    draw(
                        2,
                        (11, 22, 33, 44, 55),
                        wheel="Roma",
                    ),
                )
            )

    def test_formats_state(self) -> None:
        self.assertEqual(
            format_digits(
                frozenset({
                    9,
                    2,
                    5,
                })
            ),
            "{2,5,9}",
        )

    def test_ranking_prefers_lower_expected_time(
        self,
    ) -> None:
        state = current_state()

        slower = (
            state,
            {
                "expected_remaining_draws": 3.0,
                "completion_within": {
                    1: 0.5,
                },
            },
        )

        faster = (
            state,
            {
                "expected_remaining_draws": 2.0,
                "completion_within": {
                    1: 0.4,
                },
            },
        )

        self.assertLess(
            maturity_sort_key(faster),
            maturity_sort_key(slower),
        )

    def test_latest_target_requires_alignment(
        self,
    ) -> None:
        states = (
            current_state(
                wheel="Bari",
                wheel_order=1,
            ),
            current_state(
                wheel="Roma",
                wheel_order=2,
                latest_draw=118,
                latest_date="2026-07-24",
            ),
        )

        with self.assertRaises(RuntimeError):
            latest_target(states)

    def test_latest_target_returns_shared_target(
        self,
    ) -> None:
        states = (
            current_state(
                wheel="Bari",
                wheel_order=1,
            ),
            current_state(
                wheel="Roma",
                wheel_order=2,
            ),
        )

        self.assertEqual(
            latest_target(states),
            (
                119,
                "2026-07-25",
            ),
        )

    def test_parses_strict_iso_cutoff_date(
        self,
    ) -> None:
        self.assertEqual(
            parse_iso_date("2026-06-30"),
            date(2026, 6, 30),
        )

        with self.assertRaises(
            argparse.ArgumentTypeError
        ):
            parse_iso_date("30-06-2026")

    def test_cutoff_is_inclusive(
        self,
    ) -> None:
        draws_by_wheel = {
            "Bari": (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
                draw(
                    2,
                    (11, 22, 33, 44, 55),
                ),
                draw(
                    3,
                    (12, 34, 56, 78, 90),
                ),
            ),
        }

        limited = limit_draws_to_date(
            draws_by_wheel,
            date(2025, 1, 2),
        )

        self.assertEqual(
            tuple(
                item.draw_number
                for item in limited["Bari"]
            ),
            (1, 2),
        )

    def test_cutoff_rejects_empty_history(
        self,
    ) -> None:
        draws_by_wheel = {
            "Bari": (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
            ),
        }

        with self.assertRaises(RuntimeError):
            limit_draws_to_date(
                draws_by_wheel,
                date(2024, 12, 31),
            )

    def test_finds_aligned_next_draw(
        self,
    ) -> None:
        bari_draws = (
            draw(
                1,
                (1, 23, 45, 67, 89),
            ),
            draw(
                2,
                (11, 22, 33, 44, 55),
            ),
        )
        roma_draws = (
            DrawSnapshot(
                draw_number=1,
                draw_date="2025-01-01",
                wheel="Roma",
                wheel_order=2,
                numbers=(2, 24, 46, 68, 90),
            ),
            DrawSnapshot(
                draw_number=2,
                draw_date="2025-01-02",
                wheel="Roma",
                wheel_order=2,
                numbers=(12, 23, 34, 45, 56),
            ),
        )

        following = next_draws_after_target(
            {
                "Bari": bari_draws,
                "Roma": roma_draws,
            },
            latest_draw=1,
            latest_date="2025-01-01",
        )

        self.assertEqual(
            tuple(
                (
                    item.wheel,
                    item.draw_number,
                    item.draw_date,
                )
                for item in following
            ),
            (
                (
                    "Bari",
                    2,
                    "2025-01-02",
                ),
                (
                    "Roma",
                    2,
                    "2025-01-02",
                ),
            ),
        )

    def test_next_draw_is_empty_at_archive_end(
        self,
    ) -> None:
        draws_by_wheel = {
            "Bari": (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
            ),
        }

        self.assertEqual(
            next_draws_after_target(
                draws_by_wheel,
                latest_draw=1,
                latest_date="2025-01-01",
            ),
            (),
        )

    def test_next_draw_rejects_partial_target(
        self,
    ) -> None:
        draws_by_wheel = {
            "Bari": (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
                draw(
                    2,
                    (11, 22, 33, 44, 55),
                ),
            ),
            "Roma": (
                DrawSnapshot(
                    draw_number=1,
                    draw_date="2025-01-01",
                    wheel="Roma",
                    wheel_order=2,
                    numbers=(2, 24, 46, 68, 90),
                ),
            ),
        }

        with self.assertRaises(RuntimeError):
            next_draws_after_target(
                draws_by_wheel,
                latest_draw=1,
                latest_date="2025-01-01",
            )

    def test_formats_candidate_numbers(self) -> None:
        self.assertEqual(
            format_numbers(
                frozenset({
                    76,
                    16,
                    61,
                    17,
                    71,
                    67,
                })
            ),
            "{16,17,61,67,71,76}",
        )

    def test_parses_positive_draw_number(self) -> None:
        self.assertEqual(
            parse_draw_number("119"),
            119,
        )

        for invalid in (
            "0",
            "-1",
            "abc",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(
                    argparse.ArgumentTypeError
                ):
                    parse_draw_number(invalid)

    def test_draw_number_cutoff_is_inclusive(
        self,
    ) -> None:
        draws_by_wheel = {
            "Bari": (
                draw(
                    1,
                    (1, 23, 45, 67, 89),
                ),
                draw(
                    2,
                    (11, 22, 33, 44, 55),
                ),
                draw(
                    3,
                    (12, 34, 56, 78, 90),
                ),
            ),
        }

        limited = limit_draws_to_number(
            draws_by_wheel,
            2,
        )

        self.assertEqual(
            tuple(
                item.draw_number
                for item in limited["Bari"]
            ),
            (1, 2),
        )

    def test_draw_number_cutoff_rejects_empty_history(
        self,
    ) -> None:
        draws_by_wheel = {
            "Bari": (
                draw(
                    2,
                    (1, 23, 45, 67, 89),
                ),
            ),
        }

        with self.assertRaises(RuntimeError):
            limit_draws_to_number(
                draws_by_wheel,
                1,
            )

    def test_cutoff_options_are_mutually_exclusive(
        self,
    ) -> None:
        parser = build_parser()

        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(
                    (
                        "--to",
                        "2026-07-25",
                        "--to-num",
                        "119",
                    )
                )

    def test_draw_number_option_supports_both_spellings(
        self,
    ) -> None:
        parser = build_parser()

        underscored = parser.parse_args(
            (
                "--to_num",
                "119",
            )
        )
        hyphenated = parser.parse_args(
            (
                "--to-num",
                "119",
            )
        )

        self.assertEqual(
            underscored.to_draw_number,
            119,
        )
        self.assertEqual(
            hyphenated.to_draw_number,
            119,
        )

    def test_transversal_convergence_uses_maximum_one_step_group(
        self,
    ) -> None:
        states = (
            CurrentCoverageState(
                wheel="Genova",
                wheel_order=1,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=35,
                draws_in_cycle=3,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    0,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    6,
                }),
            ),
            CurrentCoverageState(
                wheel="Milano",
                wheel_order=2,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=32,
                draws_in_cycle=4,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    6,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    7,
                }),
            ),
            CurrentCoverageState(
                wheel="Nazionale",
                wheel_order=3,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=34,
                draws_in_cycle=3,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    1,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    7,
                }),
            ),
            CurrentCoverageState(
                wheel="Torino",
                wheel_order=4,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=33,
                draws_in_cycle=6,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    9,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    1,
                    8,
                }),
            ),
            CurrentCoverageState(
                wheel="Bari",
                wheel_order=5,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=37,
                draws_in_cycle=0,
                covered_digits=frozenset(),
                missing_digits=ALL_DIGITS,
                synchronized=True,
                most_present_digits=frozenset(),
            ),
        )

        self.assertEqual(
            transversal_convergence(states),
            (
                frozenset({
                    1,
                    6,
                    7,
                    8,
                }),
                frozenset({
                    0,
                    1,
                    6,
                }),
                frozenset({
                    1,
                    6,
                }),
                frozenset({
                    16,
                    61,
                }),
            ),
        )

    def test_markov_summary_prints_transversal_row(
        self,
    ) -> None:
        states = (
            CurrentCoverageState(
                wheel="Genova",
                wheel_order=1,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=35,
                draws_in_cycle=3,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    0,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    6,
                }),
            ),
            CurrentCoverageState(
                wheel="Milano",
                wheel_order=2,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=32,
                draws_in_cycle=4,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    6,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    7,
                }),
            ),
            CurrentCoverageState(
                wheel="Nazionale",
                wheel_order=3,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=34,
                draws_in_cycle=3,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    1,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    7,
                }),
            ),
            CurrentCoverageState(
                wheel="Torino",
                wheel_order=4,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=33,
                draws_in_cycle=6,
                covered_digits=frozenset(),
                missing_digits=frozenset({
                    9,
                }),
                synchronized=True,
                most_present_digits=frozenset({
                    1,
                    8,
                }),
            ),
            CurrentCoverageState(
                wheel="Bari",
                wheel_order=5,
                latest_draw=120,
                latest_date="2026-07-28",
                completed_cycles=37,
                draws_in_cycle=0,
                covered_digits=frozenset(),
                missing_digits=ALL_DIGITS,
                synchronized=True,
                most_present_digits=frozenset(),
            ),
        )
        output = io.StringIO()

        with redirect_stdout(output):
            print_markov_summary(states)

        rendered = output.getvalue()

        self.assertIn(
            "TUTTE",
            rendered,
        )
        self.assertIn(
            "{1,6,7,8}",
            rendered,
        )
        self.assertIn(
            "{0,1,6}",
            rendered,
        )
        self.assertIn(
            "C={1,6}",
            rendered,
        )
        self.assertIn(
            "Numeri={16,61}",
            rendered,
        )
        self.assertIn(
            "probabilità Entro 1 massima",
            rendered,
        )

    def test_active_anomalies_distinguish_stateful_a1(
        self,
    ) -> None:
        events = (
            anomaly_event(
                category="A1",
                target_draw=110,
                target_date="2026-07-04",
                right_censored=True,
                wheel="Palermo",
                wheel_order=7,
            ),
            anomaly_event(
                category="A1",
                target_draw=111,
                target_date="2026-07-07",
                right_censored=False,
                wheel="Roma",
                wheel_order=8,
            ),
            anomaly_event(
                category="A2",
                target_draw=119,
                target_date="2026-07-25",
                wheel="Genova",
                wheel_order=4,
            ),
            anomaly_event(
                category="A3",
                target_draw=118,
                target_date="2026-07-24",
                wheel="Milano",
                wheel_order=5,
            ),
        )

        active = active_anomalies(
            events,
            latest_draw=119,
            latest_date="2026-07-25",
        )

        self.assertEqual(
            tuple(
                (
                    event.category,
                    event.wheel,
                )
                for event in active
            ),
            (
                (
                    "A1",
                    "Palermo",
                ),
                (
                    "A2",
                    "Genova",
                ),
            ),
        )

    def test_current_instant_anomaly_requires_date(
        self,
    ) -> None:
        events = (
            anomaly_event(
                category="A2",
                target_draw=119,
                target_date="2025-07-25",
            ),
        )

        self.assertEqual(
            active_anomalies(
                events,
                latest_draw=119,
                latest_date="2026-07-25",
            ),
            (),
        )


if __name__ == "__main__":
    unittest.main()
