from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from strategies.coverage_checkpoint import (
    ArchiveSegment,
    MutableWheelState,
    WheelCheckpoint,
    apply_draws,
    checkpoint_payload,
    freeze_state,
    previous_complete_year,
    read_checkpoint,
    resolve_archive_chain,
    semantic_checkpoint_state,
    states_from_checkpoint,
    validate_checkpoint_payload,
    write_checkpoint,
)
from strategies.lotto_repository import DrawSnapshot


def draw(
    number: int,
    draw_date: str,
    numbers: tuple[int, ...],
) -> DrawSnapshot:
    return DrawSnapshot(
        draw_number=number,
        draw_date=draw_date,
        wheel="Bari",
        wheel_order=1,
        numbers=numbers,
    )


class CoverageCheckpointTests(unittest.TestCase):
    def test_previous_complete_year_is_dynamic(
        self,
    ) -> None:
        self.assertEqual(
            previous_complete_year(2026),
            2025,
        )
        self.assertEqual(
            previous_complete_year(2034),
            2033,
        )

    def test_prefers_partial_consolidated_chain(
        self,
    ) -> None:
        segments = (
            ArchiveSegment(
                1871,
                2025,
                Path("overall.sqlite3"),
            ),
            ArchiveSegment(
                1871,
                1900,
                Path("first.sqlite3"),
            ),
            ArchiveSegment(
                1901,
                1950,
                Path("second.sqlite3"),
            ),
            ArchiveSegment(
                1951,
                2000,
                Path("third.sqlite3"),
            ),
            ArchiveSegment(
                2001,
                2020,
                Path("fourth.sqlite3"),
            ),
            ArchiveSegment(
                2021,
                2025,
                Path("fifth.sqlite3"),
            ),
        )

        chain = resolve_archive_chain(
            segments,
            first_year=1871,
            last_year=2025,
        )

        self.assertEqual(
            [
                (
                    segment.first_year,
                    segment.last_year,
                )
                for segment in chain
            ],
            [
                (1871, 1900),
                (1901, 1950),
                (1951, 2000),
                (2001, 2020),
                (2021, 2025),
            ],
        )

    def test_prefers_consolidated_over_annual_start(
        self,
    ) -> None:
        segments = (
            ArchiveSegment(
                1871,
                1871,
                Path("lotto-1871.sqlite3"),
            ),
            ArchiveSegment(
                1871,
                1900,
                Path("lotto-1871-1900.sqlite3"),
            ),
            ArchiveSegment(
                1871,
                2025,
                Path("lotto-1871-2025.sqlite3"),
            ),
        )

        chain = resolve_archive_chain(
            segments,
            first_year=1871,
            last_year=1900,
        )

        self.assertEqual(
            chain,
            (
                ArchiveSegment(
                    1871,
                    1900,
                    Path("lotto-1871-1900.sqlite3"),
                ),
            ),
        )

    def test_uses_annual_tail_for_next_year(
        self,
    ) -> None:
        segments = (
            ArchiveSegment(
                1871,
                2025,
                Path("overall.sqlite3"),
            ),
            ArchiveSegment(
                1871,
                1900,
                Path("first.sqlite3"),
            ),
            ArchiveSegment(
                1901,
                1950,
                Path("second.sqlite3"),
            ),
            ArchiveSegment(
                1951,
                2000,
                Path("third.sqlite3"),
            ),
            ArchiveSegment(
                2001,
                2020,
                Path("fourth.sqlite3"),
            ),
            ArchiveSegment(
                2021,
                2025,
                Path("fifth.sqlite3"),
            ),
            ArchiveSegment(
                2026,
                2026,
                Path("lotto-2026.sqlite3"),
            ),
        )

        chain = resolve_archive_chain(
            segments,
            first_year=1871,
            last_year=2026,
        )

        self.assertEqual(
            chain[-1].path,
            Path("lotto-2026.sqlite3"),
        )

    def test_checkpoint_resume_matches_continuous_run(
        self,
    ) -> None:
        first_part = (
            draw(
                208,
                "2025-12-30",
                (1, 2, 3, 4, 5),
            ),
            draw(
                209,
                "2025-12-31",
                (6, 7, 8, 9, 10),
            ),
        )
        second_part = (
            draw(
                1,
                "2026-01-02",
                (11, 22, 33, 44, 55),
            ),
            draw(
                2,
                "2026-01-04",
                (66, 77, 88, 89, 90),
            ),
        )

        continuous = {}
        apply_draws(
            continuous,
            (*first_part, *second_part),
        )

        resumed = {}
        apply_draws(
            resumed,
            first_part,
        )
        apply_draws(
            resumed,
            second_part,
        )

        self.assertEqual(
            freeze_state(continuous["Bari"]),
            freeze_state(resumed["Bari"]),
        )

    def test_json_round_trip_preserves_resume_state(
        self,
    ) -> None:
        states = {}

        apply_draws(
            states,
            (
                draw(
                    208,
                    "2025-12-30",
                    (1, 2, 3, 4, 5),
                ),
                draw(
                    209,
                    "2025-12-31",
                    (6, 7, 8, 8, 9),
                ),
            ),
        )

        frozen = freeze_state(states["Bari"])

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite3"
            source.write_bytes(b"test")

            payload = checkpoint_payload(
                current_year=2026,
                checkpoint_year=2025,
                checkpoint_date="2025-12-31",
                chain=(
                    ArchiveSegment(
                        2025,
                        2025,
                        source,
                    ),
                ),
                states=(frozen,),
                total_draws=2,
            )

            destination = (
                Path(directory) / "checkpoint.json"
            )

            write_checkpoint(
                payload,
                destination,
            )

            loaded = read_checkpoint(destination)
            restored = states_from_checkpoint(
                loaded
            )

        self.assertEqual(
            freeze_state(restored["Bari"]),
            frozen,
        )

        next_draw = draw(
            1,
            "2026-01-02",
            (10, 20, 30, 40, 50),
        )

        apply_draws(states, (next_draw,))
        apply_draws(restored, (next_draw,))

        self.assertEqual(
            freeze_state(restored["Bari"]),
            freeze_state(states["Bari"]),
        )

    def test_rejects_incoherent_digit_partition(
        self,
    ) -> None:
        payload = {
            "schema_version": 1,
            "artifact_family": (
                "historical-coverage-checkpoint"
            ),
            "current_year": 2026,
            "checkpoint_year": 2025,
            "checkpoint_date": "2025-12-30",
            "source_archives": [
                {"path": "source.sqlite3"}
            ],
            "wheels": [
                {
                    "wheel": "Bari",
                    "wheel_order": 1,
                    "latest_draw": 1,
                    "latest_date": "2025-12-30",
                    "completed_cycles": 1,
                    "synchronized": True,
                    "draws_in_cycle": 1,
                    "cycle_start_draw": 1,
                    "cycle_start_date": "2025-12-30",
                    "covered_digits": [0, 1],
                    "missing_digits": [1, 2, 3],
                    "digit_occurrences": [0] * 10,
                    "most_present_digits": [],
                }
            ],
        }

        with self.assertRaises(ValueError):
            validate_checkpoint_payload(payload)

    def test_semantic_state_ignores_source_local_draw_numbers(
        self,
    ) -> None:
        first = WheelCheckpoint(
            wheel="Bari",
            wheel_order=1,
            latest_draw=912,
            latest_date="2025-12-30",
            completed_cycles=10,
            synchronized=True,
            draws_in_cycle=2,
            cycle_start_draw=911,
            cycle_start_date="2025-12-29",
            covered_digits=(0, 1, 2),
            missing_digits=(3, 4, 5, 6, 7, 8, 9),
            digit_occurrences=(
                1,
                2,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ),
            most_present_digits=(1,),
        )

        second = WheelCheckpoint(
            wheel="Bari",
            wheel_order=1,
            latest_draw=10779,
            latest_date="2025-12-30",
            completed_cycles=10,
            synchronized=True,
            draws_in_cycle=2,
            cycle_start_draw=10778,
            cycle_start_date="2025-12-29",
            covered_digits=(0, 1, 2),
            missing_digits=(3, 4, 5, 6, 7, 8, 9),
            digit_occurrences=(
                1,
                2,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ),
            most_present_digits=(1,),
        )

        self.assertNotEqual(first, second)
        self.assertEqual(
            semantic_checkpoint_state(first),
            semantic_checkpoint_state(second),
        )

    def test_freezes_occurrences_needed_for_resume(
        self,
    ) -> None:
        states: dict[str, MutableWheelState] = {}

        apply_draws(
            states,
            (
                draw(
                    1,
                    "2026-01-02",
                    (11, 12, 13, 14, 15),
                ),
            ),
        )

        checkpoint = freeze_state(
            states["Bari"]
        )

        self.assertEqual(
            checkpoint.draws_in_cycle,
            1,
        )
        self.assertEqual(
            checkpoint.cycle_start_date,
            "2026-01-02",
        )
        self.assertEqual(
            len(checkpoint.digit_occurrences),
            10,
        )
        self.assertEqual(
            checkpoint.digit_occurrences[1],
            6,
        )


if __name__ == "__main__":
    unittest.main()
