from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import lotto
from lotto_digit_coverage.interfaces.gui import launcher


class GuiLauncherTests(unittest.TestCase):
    def test_help_does_not_require_frontend_or_pywebview(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            result = launcher.main(("--help",))

        self.assertEqual(result, 0)
        self.assertIn("./lotto.py gui", output.getvalue())

    def test_gui_command_uses_direct_optional_launcher(self) -> None:
        with patch(
            "lotto.run_direct_command",
            return_value=0,
        ) as direct, patch("lotto.subprocess.run") as subprocess_run:
            result = lotto.main(("gui",))

        self.assertEqual(result, 0)
        direct.assert_called_once_with("gui", [])
        subprocess_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
