from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "view_lotto_database.sh"

HIGHLIGHT = "\033[1;30;46m"
RESET = "\033[0m"


class ViewLottoDatabaseTests(unittest.TestCase):
    def create_database(self, path: Path) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                CREATE TABLE draws (
                    draw_number INTEGER NOT NULL,
                    draw_date TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE v_draw_numbers (
                    draw_number INTEGER NOT NULL,
                    draw_date TEXT NOT NULL,
                    wheel TEXT NOT NULL,
                    wheel_order INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    value_padded TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                INSERT INTO draws (
                    draw_number,
                    draw_date
                )
                VALUES (?, ?)
                """,
                (
                    121,
                    "2026-07-31",
                ),
            )

            for position, number in enumerate(
                (
                    1,
                    17,
                    23,
                    67,
                    90,
                ),
                start=1,
            ):
                connection.execute(
                    """
                    INSERT INTO v_draw_numbers (
                        draw_number,
                        draw_date,
                        wheel,
                        wheel_order,
                        position,
                        value_padded
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        121,
                        "2026-07-31",
                        "Bari",
                        1,
                        position,
                        f"{number:02d}",
                    ),
                )

    def run_script(
        self,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            database = temporary_path / "lotto.sqlite3"
            binary_directory = temporary_path / "bin"
            less = binary_directory / "less"

            binary_directory.mkdir()
            self.create_database(database)

            less.write_text(
                "#!/usr/bin/env bash\n"
                'cat "${@: -1}"\n'
            )
            less.chmod(0o755)

            environment = os.environ.copy()
            environment["PATH"] = (
                f"{binary_directory}:"
                f"{environment['PATH']}"
            )

            return subprocess.run(
                [
                    str(SCRIPT),
                    "--database",
                    str(database),
                    *arguments,
                ],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_help_documents_number_option(self) -> None:
        result = subprocess.run(
            [
                str(SCRIPT),
                "--help",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn(
            "--number NUMERI",
            result.stdout,
        )
        self.assertIn(
            "numeri da 1 a 90",
            result.stdout,
        )

    def test_highlights_numbers_and_digits_together(self) -> None:
        result = self.run_script(
            "--digit",
            "7",
            "--number",
            "23,1",
            "--number",
            "90,23",
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertIn(
            "Cifre evidenziate: 7",
            result.stdout,
        )
        self.assertIn(
            "Numeri evidenziati: 1, 23, 90",
            result.stdout,
        )
        self.assertIn(
            f"{HIGHLIGHT}01{RESET}",
            result.stdout,
        )
        self.assertIn(
            f"{HIGHLIGHT}23{RESET}",
            result.stdout,
        )
        self.assertIn(
            f"{HIGHLIGHT}90{RESET}",
            result.stdout,
        )
        self.assertIn(
            f"1{HIGHLIGHT}7{RESET}",
            result.stdout,
        )
        self.assertIn(
            f"6{HIGHLIGHT}7{RESET}",
            result.stdout,
        )

    def test_rejects_invalid_numbers(self) -> None:
        for value in (
            "0",
            "91",
            "-1",
            "1.5",
            "1,,2",
            "banana",
        ):
            with self.subTest(value=value):
                result = self.run_script(
                    "--number",
                    value,
                )

                self.assertEqual(
                    result.returncode,
                    2,
                )
                self.assertIn(
                    "--number accetta soltanto numeri interi",
                    result.stderr,
                )

    def test_rejects_number_without_value(self) -> None:
        result = self.run_script("--number")

        self.assertEqual(
            result.returncode,
            2,
        )
        self.assertIn(
            "--number richiede almeno un numero",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
