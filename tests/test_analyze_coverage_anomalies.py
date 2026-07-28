from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analyze_coverage_anomalies import (
    AnomalyEvent,
    TransitionObservation,
    build_transition_observations,
    detect_persistence_anomalies,
    detect_recurrence_anomalies,
    detect_transition_anomalies,
    make_primary_event,
    summary_document,
    transition_surprise_probability,
    validate_anomalies,
    write_csv,
    write_json,
)
from strategies.coverage_completion import ALL_DIGITS
from strategies.coverage_markov import completion_probability_within, transition_probability
from strategies.twin_digits import DrawSnapshot


SYNCHRONIZING_DRAW = (12, 34, 56, 78, 90)


def draw(
    number: int,
    date: str,
    numbers: tuple[int, ...],
    *,
    wheel: str = "Bari",
    wheel_order: int = 1,
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=date,
        wheel=wheel,
        wheel_order=wheel_order,
        numbers=numbers,
    )


def transition(
    index: int,
    source: tuple[int, ...],
    target: tuple[int, ...],
    *,
    cycle: int = 1,
) -> TransitionObservation:
    return TransitionObservation(
        wheel="Bari",
        wheel_order=1,
        cycle_number=cycle,
        event_index=index,
        position_in_cycle=index,
        target_draw=index,
        target_date=f"2025-01-{index:02d}",
        source_state=source,
        target_state=target,
        transition_probability=transition_probability(source, target),
    )


class CoverageAnomalyTests(unittest.TestCase):
    def test_skips_initial_left_censored_segment(self) -> None:
        observations = build_transition_observations(
            (
                draw(1, "2025-01-01", (11, 22, 33, 44, 55)),
                draw(2, "2025-01-02", SYNCHRONIZING_DRAW),
                draw(3, "2025-01-03", (11, 22, 33, 44, 55)),
            )
        )

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].event_index, 1)
        self.assertEqual(observations[0].cycle_number, 1)
        self.assertEqual(observations[0].source_state, tuple(range(10)))

    def test_detects_rare_immediate_closure(self) -> None:
        observations = build_transition_observations(
            (
                draw(1, "2025-01-01", SYNCHRONIZING_DRAW),
                draw(2, "2025-01-02", SYNCHRONIZING_DRAW),
            )
        )
        events = detect_transition_anomalies(observations, threshold=0.01)

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.category, "A2")
        self.assertEqual(event.source_state, "{0,1,2,3,4,5,6,7,8,9}")
        self.assertEqual(event.target_state, "{}")
        self.assertAlmostEqual(
            event.conditional_probability,
            transition_probability(ALL_DIGITS, ()),
            places=15,
        )

    def test_detects_exact_rare_transition(self) -> None:
        observations = build_transition_observations(
            (
                draw(1, "2025-01-01", SYNCHRONIZING_DRAW),
                draw(2, "2025-01-02", (1, 23, 45, 67, 88)),
            )
        )
        events = detect_transition_anomalies(observations, threshold=1.0)

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.category, "A3")
        self.assertEqual(event.target_state, "{9}")
        atom = transition_probability(
            ALL_DIGITS,
            (9,),
        )

        self.assertAlmostEqual(
            event.atom_probability or 0.0,
            atom,
            places=15,
        )

        self.assertAlmostEqual(
            event.conditional_probability,
            transition_surprise_probability(
                tuple(range(10)),
                (9,),
            ),
            places=15,
        )

        self.assertGreaterEqual(
            event.conditional_probability,
            atom,
        )


    def test_full_state_common_exact_cell_is_not_anomalous(self) -> None:
        observation = transition(
            1,
            tuple(range(10)),
            (1, 6, 9),
        )

        self.assertLess(
            observation.transition_probability,
            0.01,
        )

        self.assertGreater(
            transition_surprise_probability(
                observation.source_state,
                observation.target_state,
            ),
            0.01,
        )

        events = detect_transition_anomalies(
            (observation,),
            threshold=0.01,
        )

        self.assertEqual(events, ())

    def test_persistence_emits_first_crossing_once(self) -> None:
        observations = tuple(
            transition(index, (6,), (6,))
            for index in range(1, 7)
        )
        events = detect_persistence_anomalies(observations, threshold=0.01)

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.category, "A1")
        self.assertEqual(event.horizon, 5)
        self.assertEqual(event.event_index, 5)
        self.assertTrue(event.right_censored)
        self.assertAlmostEqual(
            event.conditional_probability,
            1.0 - completion_probability_within((6,), 5),
            places=15,
        )

    def test_completed_cycle_persistence_is_not_censored(self) -> None:
        observations = tuple(
            [transition(index, (6,), (6,)) for index in range(1, 6)]
            + [transition(6, (6,), ())]
        )
        events = detect_persistence_anomalies(observations, threshold=0.01)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_index, 5)
        self.assertFalse(events[0].right_censored)

    def test_recurrence_uses_previous_equal_key(self) -> None:
        first_observation = transition(1, tuple(range(10)), ())
        second_observation = transition(5, tuple(range(10)), (), cycle=2)
        first = make_primary_event(
            category="A2",
            signature="A2:closure:{0,1,2,3,4,5,6,7,8,9}->{}",
            recurrence_key="A2:closure:{0,1,2,3,4,5,6,7,8,9}",
            observation=first_observation,
            source_state=tuple(range(10)),
            target_state=(),
            horizon=1,
            probability=0.0005,
            atom_probability=0.0005,
        )
        second = make_primary_event(
            category="A2",
            signature="A2:closure:{0,1,2,3,4,5,6,7,8,9}->{}",
            recurrence_key="A2:closure:{0,1,2,3,4,5,6,7,8,9}",
            observation=second_observation,
            source_state=tuple(range(10)),
            target_state=(),
            horizon=1,
            probability=0.0005,
            atom_probability=0.0005,
        )

        events = detect_recurrence_anomalies(
            (first, second), max_gap=10, threshold=0.01
        )

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.category, "A4")
        self.assertEqual(event.recurrence_gap, 4)
        self.assertEqual(event.previous_target_draw, 1)
        self.assertAlmostEqual(
            event.conditional_probability,
            0.005,
        )
        self.assertAlmostEqual(
            event.previous_conditional_probability or 0.0,
            0.0005,
        )
        self.assertAlmostEqual(
            event.pair_probability or 0.0,
            0.00000025,
        )

    def test_validator_rejects_exact_duplicates(self) -> None:
        observation = transition(1, tuple(range(10)), ())
        event = make_primary_event(
            category="A2",
            signature="A2:test",
            recurrence_key="A2:test",
            observation=observation,
            source_state=tuple(range(10)),
            target_state=(),
            horizon=1,
            probability=0.001,
        )

        with self.assertRaises(RuntimeError):
            validate_anomalies((event, event))

    def test_outputs_are_lf_and_summary_has_no_duplicates(self) -> None:
        observation = transition(1, tuple(range(10)), ())
        event = make_primary_event(
            category="A2",
            signature="A2:test",
            recurrence_key="A2:test",
            observation=observation,
            source_state=tuple(range(10)),
            target_state=(),
            horizon=1,
            probability=0.001,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "events.csv"
            json_path = root / "events.json"
            write_csv((event,), csv_path)
            write_json(
                (event,),
                label="synthetic",
                databases=(Path("archive.sqlite3"),),
                threshold=0.01,
                recurrence_window=10,
                recurrence_threshold=0.01,
                output=json_path,
            )

            self.assertNotIn(b"\r", csv_path.read_bytes())
            document = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(document["summary"]["event_count"], 1)
            self.assertEqual(document["summary"]["duplicate_event_count"], 0)
            self.assertEqual(summary_document((event,))["category_counts"]["A2"], 1)


if __name__ == "__main__":
    unittest.main()
