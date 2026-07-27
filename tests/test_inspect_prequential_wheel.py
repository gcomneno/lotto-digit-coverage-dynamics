from __future__ import annotations

import unittest

from inspect_prequential_wheel import (
    available_wheels,
    format_digits,
    format_numbers,
    render_detail,
    render_table,
    resolve_wheel,
    select_observations,
    summarize,
)


def observation(
    *,
    target: int,
    wheel: str = "Bari",
    wheel_order: int = 1,
    probability: float = 0.45,
    completed: bool = False,
) -> dict[str, object]:
    return {
        "target_draw": target,
        "target_date": f"2025-07-{target:02d}",
        "wheel": wheel,
        "wheel_order": wheel_order,
        "source_latest_draw": target - 1,
        "source_latest_date": f"2025-07-{target - 1:02d}",
        "cycle_age": 2,
        "missing_digits": [9],
        "completion_probability_within": {
            "1": probability,
            "2": 0.70,
            "3": 0.83,
            "5": 0.95,
        },
        "expected_remaining_draws": 2.207,
        "target_numbers": [1, 2, 3, 4, 5],
        "target_digits": [0, 1, 2, 3, 4, 5],
        "completed": completed,
        "remaining_before_reset": (
            []
            if completed
            else [9]
        ),
    }


class InspectPrequentialWheelTests(unittest.TestCase):
    def test_formats_digits(self) -> None:
        self.assertEqual(
            format_digits([9, 2, 5]),
            "{2,5,9}",
        )

    def test_formats_numbers_with_leading_zero(self) -> None:
        self.assertEqual(
            format_numbers([1, 9, 40]),
            "01 09 40",
        )

    def test_available_wheels_follow_wheel_order(self) -> None:
        observations = (
            observation(
                target=101,
                wheel="Roma",
                wheel_order=2,
            ),
            observation(
                target=101,
                wheel="Bari",
                wheel_order=1,
            ),
        )

        self.assertEqual(
            available_wheels(observations),
            ("Bari", "Roma"),
        )

    def test_resolves_wheel_case_insensitively(self) -> None:
        self.assertEqual(
            resolve_wheel(
                "bArI",
                ("Bari", "Roma"),
            ),
            "Bari",
        )

    def test_rejects_unknown_wheel(self) -> None:
        with self.assertRaises(ValueError):
            resolve_wheel(
                "Lucca",
                ("Bari", "Roma"),
            )

    def test_selects_target_range(self) -> None:
        observations = tuple(
            observation(target=target)
            for target in range(101, 106)
        )

        selected = select_observations(
            observations,
            wheel="Bari",
            start_target=102,
            end_target=104,
        )

        self.assertEqual(
            [
                item["target_draw"]
                for item in selected
            ],
            [102, 103, 104],
        )

    def test_summarizes_expected_and_observed(self) -> None:
        result = summarize(
            (
                observation(
                    target=101,
                    probability=0.25,
                    completed=False,
                ),
                observation(
                    target=102,
                    probability=0.75,
                    completed=True,
                ),
            )
        )

        self.assertEqual(result["cases"], 2)
        self.assertEqual(
            result["expected_closures"],
            1.0,
        )
        self.assertEqual(
            result["observed_closures"],
            1,
        )
        self.assertAlmostEqual(
            result["brier_score"],
            0.0625,
        )

    def test_table_contains_cumulative_metrics(self) -> None:
        rendered = render_table(
            (
                observation(
                    target=101,
                    completed=False,
                ),
                observation(
                    target=102,
                    completed=True,
                ),
            )
        )

        self.assertIn("Cum.att", rendered)
        self.assertIn("101", rendered)
        self.assertIn("102", rendered)
        self.assertIn("CHIUSO", rendered)

    def test_detail_contains_all_horizons(self) -> None:
        rendered = render_detail(
            (
                observation(target=101),
            )
        )

        self.assertIn(
            "Chiusura entro 1",
            rendered,
        )
        self.assertIn(
            "Chiusura entro 5",
            rendered,
        )
        self.assertIn(
            "Attesa residua teorica",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
