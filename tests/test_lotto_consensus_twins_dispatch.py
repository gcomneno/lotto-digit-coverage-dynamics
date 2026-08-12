from __future__ import annotations

import unittest
from unittest.mock import patch

import lotto


class LottoConsensusTwinsDispatchTests(unittest.TestCase):
    def test_current_uses_direct_application_adapter(self) -> None:
        with patch(
            "lotto.run_direct_command",
            return_value=0,
        ) as direct:
            exit_code = lotto.main(["current", "--to-num", "127"])

        self.assertEqual(exit_code, 0)
        direct.assert_called_once_with(
            "current",
            ["--to-num", "127"],
        )

    def test_twins_and_gemelli_use_same_direct_analyzer(self) -> None:
        for command in ("twins", "gemelli"):
            with self.subTest(command=command):
                with patch(
                    "lotto.run_direct_command",
                    return_value=0,
                ) as direct, patch("lotto.subprocess.run") as subprocess_run:
                    exit_code = lotto.main([command])

                self.assertEqual(exit_code, 0)
                direct.assert_called_once_with("twins", [])
                subprocess_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
