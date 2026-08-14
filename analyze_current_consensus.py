#!/usr/bin/env python3

"""Compatibility entry point for the direct current CLI adapter."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import analyze_current_coverage as legacy
from lotto_digit_coverage.interfaces.cli.consensus import render_digit_consensus
from lotto_digit_coverage.interfaces.cli.current_command import main
from strategies.coverage_consensus import build_digit_consensus


# Compatibility surface for callers/tests that still import the PR #7 wrapper
# helper directly. The canonical current command no longer depends on this
# text-rewriting path.
_ORIGINAL_PRINT_MARKOV_SUMMARY = legacy.print_markov_summary


def print_markov_summary_with_consensus(states) -> None:
    buffer = io.StringIO()

    with redirect_stdout(buffer):
        _ORIGINAL_PRINT_MARKOV_SUMMARY(states)

    retained = [
        line
        for line in buffer.getvalue().splitlines()
        if not line.startswith("*    TUTTE")
        and not line.startswith("* TUTTE:")
    ]

    while retained and not retained[-1].strip():
        retained.pop()

    print("\n".join(retained))
    print()
    print(render_digit_consensus(build_digit_consensus(states)))


if __name__ == "__main__":
    raise SystemExit(main())
