from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tools.generate_historical_databases as historical


class GenerateHistoricalDatabasesTests(unittest.TestCase):
    def test_resolves_inclusive_range(self) -> None:
        self.assertEqual(
            historical.resolve_years(
                1871,
                1873,
            ),
            (
                1871,
                1872,
                1873,
            ),
        )

    def test_rejects_reverse_range(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "anno iniziale",
        ):
            historical.resolve_years(
                1873,
                1871,
            )

    def test_default_command_keeps_going(self) -> None:
        arguments = argparse.Namespace(
            from_year=1871,
            to_year=1873,
            dry_run=False,
            fail_fast=False,
            source_directory=None,
        )

        command = historical.build_update_command(
            arguments
        )

        self.assertEqual(
            command[1:],
            [
                "db",
                "update",
                "--from-year",
                "1871",
                "--to-year",
                "1873",
                "--keep-going",
            ],
        )

    def test_fail_fast_omits_keep_going(self) -> None:
        arguments = argparse.Namespace(
            from_year=1871,
            to_year=1873,
            dry_run=True,
            fail_fast=True,
            source_directory=Path("sources"),
        )

        command = historical.build_update_command(
            arguments
        )

        self.assertNotIn(
            "--keep-going",
            command,
        )
        self.assertIn(
            "--dry-run",
            command,
        )
        self.assertEqual(
            command[-2:],
            [
                "--source-directory",
                "sources",
            ],
        )

    def test_verifies_present_integral_databases(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with patch.object(
                historical,
                "REPOSITORY_ROOT",
                root,
            ):
                data = root / "data"
                data.mkdir()

                for year in (
                    1871,
                    1872,
                ):
                    database = (
                        data
                        / f"lotto-{year}.sqlite3"
                    )

                    import sqlite3

                    with sqlite3.connect(database):
                        pass

                summary = (
                    historical.verify_databases(
                        (
                            1871,
                            1872,
                            1873,
                        )
                    )
                )

        self.assertEqual(
            summary.present_count,
            2,
        )
        self.assertEqual(
            summary.integral_count,
            2,
        )
        self.assertEqual(
            summary.missing_years,
            (1873,),
        )
        self.assertEqual(
            summary.invalid_years,
            (),
        )


if __name__ == "__main__":
    unittest.main()
