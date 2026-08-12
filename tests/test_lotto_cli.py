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
            f"CLI disponibili: {len(lotto.TOOLS)}",
            rendered,
        )

        for tool in lotto.TOOLS:
            with self.subTest(command=tool.command):
                display_command = (
                    "db update"
                    if tool.command == "db-update"
                    else tool.command
                )

                self.assertIn(display_command, rendered)
                self.assertIn(tool.script, rendered)

    def test_current_calls_direct_adapter_with_forwarded_arguments(self) -> None:
        with patch(
            "lotto.run_direct_command",
            return_value=7,
        ) as direct:
            result = lotto.main(
                ("current", "--to-num", "119")
            )

        self.assertEqual(result, 7)
        direct.assert_called_once_with(
            "current",
            ["--to-num", "119"],
        )

    def test_db_calls_direct_adapter_with_forwarded_arguments(self) -> None:
        with patch(
            "lotto.run_direct_command",
            return_value=0,
        ) as direct:
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
        direct.assert_called_once_with(
            "db",
            [
                "--database",
                "data/lotto-2025.sqlite3",
                "--latest-occurrences",
                "100",
            ],
        )

    def test_forwards_rolling_frequency_tool(self) -> None:
        completed = SimpleNamespace(returncode=0)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(
                (
                    "rolling-frequency",
                    "--repetitions",
                    "25",
                )
            )

        self.assertEqual(result, 0)
        self.assertEqual(
            run.call_args.args[0],
            [
                sys.executable,
                str(lotto.ROOT / "analyze_rolling_frequency.py"),
                "--repetitions",
                "25",
            ],
        )

    def test_forwards_coverage_hits_tool(self) -> None:
        completed = SimpleNamespace(returncode=0)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(
                (
                    "coverage-hits",
                    "--last",
                    "10",
                    "--details",
                )
            )

        self.assertEqual(result, 0)
        self.assertEqual(
            run.call_args.args[0],
            [
                sys.executable,
                str(lotto.ROOT / "analyze_coverage_hit_statistics.py"),
                "--last",
                "10",
                "--details",
            ],
        )

    def test_coverage_hits_alias_selects_legacy_tool(self) -> None:
        completed = SimpleNamespace(returncode=0)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(("hits", "--help"))

        self.assertEqual(result, 0)
        self.assertEqual(
            run.call_args.args[0][1],
            str(lotto.ROOT / "analyze_coverage_hit_statistics.py"),
        )

    def test_current_alias_selects_direct_adapter(self) -> None:
        with patch(
            "lotto.run_direct_command",
            return_value=0,
        ) as direct:
            result = lotto.main(("now", "--help"))

        self.assertEqual(result, 0)
        direct.assert_called_once_with("current", ["--help"])

    def test_help_forwards_to_selected_legacy_tool(self) -> None:
        completed = SimpleNamespace(returncode=0)

        with patch(
            "lotto.subprocess.run",
            return_value=completed,
        ) as run:
            result = lotto.main(("help", "update"))

        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.args[0][-1], "--help")

    def test_help_current_uses_direct_adapter(self) -> None:
        with patch(
            "lotto.run_direct_command",
            return_value=0,
        ) as direct:
            result = lotto.main(("help", "current"))

        self.assertEqual(result, 0)
        direct.assert_called_once_with("current", ["--help"])

    def test_unknown_command_is_rejected(self) -> None:
        error = io.StringIO()

        with redirect_stderr(error):
            result = lotto.main(("radioactive-banana",))

        self.assertEqual(result, 2)
        self.assertIn("comando sconosciuto", error.getvalue())


if __name__ == "__main__":
    unittest.main()
