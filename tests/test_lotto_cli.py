from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

import lotto


class LottoCliTests(unittest.TestCase):
    def test_lists_all_registered_tools(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            result = lotto.main(("list",))

        rendered = output.getvalue()

        self.assertEqual(result, 0)
        self.assertIn(
            "CLI disponibili: 15",
            rendered,
        )

        for tool in lotto.TOOLS:
            with self.subTest(command=tool.command):
                self.assertIn(
                    tool.command,
                    rendered,
                )
                self.assertIn(
                    tool.script,
                    rendered,
                )

    def test_forwards_arguments_to_python_tool(self) -> None:
        completed = SimpleNamespace(returncode=7)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(
                (
                    "current",
                    "--to-num",
                    "119",
                )
            )

        self.assertEqual(result, 7)

        command = run.call_args.args[0]

        self.assertEqual(
            command[0],
            sys.executable,
        )
        self.assertEqual(
            command[1],
            str(
                lotto.ROOT
                / "analyze_current_coverage.py"
            ),
        )
        self.assertEqual(
            command[2:],
            [
                "--to-num",
                "119",
            ],
        )
        self.assertEqual(
            run.call_args.kwargs,
            {
                "cwd": lotto.ROOT,
                "check": False,
            },
        )

    def test_forwards_latest_occurrences_to_db_tool(
        self,
    ) -> None:
        completed = SimpleNamespace(returncode=0)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(
                (
                    "db",
                    "--database",
                    "data/lotto-2025.sqlite3",
                    "--latest-occurrences",
                    "100",
                )
            )

        self.assertEqual(result, 0)
        self.assertEqual(
            run.call_args.args[0],
            [
                str(
                    lotto.ROOT
                    / "view_lotto_database.sh"
                ),
                "--database",
                "data/lotto-2025.sqlite3",
                "--latest-occurrences",
                "100",
            ],
        )
        self.assertEqual(
            run.call_args.kwargs,
            {
                "cwd": lotto.ROOT,
                "check": False,
            },
        )

    def test_alias_selects_expected_tool(self) -> None:
        completed = SimpleNamespace(returncode=0)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(
                (
                    "now",
                    "--help",
                )
            )

        self.assertEqual(result, 0)
        self.assertEqual(
            run.call_args.args[0][1],
            str(
                lotto.ROOT
                / "analyze_current_coverage.py"
            ),
        )

    def test_help_forwards_to_selected_tool(self) -> None:
        completed = SimpleNamespace(returncode=0)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(
                (
                    "help",
                    "update",
                )
            )

        self.assertEqual(result, 0)
        self.assertEqual(
            run.call_args.args[0][-1],
            "--help",
        )

    def test_unknown_command_is_rejected(self) -> None:
        error = io.StringIO()

        with redirect_stderr(error):
            result = lotto.main(
                (
                    "radioactive-banana",
                )
            )

        self.assertEqual(result, 2)
        self.assertIn(
            "comando sconosciuto",
            error.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
