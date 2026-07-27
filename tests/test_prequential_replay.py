from __future__ import annotations

import unittest

from strategies.prequential_replay import (
    build_prequential_replay,
)
from strategies.twin_digits import DrawSnapshot


def draw(
    number: int,
    values: tuple[int, ...],
    wheel: str = "Bari",
    wheel_order: int = 1,
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=f"2025-01-{number:02d}",
        wheel=wheel,
        wheel_order=wheel_order,
        numbers=values,
    )


class PrequentialReplayTests(unittest.TestCase):
    def test_target_is_never_in_source_state(self) -> None:
        observations = build_prequential_replay(
            {
                "Bari": (
                    draw(1, (1, 23, 45, 67, 89)),
                    draw(2, (11, 22, 33, 44, 55)),
                    draw(3, (9, 12, 34, 56, 78)),
                )
            },
            start_target=2,
            end_target=3,
        )

        self.assertEqual(
            observations[0].source_latest_draw,
            1,
        )
        self.assertEqual(
            observations[0].target_draw,
            2,
        )

        self.assertEqual(
            observations[1].source_latest_draw,
            2,
        )
        self.assertEqual(
            observations[1].target_draw,
            3,
        )

    def test_sequential_update_changes_state(self) -> None:
        observations = build_prequential_replay(
            {
                "Bari": (
                    draw(1, (1, 23, 45, 67, 89)),
                    draw(2, (11, 22, 33, 44, 55)),
                    draw(3, (9, 12, 34, 56, 78)),
                )
            },
            start_target=2,
            end_target=3,
        )

        self.assertEqual(
            observations[0].missing_digits,
            frozenset(range(10)),
        )

        self.assertEqual(
            observations[1].missing_digits,
            frozenset({0, 6, 7, 8, 9}),
        )

    def test_detects_target_completion(self) -> None:
        observation = build_prequential_replay(
            {
                "Bari": (
                    draw(1, (1, 23, 45, 67, 89)),
                    draw(2, (9, 12, 34, 56, 78)),
                )
            },
            start_target=2,
            end_target=2,
        )[0]

        self.assertTrue(observation.completed)
        self.assertEqual(
            observation.remaining_before_reset,
            frozenset(),
        )

    def test_probability_is_frozen_from_previous_state(self) -> None:
        observation = build_prequential_replay(
            {
                "Bari": (
                    draw(1, (1, 23, 45, 67, 89)),
                    draw(2, (11, 22, 33, 44, 55)),
                )
            },
            start_target=2,
            end_target=2,
        )[0]

        self.assertAlmostEqual(
            observation.probability(1),
            0.0004,
            places=3,
        )

    def test_rejects_unaligned_wheels(self) -> None:
        with self.assertRaises(ValueError):
            build_prequential_replay(
                {
                    "Bari": (
                        draw(1, (1, 23, 45, 67, 89)),
                        draw(2, (11, 22, 33, 44, 55)),
                    ),
                    "Roma": (
                        draw(
                            1,
                            (1, 23, 45, 67, 89),
                            wheel="Roma",
                            wheel_order=2,
                        ),
                    ),
                },
                start_target=2,
            )

    def test_rejects_unsynchronized_history(self) -> None:
        with self.assertRaises(ValueError):
            build_prequential_replay(
                {
                    "Bari": (
                        draw(1, (11, 22, 33, 44, 55)),
                        draw(2, (11, 22, 33, 44, 55)),
                    )
                },
                start_target=2,
                end_target=2,
            )


if __name__ == "__main__":
    unittest.main()
