from __future__ import annotations

import unittest

from analyze_takeoff_momentum import (
    TakeoffSignal,
    detect_takeoff_signals,
    summarize,
)


def observation(
    target: int,
    completed: bool,
    *,
    probability: float = 0.5,
    wheel: str = "Bari",
) -> dict[str, object]:
    return {
        "target_draw": target,
        "target_date": f"2025-01-{target:02d}",
        "source_latest_draw": target - 1,
        "source_latest_date": f"2025-01-{target - 1:02d}",
        "wheel": wheel,
        "wheel_order": 1,
        "cycle_age": 2,
        "missing_digits": [2, 5],
        "completion_probability_within": {
            "1": probability,
        },
        "expected_remaining_draws": 1.839,
        "target_numbers": [1, 2, 3, 4, 5],
        "target_digits": [0, 1, 2, 3, 4, 5],
        "completed": completed,
        "remaining_before_reset": (
            []
            if completed
            else [2, 5]
        ),
    }


def build_rows(
    outcomes: list[bool],
) -> list[dict[str, object]]:
    return [
        observation(index, outcome)
        for index, outcome in enumerate(
            outcomes,
            start=1,
        )
    ]


def signal(
    *,
    target: int,
    probability: float,
    completed: bool,
) -> TakeoffSignal:
    return TakeoffSignal(
        report="test",
        wheel="Bari",
        target_draw=target,
        target_date="2025-01-01",
        source_latest_draw=target - 1,
        calm_start_draw=1,
        calm_end_draw=5,
        calm_z=0.1,
        wave_start_draw=6,
        wave_end_draw=7,
        wave_z=1.5,
        probability=probability,
        completed=completed,
        missing_digits=(2, 5),
        cycle_age=2,
    )


class TakeoffMomentumTests(unittest.TestCase):
    def test_no_signal_without_calm(
        self,
    ) -> None:
        rows = build_rows(
            [True] * 10
        )

        signals = detect_takeoff_signals(
            rows,
            report_label="test",
        )

        self.assertEqual(signals, ())

    def test_calm_and_wave_same_history_only_arms(
        self,
    ) -> None:
        rows = build_rows(
            [
                False,
                False,
                True,
                True,
                True,
                False,
            ]
        )

        signals = detect_takeoff_signals(
            rows,
            report_label="test",
        )

        self.assertEqual(signals, ())

    def test_takeoff_is_evaluated_on_following_target(
        self,
    ) -> None:
        rows = build_rows(
            [
                False,
                False,
                True,
                True,
                True,
                True,
                False,
            ]
        )

        signals = detect_takeoff_signals(
            rows,
            report_label="test",
        )

        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].target_draw,
            7,
        )
        self.assertEqual(
            signals[0].calm_end_draw,
            5,
        )
        self.assertEqual(
            signals[0].wave_end_draw,
            6,
        )

    def test_target_outcome_does_not_change_entry(
        self,
    ) -> None:
        prefix = [
            False,
            False,
            True,
            True,
            True,
            True,
        ]

        open_signals = detect_takeoff_signals(
            build_rows(prefix + [False]),
            report_label="test",
        )

        closed_signals = detect_takeoff_signals(
            build_rows(prefix + [True]),
            report_label="test",
        )

        self.assertAlmostEqual(
            open_signals[0].wave_z,
            closed_signals[0].wave_z,
        )

    def test_second_signal_requires_new_full_calm(
        self,
    ) -> None:
        rows = build_rows(
            [
                True,
                False,
                True,
                False,
                False,
                True,
                True,
                False,
                False,
                True,
                False,
                True,
                True,
                True,
                False,
            ]
        )

        signals = detect_takeoff_signals(
            rows,
            report_label="test",
        )

        self.assertEqual(
            [
                item.target_draw
                for item in signals
            ],
            [8, 15],
        )

        self.assertGreater(
            signals[1].calm_start_draw,
            signals[0].target_draw,
        )

    def test_summary_compares_observed_and_expected(
        self,
    ) -> None:
        result = summarize(
            (
                signal(
                    target=10,
                    probability=0.25,
                    completed=False,
                ),
                signal(
                    target=20,
                    probability=0.75,
                    completed=True,
                ),
            )
        )

        self.assertEqual(result["cases"], 2)
        self.assertEqual(result["observed"], 1)
        self.assertEqual(result["expected"], 1.0)
        self.assertAlmostEqual(
            result["brier"],
            0.0625,
        )

    def test_invalid_parameters_are_rejected(
        self,
    ) -> None:
        rows = build_rows(
            [False] * 10
        )

        for kwargs in (
            {"calm_window": 0},
            {"wave_window": 0},
            {"calm_abs_z": -0.1},
            {"entry_z": 0.0},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    detect_takeoff_signals(
                        rows,
                        report_label="test",
                        **kwargs,
                    )


if __name__ == "__main__":
    unittest.main()
