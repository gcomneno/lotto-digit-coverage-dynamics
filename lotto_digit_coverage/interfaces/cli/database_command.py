"""Direct CLI command adapter for the database viewer."""

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


def _extract_occurrence_limit(
    arguments: Sequence[str],
) -> tuple[list[str], int | None]:
    cleaned: list[str] = []
    occurrence_limit: int | None = None
    index = 0

    while index < len(arguments):
        argument = arguments[index]
        if argument != "--occurrence-limit":
            cleaned.append(argument)
            index += 1
            continue

        if index + 1 >= len(arguments):
            raise legacy.CliError(
                "--occurrence-limit richiede un numero di estrazioni."
            )
        if occurrence_limit is not None:
            raise legacy.CliError(
                "--occurrence-limit può essere specificato una sola volta."
            )

        occurrence_limit = legacy._positive_integer(
            arguments[index + 1],
            "--occurrence-limit",
        )
        index += 2

    return cleaned, occurrence_limit


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else list(argv)

    try:
        parsed_arguments, occurrence_limit = _extract_occurrence_limit(arguments)
        options = legacy.parse_options(parsed_arguments)
    except legacy.CliError as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        if error.show_usage:
            print(file=sys.stderr)
            legacy.usage(sys.stderr)
        return 2

    if options is None:
        if "--help" in arguments or "-h" in arguments:
            print(
                "\nEstensione occurrence groups:\n"
                "  --occurrence-limit N  Limita il range globale a N concorsi "
                "consecutivi, incluse le righe di riferimento."
            )
        return 0

    if occurrence_limit is not None and options.occurrence_groups is None:
        print(
            "ERRORE: --occurrence-limit richiede --occurrence-groups.",
            file=sys.stderr,
        )
        return 2

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
            occurrence_limit=occurrence_limit,
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
