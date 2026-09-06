from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from lotto_digit_coverage.interfaces.cli.current_command import build_parser, main


class CurrentCliLocalizationTests(unittest.TestCase):
    def test_parser_defaults_to_english_and_supports_italian(self):
        self.assertEqual(build_parser().parse_args([]).language, "en")
        self.assertEqual(build_parser("it").parse_args(["--language", "it"]).language, "it")
        self.assertIn("Compute current coverage state", build_parser().format_help())
        self.assertIn("Calcola lo stato corrente", build_parser("it").format_help())

    def test_invalid_language_is_same_validation_failure(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["--language", "fr"])

        self.assertEqual(status, 2)
        self.assertIn("invalid choice", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
