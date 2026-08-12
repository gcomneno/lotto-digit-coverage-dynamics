#!/usr/bin/env python3

"""CLI current backed by the structured application report."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout

import analyze_current_coverage as legacy
from lotto_digit_coverage.application.current import build_current_coverage_report
from lotto_digit_coverage.interfaces.cli.current import render_current_report
from strategies.coverage_consensus import render_digit_consensus
from strategies.current_coverage_signal import (
    DEFAULT_HISTORICAL_SUMMARY,
    load_historical_coverage_classes,
)
from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import LottoRepository


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
    print(render_digit_consensus(states))


def main() -> int:
    args = legacy.build_parser().parse_args()

    try:
        with LottoRepository(args.database) as repository:
            all_draws_by_wheel = load_draws_by_wheel(repository)

        checkpoint_path = None
        checkpoint_payload = None

        if not args.without_checkpoint:
            checkpoint_path, checkpoint_payload = (
                legacy.checkpoint_for_current_archive(
                    explicit_path=args.checkpoint,
                    current_draws_by_wheel=all_draws_by_wheel,
                )
            )

        historical_classes = load_historical_coverage_classes(
            DEFAULT_HISTORICAL_SUMMARY
        )
        report = build_current_coverage_report(
            all_draws_by_wheel=all_draws_by_wheel,
            historical_classes=historical_classes,
            cutoff_date=args.to_date,
            cutoff_draw_number=args.to_draw_number,
            checkpoint_payload=checkpoint_payload,
        )

        render_current_report(
            report,
            database=args.database,
            summary_path=DEFAULT_HISTORICAL_SUMMARY,
            checkpoint_path=checkpoint_path,
            checkpoint_date=(
                None
                if checkpoint_payload is None
                else str(checkpoint_payload["checkpoint_date"])
            ),
            cutoff_date=(
                None
                if args.to_date is None
                else args.to_date.isoformat()
            ),
            cutoff_draw_number=args.to_draw_number,
        )
    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
