from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import lotto


class LottoDispatcherTests(unittest.TestCase):
    def run_dispatch(
        self,
        arguments: list[str],
    ) -> list[str]:
        with patch(
            "lotto.subprocess.run",
            return_value=SimpleNamespace(
                returncode=0,
            ),
        ) as runner:
            exit_code = lotto.main(arguments)

        self.assertEqual(exit_code, 0)

        command = runner.call_args.args[0]
        return command

    def test_db_without_subcommand_opens_viewer(
        self,
    ) -> None:
        command = self.run_dispatch(["db"])

        self.assertTrue(
            command[0].endswith(
                "view_lotto_database.sh"
            )
        )

    def test_db_update_uses_range_orchestrator(
        self,
    ) -> None:
        command = self.run_dispatch(
            [
                "db",
                "update",
                "--year",
                "2025",
            ]
        )

        self.assertTrue(
            command[1].endswith(
                "update_lotto_databases.py"
            )
        )
        self.assertEqual(
            command[-2:],
            ["--year", "2025"],
        )

    def test_help_db_update_targets_orchestrator(
        self,
    ) -> None:
        command = self.run_dispatch(
            [
                "help",
                "db",
                "update",
            ]
        )

        self.assertTrue(
            command[1].endswith(
                "update_lotto_databases.py"
            )
        )
        self.assertEqual(
            command[-1],
            "--help",
        )


if __name__ == "__main__":
    unittest.main()
