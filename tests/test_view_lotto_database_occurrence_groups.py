from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "view_lotto_database.sh"

EXPECTED_WHEELS = (
    "Bari",
    "Cagliari",
    "Firenze",
    "Genova",
    "Milano",
    "Napoli",
    "Palermo",
    "Roma",
    "Torino",
    "Venezia",
    "Nazionale",
)

OCCURRENCE_HIGHLIGHTS = (
    "\033[1;30;41m",
    "\033[1;30;42m",
    "\033[1;30;43m",
    "\033[1;30;44m",
    "\033[1;30;45m",
)

RESET = "\033[0m"
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


class OccurrenceGroupViewerTests(unittest.TestCase):
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

            draws = (
                (120, "2026-07-31"),
                (121, "2026-08-02"),
                (122, "2026-08-04"),
            )
            bari = {
                120: (1, 12, 23, 34, 46),
                121: (1, 12, 23, 56, 67),
                122: (1, 12, 23, 34, 9),
            }
            roma = {
                120: (1, 12, 23, 34, 9),
                121: (50, 60, 70, 80, 90),
                122: (50, 60, 70, 80, 90),
            }

            for draw_number, draw_date in draws:
                connection.execute(
                    "INSERT INTO draws (draw_number, draw_date) VALUES (?, ?)",
                    (draw_number, draw_date),
                )

                for wheel_order, wheel in enumerate(
                    EXPECTED_WHEELS,
                    start=1,
                ):
                    if wheel == "Bari":
                        numbers = bari[draw_number]
                    elif wheel == "Roma":
                        numbers = roma[draw_number]
                    else:
                        first = 10 + wheel_order * 6
                        numbers = tuple(first + offset for offset in range(5))

                    for position, number in enumerate(numbers, start=1):
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
                                draw_number,
                                draw_date,
                                wheel,
                                wheel_order,
                                position,
                                f"{number:02d}",
                            ),
                        )

    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            database = temporary_path / "lotto.sqlite3"
            binary_directory = temporary_path / "bin"
            less = binary_directory / "less"

            binary_directory.mkdir()
            self.create_database(database)
            less.write_text(
                "#!/usr/bin/env bash\n"
                'cat "${@: -1}"\n',
                encoding="utf-8",
            )
            less.chmod(0o755)

            environment = os.environ.copy()
            environment["PATH"] = (
                f"{binary_directory}:{environment['PATH']}"
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

    def test_help_documents_occurrence_groups(self) -> None:
        result = subprocess.run(
            [str(SCRIPT), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--occurrence-groups N", result.stdout)
        self.assertIn("propria estrazione più recente", result.stdout)

    def test_occurrence_groups_requires_latest_occurrences(self) -> None:
        result = self.run_script("--occurrence-groups", "2")

        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "--occurrence-groups richiede --latest-occurrences",
            result.stderr,
        )

    def test_occurrence_groups_rejects_invalid_sizes(self) -> None:
        for value in ("0", "-1", "1.5", "banana"):
            with self.subTest(value=value):
                result = self.run_script(
                    "--latest-occurrences",
                    "--occurrence-groups",
                    value,
                )

                self.assertEqual(result.returncode, 2)
                self.assertIn(
                    "--occurrence-groups accetta soltanto un intero positivo",
                    result.stderr,
                )

    def test_groups_separate_reference_from_counted_history(self) -> None:
        result = self.run_script(
            "--latest-occurrences",
            "--occurrence-groups",
            "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "Gruppo: riferimento 122 del 2026-08-04; "
            "analisi 121–120 (2 estrazioni conteggiate)",
            result.stdout,
        )
        self.assertNotIn("Gruppo: riferimento 120", result.stdout)

        group = result.stdout.split("Gruppo: riferimento ", 1)[1]
        plain_group = ANSI_PATTERN.sub("", group)
        self.assertIn("Rif.    122", plain_group)
        self.assertIn("Conta   121", plain_group)
        self.assertIn("Conta   120", plain_group)

        for color, count in zip(
            OCCURRENCE_HIGHLIGHTS,
            (2, 2, 2, 1, 0),
            strict=True,
        ):
            self.assertIn(
                f"{color}{count:02d}{RESET}",
                group,
            )

    def test_explicit_cutoff_becomes_first_group_reference(self) -> None:
        result = self.run_script(
            "--latest-occurrences",
            "121",
            "--occurrence-groups",
            "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "Riferimento:  esplicito — estrazione 121 del 2026-08-02",
            result.stdout,
        )
        self.assertIn(
            "Gruppo: riferimento 121 del 2026-08-02; "
            "analisi 120–120 (1 estrazioni conteggiate)",
            result.stdout,
        )
        self.assertIn("Rif.    121", ANSI_PATTERN.sub("", result.stdout))
        self.assertIn("Conta   120", ANSI_PATTERN.sub("", result.stdout))
        self.assertNotIn("Rif.    122", ANSI_PATTERN.sub("", result.stdout))


if __name__ == "__main__":
    unittest.main()
