from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import lotto


class LottoConsensusTwinsDispatchTests(unittest.TestCase):
    def run_dispatch(self, arguments: list[str]) -> list[str]:
        with patch(
            "lotto.subprocess.run",
            return_value=SimpleNamespace(returncode=0),
        ) as runner:
            exit_code = lotto.main(arguments)

        self.assertEqual(exit_code, 0)
        return runner.call_args.args[0]

    def test_current_uses_consensus_wrapper(self) -> None:
        command = self.run_dispatch(["current", "--to-num", "127"])

        self.assertTrue(command[1].endswith("analyze_current_consensus.py"))
        self.assertEqual(command[-2:], ["--to-num", "127"])

    def test_twins_and_gemelli_use_same_analyzer(self) -> None:
        twins = self.run_dispatch(["twins"])
        gemelli = self.run_dispatch(["gemelli"])

        self.assertTrue(twins[1].endswith("analyze_twin_numbers.py"))
        self.assertEqual(twins, gemelli)


if __name__ == "__main__":
    unittest.main()
