from __future__ import annotations

import unittest

from analyze_coverage_anomalies import AnomalyEvent
from analyze_current_coverage import (
    active_anomalies,
    format_digits,
    latest_target,
    maturity_sort_key,
)
from strategies.coverage_completion import (
    ALL_DIGITS,
    CurrentCoverageState,
    current_coverage_state,
)
from strategies.twin_digits import DrawSnapshot


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
