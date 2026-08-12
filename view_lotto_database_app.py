#!/usr/bin/env python3

"""Database viewer adapter with structured occurrence-group calculation."""

from __future__ import annotations

import sqlite3
import sys
from collections.abc import Sequence

import view_lotto_database as legacy
from lotto_digit_coverage.application.occurrence_groups import (
    build_occurrence_group_report,
)
from lotto_digit_coverage.interfaces.cli.occurrence_groups import (
    render_occurrence_group_report,
)


def _structured_draws(draws):
    return {
        key: {
            wheel: tuple(int(token) for token in numbers.split())
            for wheel, numbers in wheel_results.items()
        }
        for key, wheel_results in draws.items()
    }


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else list(argv)

    try:
        options = legacy.parse_options(arguments)
    except legacy.CliError as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        if error.show_usage:
            print(file=sys.stderr)
            legacy.usage(sys.stderr)
        return 2

    if options is None:
        return 0

    # Non-grouped views remain on the legacy renderer until their own vertical
    # is migrated. The grouped path below is the #13 application boundary.
    if options.occurrence_groups is None:
        try:
            output = legacy.render(options)
        except FileNotFoundError as error:
            print(f"ERRORE: {error}", file=sys.stderr)
            return 1
        except (sqlite3.Error, ValueError) as error:
            print(f"ERRORE: {error}", file=sys.stderr)
            return 1

        print(output)
        return 0

    if not options.database.is_file():
        print(
            f"ERRORE: database assente: {options.database}",
            file=sys.stderr,
        )
        return 1

    try:
        count, first_draw, last_draw, raw_draws = legacy.load_database(
            options.database
        )
        report = build_occurrence_group_report(
            draws=_structured_draws(raw_draws),
            expected_wheels=legacy.EXPECTED_WHEELS,
            group_size=options.occurrence_groups,
            requested_draw_number=(
                int(options.latest_occurrences_draw)
                if options.latest_occurrences_draw
                else None
            ),
        )
        render_occurrence_group_report(
            report,
            database=options.database,
            draw_count=count,
            first_draw=first_draw,
            last_draw=last_draw,
            expected_wheels=legacy.EXPECTED_WHEELS,
        )
    except (sqlite3.Error, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
