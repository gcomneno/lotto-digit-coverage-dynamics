from __future__ import annotations

import unittest
from unittest.mock import patch

import lotto


class LottoHistoricalDirectDispatchTests(unittest.TestCase):
    def test_every_historical_analysis_command_is_direct(self) -> None:
        historical = tuple(
            tool.command
            for tool in lotto.TOOLS
            if tool.category == "Analisi storiche"
        )

        self.assertTrue(historical)
        self.assertTrue(set(historical).issubset(lotto.DIRECT_COMMANDS))

        for command in historical:
            with self.subTest(command=command):
                with patch(
                    "lotto.run_direct_command",
                    return_value=0,
                ) as direct, patch(
                    "lotto.subprocess.run",
                ) as subprocess_run:
                    result = lotto.main((command, "--help"))

                self.assertEqual(result, 0)
                direct.assert_called_once_with(command, ["--help"])
                subprocess_run.assert_not_called()

    def test_historical_aliases_resolve_to_canonical_direct_command(self) -> None:
        aliases = {
            alias: tool.command
            for tool in lotto.TOOLS
            if tool.category == "Analisi storiche"
            for alias in tool.aliases
        }
        for alias, command in aliases.items():
            with self.subTest(alias=alias):
                with patch(
                    "lotto.run_direct_command",
                    return_value=0,
                ) as direct:
                    result = lotto.main((alias, "--help"))

                self.assertEqual(result, 0)
                direct.assert_called_once_with(command, ["--help"])


if __name__ == "__main__":
    unittest.main()
