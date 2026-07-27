from __future__ import annotations

import unittest

from analyze_one_shot_momentum import (
    MomentumSignal,
    detect_signals,
    momentum_z,
    poisson_binomial_p_values,
    summarize,
)


def observation(
    target: int,
    completed: bool,
    *,
    probability: float = 0.1,
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


def signal(
    *,
    target: int,
    probability: float,
    completed: bool,
) -> MomentumSignal:
    return MomentumSignal(
        report="test",
        wheel="Bari",
        target_draw=target,
        target_date="2025-01-01",
        source_latest_draw=target - 1,
        history_start_draw=target - 3,
        history_end_draw=target - 1,
        z_score=2.0,
        probability=probability,
        completed=completed,
        missing_digits=(2, 5),
        cycle_age=2,
    )


class OneShotMomentumTests(unittest.TestCase):
    def test_momentum_z_uses_standardized_residuals(
        self,
    ) -> None:
        history = [
            observation(1, True),
            observation(2, True),
            observation(3, True),
        ]

        self.assertAlmostEqual(
            momentum_z(history),
            5.196152422706632,
        )

    def test_no_signal_without_full_history(
        self,
    ) -> None:
        rows = [
            observation(1, True),
            observation(2, True),
            observation(3, True),
        ]

        signals = detect_signals(
            rows,
            report_label="test",
            window=3,
            entry_z=1.5,
            rearm_z=0.5,
        )

        self.assertEqual(signals, ())

    def test_signal_is_evaluated_on_next_target(
        self,
    ) -> None:
        rows = [
            observation(1, True),
            observation(2, True),
            observation(3, True),
            observation(4, False),
        ]

        signals = detect_signals(
            rows,
            report_label="test",
            window=3,
            entry_z=1.5,
            rearm_z=0.5,
        )

        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].target_draw,
            4,
        )
        self.assertEqual(
            signals[0].history_end_draw,
            3,
        )

    def test_target_outcome_does_not_change_entry(
        self,
    ) -> None:
        prefix = [
            observation(1, True),
            observation(2, True),
            observation(3, True),
        ]

        open_signals = detect_signals(
            prefix + [observation(4, False)],
            report_label="test",
            window=3,
            entry_z=1.5,
            rearm_z=0.5,
        )

        closed_signals = detect_signals(
            prefix + [observation(4, True)],
            report_label="test",
            window=3,
            entry_z=1.5,
            rearm_z=0.5,
        )

        self.assertAlmostEqual(
            open_signals[0].z_score,
            closed_signals[0].z_score,
        )

    def test_disarm_prevents_repeated_entries(
        self,
    ) -> None:
        rows = [
            observation(1, True),
            observation(2, True),
            observation(3, True),
            observation(4, True),
            observation(5, True),
        ]

        signals = detect_signals(
            rows,
            report_label="test",
            window=3,
            entry_z=1.5,
            rearm_z=0.5,
        )

        self.assertEqual(
            [
                item.target_draw
                for item in signals
            ],
            [4],
        )

    def test_rearm_allows_a_later_new_wave(
        self,
    ) -> None:
        outcomes = [
            True,
            True,
            True,
            False,
            False,
            False,
            True,
            True,
            True,
            False,
        ]

        rows = [
            observation(index, outcome)
            for index, outcome in enumerate(
                outcomes,
                start=1,
            )
        ]

        signals = detect_signals(
            rows,
            report_label="test",
            window=3,
            entry_z=1.5,
            rearm_z=0.5,
        )

        self.assertEqual(
            [
                item.target_draw
                for item in signals
            ],
            [4, 9],
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

    def test_poisson_binomial_p_values(
        self,
    ) -> None:
        upper, two_sided = (
            poisson_binomial_p_values(
                (0.5, 0.5),
                2,
            )
        )

        self.assertAlmostEqual(upper, 0.25)
        self.assertAlmostEqual(two_sided, 0.5)


if __name__ == "__main__":
    unittest.main()
