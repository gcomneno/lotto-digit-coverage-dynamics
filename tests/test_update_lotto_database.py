from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from import_lotto import Draw
from update_lotto_database import (
    DatabaseRange,
    read_database_range,
    validate_complete_archive,
)


def archive_draw(
    number: int,
) -> Draw:
    return Draw(
        number=number,
        date="2026-01-01",
        wheels=(),
    )


class UpdateLottoDatabaseTests(unittest.TestCase):
    def create_database(
        self,
        path: Path,
        draw_numbers: tuple[int, ...],
    ) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                CREATE TABLE draws (
                    draw_number INTEGER PRIMARY KEY,
                    draw_date TEXT NOT NULL
                )
                """
            )

            connection.executemany(
                """
                INSERT INTO draws(
                    draw_number,
                    draw_date
                )
                VALUES (?, ?)
                """,
                [
                    (
                        number,
                        f"2026-01-{number:02d}",
                    )
                    for number in draw_numbers
                ],
            )

    def test_reads_contiguous_database_range(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = (
                Path(directory)
                / "lotto.sqlite3"
            )

            self.create_database(
                database,
                (1, 2, 3),
            )

            self.assertEqual(
                read_database_range(database),
                DatabaseRange(
                    count=3,
                    first_draw=1,
                    last_draw=3,
                    latest_date="2026-01-03",
                ),
            )

    def test_rejects_database_gap(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = (
                Path(directory)
                / "lotto.sqlite3"
            )

            self.create_database(
                database,
                (1, 3),
            )

            with self.assertRaises(ValueError):
                read_database_range(database)

    def test_accepts_complete_annual_archive(
        self,
    ) -> None:
        draws = (
            archive_draw(4),
            archive_draw(3),
            archive_draw(2),
            archive_draw(1),
        )

        self.assertEqual(
            validate_complete_archive(draws),
            draws,
        )

    def test_rejects_archive_without_draw_one(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "sequenza completa",
        ):
            validate_complete_archive(
                (
                    archive_draw(4),
                    archive_draw(3),
                    archive_draw(2),
                )
            )

    def test_rejects_archive_with_internal_gap(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "sequenza completa",
        ):
            validate_complete_archive(
                (
                    archive_draw(4),
                    archive_draw(2),
                    archive_draw(1),
                )
            )


if __name__ == "__main__":
    unittest.main()
