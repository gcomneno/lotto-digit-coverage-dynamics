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
from lotto_digit_coverage.interfaces.cli.occurrence_localization import occurrence_text
from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    DEFAULT_PRESENTATION_CATALOG,
    SUPPORTED_LOCALES,
)


def _structured_draws(draws):
    return {
        key: {
            wheel: tuple(int(token) for token in numbers.split())
            for wheel, numbers in wheel_results.items()
        }
        for key, wheel_results in draws.items()
    }


def _extract_language(arguments: Sequence[str]) -> tuple[list[str], str]:
    cleaned: list[str] = []
    locale = CANONICAL_LOCALE
    language_seen = False
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument != "--language":
            cleaned.append(argument)
            index += 1
            continue
        if index + 1 >= len(arguments):
            raise legacy.CliError(occurrence_text("language_missing", locale))
        if language_seen:
            raise legacy.CliError(occurrence_text("language_duplicate", locale))
        requested_locale = arguments[index + 1]
        if requested_locale not in SUPPORTED_LOCALES:
            raise legacy.CliError(occurrence_text("language_invalid", locale))
        locale = requested_locale
        language_seen = True
        index += 2
    return cleaned, locale


def _extract_occurrence_limit(
    arguments: Sequence[str],
    *,
    locale: str,
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
            raise legacy.CliError(occurrence_text("occurrence_limit_missing", locale))
        if occurrence_limit is not None:
            raise legacy.CliError(occurrence_text("occurrence_limit_duplicate", locale))

        occurrence_limit = legacy._positive_integer(
            arguments[index + 1],
            "--occurrence-limit",
        )
        index += 2

    return cleaned, occurrence_limit


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else list(argv)

    if arguments and arguments[0] == "ask":
        from lotto_digit_coverage.interfaces.cli.natural_query_command import (
            main as natural_query_main,
        )

        return natural_query_main(arguments[1:])

    locale = CANONICAL_LOCALE
    try:
        language_cleaned, locale = _extract_language(arguments)
        parsed_arguments, occurrence_limit = _extract_occurrence_limit(
            language_cleaned,
            locale=locale,
        )
        options = legacy.parse_options(parsed_arguments)
    except legacy.CliError as error:
        prefix = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", locale).text
        print(f"{prefix}: {error}", file=sys.stderr)
        if error.show_usage:
            print(file=sys.stderr)
            legacy.usage(sys.stderr)
        return 2

    if options is None:
        if "--help" in arguments or "-h" in arguments:
            print(
                "\n" + occurrence_text("help_title", locale) + "\n"
                + occurrence_text("help_occurrence_limit", locale)
                + "\n  --language {en,it}  "
                + occurrence_text("language_help", locale)
            )
        return 0

    if occurrence_limit is not None and options.occurrence_groups is None:
        prefix = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", locale).text
        print(
            f"{prefix}: {occurrence_text('occurrence_limit_requires_groups', locale)}",
            file=sys.stderr,
        )
        return 2

    if options.occurrence_groups is None:
        try:
            output = legacy.render(options)
        except FileNotFoundError as error:
            prefix = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", locale).text
            print(f"{prefix}: {error}", file=sys.stderr)
            return 1
        except (sqlite3.Error, ValueError) as error:
            prefix = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", locale).text
            print(f"{prefix}: {error}", file=sys.stderr)
            return 1

        print(output)
        return 0

    if not options.database.is_file():
        prefix = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", locale).text
        print(
            f"{prefix}: {occurrence_text('database_missing', locale)}: {options.database}",
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
            locale=locale,
        )
    except (sqlite3.Error, ValueError) as error:
        prefix = DEFAULT_PRESENTATION_CATALOG.resolve("common.error_prefix", locale).text
        print(f"{prefix}: {error}", file=sys.stderr)
        return 1

    return 0
