from __future__ import annotations

from collections.abc import Callable
import os
import re
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "view_lotto_database.sh"

HIGHLIGHT = "\033[1;30;46m"
RESET = "\033[0m"

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

ANSI_PATTERN = re.compile(
    r"\x1b\[[0-9;]*m"
)


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

    def create_historical_database(
        self,
        path: Path,
    ) -> None:
        self.create_database(path)

        with sqlite3.connect(path) as connection:
            connection.execute(
                "DELETE FROM v_draw_numbers"
            )
            connection.execute(
                "DELETE FROM draws"
            )

            draws = (
                (122, "2026-08-04"),
                (120, "2026-07-31"),
                (121, "2026-08-02"),
            )

            custom_results = {
                (120, "Bari"): (1, 12, 23, 34, 46),
                (121, "Bari"): (1, 12, 23, 56, 67),
                (122, "Bari"): (1, 12, 23, 34, 9),
                (120, "Roma"): (1, 12, 23, 34, 9),
                (121, "Roma"): (50, 60, 70, 80, 90),
                (122, "Roma"): (50, 60, 70, 80, 90),
            }

            for draw_number, draw_date in draws:
                connection.execute(
                    """
                    INSERT INTO draws (
                        draw_number,
                        draw_date
                    )
                    VALUES (?, ?)
                    """,
                    (
                        draw_number,
                        draw_date,
                    ),
                )

                for wheel_order, wheel in enumerate(
                    EXPECTED_WHEELS,
                    start=1,
                ):
                    numbers = custom_results.get(
                        (
                            draw_number,
                            wheel,
                        )
                    )

                    if numbers is None:
                        first_number = (
                            10
                            + wheel_order * 6
                        )
                        numbers = tuple(
                            first_number + offset
                            for offset in range(5)
                        )

                    for position, number in enumerate(
                        numbers,
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
                                draw_number,
                                draw_date,
                                wheel,
                                wheel_order,
                                position,
                                f"{number:02d}",
                            ),
                        )

    def insert_draw(
        self,
        path: Path,
        draw_number: int,
        draw_date: str,
        wheels: tuple[str, ...] = EXPECTED_WHEELS,
    ) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                INSERT INTO draws (
                    draw_number,
                    draw_date
                )
                VALUES (?, ?)
                """,
                (
                    draw_number,
                    draw_date,
                ),
            )

            for wheel_order, wheel in enumerate(
                wheels,
                start=1,
            ):
                for position, number in enumerate(
                    (
                        1,
                        12,
                        23,
                        34,
                        45,
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
                            draw_number,
                            draw_date,
                            wheel,
                            wheel_order,
                            position,
                            f"{number:02d}",
                        ),
                    )

    def delete_wheel(
        self,
        path: Path,
        draw_number: int,
        draw_date: str,
        wheel: str,
    ) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                DELETE FROM v_draw_numbers
                WHERE
                    draw_number = ?
                    AND draw_date = ?
                    AND wheel = ?
                """,
                (
                    draw_number,
                    draw_date,
                    wheel,
                ),
            )

    def delete_all_draws(
        self,
        path: Path,
    ) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                "DELETE FROM v_draw_numbers"
            )
            connection.execute(
                "DELETE FROM draws"
            )

    def delete_number(
        self,
        path: Path,
        draw_number: int,
        draw_date: str,
        wheel: str,
        position: int,
    ) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                DELETE FROM v_draw_numbers
                WHERE
                    draw_number = ?
                    AND draw_date = ?
                    AND wheel = ?
                    AND position = ?
                """,
                (
                    draw_number,
                    draw_date,
                    wheel,
                    position,
                ),
            )

    def replace_value(
        self,
        path: Path,
        draw_number: int,
        draw_date: str,
        wheel: str,
        position: int,
        value: str,
    ) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                UPDATE v_draw_numbers
                SET value_padded = ?
                WHERE
                    draw_number = ?
                    AND draw_date = ?
                    AND wheel = ?
                    AND position = ?
                """,
                (
                    value,
                    draw_number,
                    draw_date,
                    wheel,
                    position,
                ),
            )

    def run_historical_script(
        self,
        *arguments: str,
        mutate: Callable[[Path], None] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            database = temporary_path / "historical.sqlite3"
            binary_directory = temporary_path / "bin"
            less = binary_directory / "less"

            binary_directory.mkdir()
            self.create_historical_database(database)

            if mutate is not None:
                mutate(database)

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

    def rendered_draw_numbers(
        self,
        output: str,
    ) -> list[int]:
        draw_numbers: list[int] = []

        for line in output.splitlines():
            match = re.match(
                r"^\s*(\d+)\s+\d{2}-\d{2}\s+",
                line,
            )

            if match is not None:
                draw_numbers.append(
                    int(match.group(1))
                )

        return draw_numbers

    def rendered_draw_line(
        self,
        output: str,
        draw_number: int,
    ) -> str:
        pattern = re.compile(
            rf"^\s*{draw_number}\s+\d{{2}}-\d{{2}}\s+"
        )

        for line in output.splitlines():
            if pattern.match(line):
                return line

        self.fail(
            f"Riga estrazione {draw_number} non trovata."
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

    def test_help_documents_latest_occurrences_option(self) -> None:
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
            "--latest-occurrences [NUM_ESTRAZIONE]",
            result.stdout,
        )
        self.assertIn(
            "ultima estrazione completa",
            result.stdout,
        )

    def test_latest_occurrences_does_not_consume_following_option(
        self,
    ) -> None:
        result = subprocess.run(
            [
                str(SCRIPT),
                "--latest-occurrences",
                "--help",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertIn(
            "--latest-occurrences [NUM_ESTRAZIONE]",
            result.stdout,
        )

    def test_rejects_ambiguous_database_path_after_latest_occurrences(
        self,
    ) -> None:
        result = subprocess.run(
            [
                str(SCRIPT),
                "--latest-occurrences",
                "data/lotto-2025.sqlite3",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            2,
        )
        self.assertIn(
            "forma ambigua",
            result.stderr,
        )
        self.assertIn(
            "--database PATH",
            result.stderr,
        )

    def test_rejects_invalid_latest_occurrences_draw_numbers(
        self,
    ) -> None:
        for value in (
            "0",
            "-1",
            "1.5",
            "banana",
        ):
            with self.subTest(value=value):
                result = self.run_script(
                    "--latest-occurrences",
                    value,
                )

                self.assertEqual(
                    result.returncode,
                    2,
                )
                self.assertIn(
                    "--latest-occurrences accetta soltanto "
                    "un numero di estrazione intero positivo",
                    result.stderr,
                )

    def test_rejects_latest_occurrences_with_manual_highlights(
        self,
    ) -> None:
        for option, value in (
            ("--digit", "7"),
            ("--number", "17"),
        ):
            with self.subTest(option=option):
                result = self.run_script(
                    "--latest-occurrences",
                    option,
                    value,
                )

                self.assertEqual(
                    result.returncode,
                    2,
                )
                self.assertIn(
                    "--latest-occurrences non è compatibile "
                    "con --digit o --number",
                    result.stderr,
                )


    def test_plain_database_rendering_keeps_ascending_order(
        self,
    ) -> None:
        result = self.run_historical_script()

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertNotIn(
            "Riferimento:",
            result.stdout,
        )
        self.assertEqual(
            self.rendered_draw_numbers(
                result.stdout,
            ),
            [
                120,
                121,
                122,
            ],
        )

    def test_latest_occurrences_preserves_visible_row_widths(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )

        rendered_lines = [
            self.rendered_draw_line(
                result.stdout,
                draw_number,
            )
            for draw_number in (
                122,
                121,
                120,
            )
        ]

        visible_widths = {
            len(
                ANSI_PATTERN.sub(
                    "",
                    line,
                )
            )
            for line in rendered_lines
        }

        self.assertEqual(
            len(visible_widths),
            1,
            visible_widths,
        )

    def test_latest_occurrences_defaults_to_latest_complete_draw(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertRegex(
            result.stdout,
            (
                r"Riferimento:\s+automatico"
                r" — estrazione 122"
                r" del 2026-08-04"
            ),
        )
        self.assertEqual(
            self.rendered_draw_numbers(
                result.stdout,
            ),
            [
                122,
                121,
                120,
            ],
        )

    def test_latest_occurrences_explicit_draw_applies_cutoff(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            "121",
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertRegex(
            result.stdout,
            (
                r"Riferimento:\s+esplicito"
                r" — estrazione 121"
                r" del 2026-08-02"
            ),
        )
        self.assertEqual(
            self.rendered_draw_numbers(
                result.stdout,
            ),
            [
                121,
                120,
            ],
        )

    def test_latest_occurrences_colors_reference_and_history(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertEqual(
            len(set(OCCURRENCE_HIGHLIGHTS)),
            5,
        )

        reference_line = self.rendered_draw_line(
            result.stdout,
            122,
        )

        bari_reference = (
            "01",
            "12",
            "23",
            "34",
            "09",
        )

        for color, number in zip(
            OCCURRENCE_HIGHLIGHTS,
            bari_reference,
            strict=True,
        ):
            self.assertIn(
                f"{color}{number}{RESET}",
                reference_line,
            )

        self.assertEqual(
            result.stdout.count(
                f"{OCCURRENCE_HIGHLIGHTS[0]}01{RESET}"
            ),
            3,
        )
        self.assertEqual(
            result.stdout.count(
                f"{OCCURRENCE_HIGHLIGHTS[1]}12{RESET}"
            ),
            3,
        )
        self.assertEqual(
            result.stdout.count(
                f"{OCCURRENCE_HIGHLIGHTS[2]}23{RESET}"
            ),
            3,
        )
        self.assertEqual(
            result.stdout.count(
                f"{OCCURRENCE_HIGHLIGHTS[3]}34{RESET}"
            ),
            2,
        )
        self.assertEqual(
            result.stdout.count(
                f"{OCCURRENCE_HIGHLIGHTS[4]}09{RESET}"
            ),
            1,
        )

    def test_latest_occurrences_isolates_wheels_and_reuses_palette(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )

        reference_line = self.rendered_draw_line(
            result.stdout,
            122,
        )

        self.assertIn(
            f"{OCCURRENCE_HIGHLIGHTS[0]}50{RESET}",
            reference_line,
        )
        self.assertIn(
            f"{OCCURRENCE_HIGHLIGHTS[1]}60{RESET}",
            reference_line,
        )

        self.assertEqual(
            result.stdout.count(
                f"{OCCURRENCE_HIGHLIGHTS[0]}01{RESET}"
            ),
            3,
        )

    def test_latest_occurrences_skips_newer_incomplete_draw(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            mutate=lambda database: self.insert_draw(
                database,
                123,
                "2026-08-06",
                (
                    "Bari",
                ),
            ),
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )
        self.assertIn(
            "automatico — estrazione 122 del 2026-08-04",
            result.stdout,
        )
        self.assertEqual(
            self.rendered_draw_numbers(
                result.stdout,
            ),
            [
                122,
                121,
                120,
            ],
        )

    def test_latest_occurrences_rejects_unknown_explicit_draw(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            "999",
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "estrazione di riferimento 999 non trovata",
            result.stderr,
        )

    def test_latest_occurrences_rejects_ambiguous_explicit_draw(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            "121",
            mutate=lambda database: self.insert_draw(
                database,
                121,
                "2026-08-03",
            ),
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "numero di estrazione ambiguo: 121",
            result.stderr,
        )

    def test_latest_occurrences_rejects_ambiguous_draw_with_incomplete_candidate(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            "121",
            mutate=lambda database: self.insert_draw(
                database,
                121,
                "2026-08-03",
                (
                    "Bari",
                ),
            ),
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "numero di estrazione ambiguo: 121",
            result.stderr,
        )

    def test_latest_occurrences_rejects_incomplete_explicit_draw(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            "121",
            mutate=lambda database: self.delete_wheel(
                database,
                121,
                "2026-08-02",
                "Nazionale",
            ),
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "ruota attesa mancante: Nazionale",
            result.stderr,
        )

    def test_latest_occurrences_rejects_empty_database(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            mutate=self.delete_all_draws,
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "nessuna estrazione completa disponibile",
            result.stderr,
        )

    def test_latest_occurrences_rejects_database_without_complete_draws(
        self,
    ) -> None:
        def make_all_draws_incomplete(
            database: Path,
        ) -> None:
            for draw_number, draw_date in (
                (120, "2026-07-31"),
                (121, "2026-08-02"),
                (122, "2026-08-04"),
            ):
                self.delete_wheel(
                    database,
                    draw_number,
                    draw_date,
                    "Nazionale",
                )

        result = self.run_historical_script(
            "--latest-occurrences",
            mutate=make_all_draws_incomplete,
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "nessuna estrazione completa disponibile",
            result.stderr,
        )

    def test_latest_occurrences_rejects_reference_wheel_with_four_values(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            "121",
            mutate=lambda database: self.delete_number(
                database,
                121,
                "2026-08-02",
                "Bari",
                5,
            ),
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "la ruota Bari contiene 4 valori anziché 5",
            result.stderr,
        )

    def test_latest_occurrences_rejects_out_of_range_values(
        self,
    ) -> None:
        result = self.run_historical_script(
            "--latest-occurrences",
            mutate=lambda database: self.replace_value(
                database,
                122,
                "2026-08-04",
                "Bari",
                1,
                "00",
            ),
        )

        self.assertEqual(
            result.returncode,
            1,
        )
        self.assertIn(
            "valore fuori dall'intervallo 01–90",
            result.stderr,
        )
        self.assertIn(
            "Bari",
            result.stderr,
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
