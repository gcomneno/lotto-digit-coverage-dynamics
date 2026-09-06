"""CLI adapter for safe natural-language Lotto exploration."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path

from lotto_digit_coverage.application.natural_query import (
    DrawHistoryIntent,
    DrawHistoryRow,
    NaturalQueryError,
    execute_draw_history,
)
from lotto_digit_coverage.infrastructure.giadaware_ai_query import (
    LottoNaturalQueryCapability,
    build_default_giadaware_backend,
)
from lotto_digit_coverage.infrastructure.sqlite_draw_history import (
    SqliteDrawHistoryRepository,
)
from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    DEFAULT_PRESENTATION_CATALOG,
    SUPPORTED_LOCALES,
)


DEFAULT_DATABASE = Path("data/lotto-current.sqlite3")
HIGHLIGHT = "\033[1;30;46m"
RESET = "\033[0m"


def _text(key: str, locale: str) -> str:
    return DEFAULT_PRESENTATION_CATALOG.resolve(key, locale).text


def _requested_locale(argv: Sequence[str] | None) -> str:
    arguments = list(sys.argv[1:] if argv is None else argv)
    bootstrap = argparse.ArgumentParser(add_help=False)
    bootstrap.add_argument(
        "--language",
        choices=SUPPORTED_LOCALES,
        default=CANONICAL_LOCALE,
    )
    namespace, _ = bootstrap.parse_known_args(arguments)
    return namespace.language


def build_parser(locale: str = CANONICAL_LOCALE) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lotto.py db ask",
        description=_text("cli.ask.description", locale),
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=_text("cli.ask.database_help", locale),
    )
    parser.add_argument(
        "--language",
        choices=SUPPORTED_LOCALES,
        default=CANONICAL_LOCALE,
        help=_text("cli.ask.language_help", locale),
    )
    parser.add_argument(
        "request",
        nargs="+",
        help=_text("cli.ask.request_help", locale),
    )
    return parser


def render_draw_history(
    intent: DrawHistoryIntent,
    rows: Sequence[DrawHistoryRow],
    *,
    database: Path = DEFAULT_DATABASE,
    locale: str = CANONICAL_LOCALE,
) -> str:
    draw_header = _text("cli.ask.draw_header", locale)
    date_header = _text("cli.ask.date_header", locale)
    numbers_header = _text("cli.ask.numbers_header", locale)
    lines = [
        f"{_text('cli.ask.database_label', locale)}: {database}",
        f"{_text('cli.ask.wheel_label', locale)}: {intent.wheel}",
        f"{_text('cli.ask.order_label', locale)}: {intent.order}",
        "",
        f"{draw_header:<4}  {date_header:<10}  {numbers_header}",
        "----  ----------  --------------",
    ]
    for row in rows:
        rendered = " ".join(
            _render_number(value, intent)
            for value in row.numbers
        )
        lines.append(f"{row.draw_number:>4}  {row.draw_date}  {rendered}")
    return "\n".join(lines)


def _render_number(value: int, intent: DrawHistoryIntent) -> str:
    token = f"{value:02d}"
    if not intent.highlight:
        return token
    if value in intent.numbers:
        return f"{HIGHLIGHT}{token}{RESET}"
    if not intent.digits:
        return token
    digits = set(intent.digits)
    return "".join(
        f"{HIGHLIGHT}{character}{RESET}" if int(character) in digits else character
        for character in token
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    backend=None,
) -> int:
    locale = _requested_locale(argv)
    args = build_parser(locale).parse_args(argv)
    request = " ".join(args.request)

    try:
        resolved_backend = backend or build_default_giadaware_backend()
        intent = LottoNaturalQueryCapability(resolved_backend).execute(request)
        repository = SqliteDrawHistoryRepository(args.database)
        rows = execute_draw_history(intent, repository)
        print(
            render_draw_history(
                intent,
                rows,
                database=args.database,
                locale=args.language,
            )
        )
    except (FileNotFoundError, NaturalQueryError, RuntimeError, sqlite3.Error, ValueError) as error:
        prefix = _text("common.error_prefix", args.language)
        print(f"{prefix}: {error}", file=sys.stderr)
        return 1

    return 0
