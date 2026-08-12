from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import lotto


class LottoDispatcherTests(unittest.TestCase):
    def test_db_without_subcommand_uses_direct_viewer_adapter(self) -> None:
        with patch(
            "lotto.run_direct_command",
            return_value=0,
        ) as direct:
            exit_code = lotto.main(["db"])

        self.assertEqual(exit_code, 0)
        direct.assert_called_once_with("db", [])

    def run_legacy_dispatch(self, arguments: list[str]) -> list[str]:
        with patch(
            "lotto.subprocess.run",
            return_value=SimpleNamespace(returncode=0),
        ) as runner:
            exit_code = lotto.main(arguments)

        self.assertEqual(exit_code, 0)
        return runner.call_args.args[0]

    def test_db_update_uses_range_orchestrator(self) -> None:
        command = self.run_legacy_dispatch(
            ["db", "update", "--year", "2025"]
        )

        self.assertTrue(
            command[1].endswith("update_lotto_databases.py")
        )
        self.assertEqual(command[-2:], ["--year", "2025"])

    def test_help_db_update_targets_orchestrator(self) -> None:
        command = self.run_legacy_dispatch(
            ["help", "db", "update"]
        )

        self.assertTrue(
            command[1].endswith("update_lotto_databases.py")
        )
        self.assertEqual(command[-1], "--help")


if __name__ == "__main__":
    unittest.main()
