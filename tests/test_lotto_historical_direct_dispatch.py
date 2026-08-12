from __future__ import annotations

import unittest
from unittest.mock import patch

import lotto


class LottoHistoricalDirectDispatchTests(unittest.TestCase):
    def test_migrated_markov_commands_use_direct_dispatch(self) -> None:
        for command in ("completion", "residuals", "validation"):
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


if __name__ == "__main__":
    unittest.main()
