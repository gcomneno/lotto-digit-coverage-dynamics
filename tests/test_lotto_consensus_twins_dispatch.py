from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import lotto


class LottoConsensusTwinsDispatchTests(unittest.TestCase):
    def run_legacy_dispatch(self, arguments: list[str]) -> list[str]:
        with patch(
            "lotto.subprocess.run",
            return_value=SimpleNamespace(returncode=0),
        ) as runner:
            exit_code = lotto.main(arguments)

        self.assertEqual(exit_code, 0)
        return runner.call_args.args[0]

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

    def test_twins_and_gemelli_use_same_legacy_analyzer(self) -> None:
        twins = self.run_legacy_dispatch(["twins"])
        gemelli = self.run_legacy_dispatch(["gemelli"])

        self.assertTrue(twins[1].endswith("analyze_twin_numbers.py"))
        self.assertEqual(twins, gemelli)


if __name__ == "__main__":
    unittest.main()
