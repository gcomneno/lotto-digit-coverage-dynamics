#!/usr/bin/env python3

"""Quadro corrente con consensus descrittivo al posto di TUTTE."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import analyze_current_coverage as legacy
from strategies.coverage_consensus import render_digit_consensus


_ORIGINAL_PRINT_MARKOV_SUMMARY = legacy.print_markov_summary


def print_markov_summary_with_consensus(states) -> None:
    """Riusa la tabella Markov esistente eliminando la riga TUTTE."""

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
    print(render_digit_consensus(states))


def main() -> int:
    legacy.print_markov_summary = print_markov_summary_with_consensus
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
