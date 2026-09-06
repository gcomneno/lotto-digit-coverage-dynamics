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


DEFAULT_DATABASE = Path("data/lotto-current.sqlite3")
HIGHLIGHT = "\033[1;30;46m"
RESET = "\033[0m"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lotto.py db ask",
        description=(
            "Interpreta una richiesta naturale tramite GiadaWare AI e la "
            "esegue come query Lotto deterministica e read-only."
        ),
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Database SQLite da consultare.",
    )
    parser.add_argument(
        "request",
        nargs="+",
        help="Richiesta in linguaggio naturale.",
    )
    return parser


def render_draw_history(
    intent: DrawHistoryIntent,
    rows: Sequence[DrawHistoryRow],
) -> str:
    lines = [
        f"Database: {DEFAULT_DATABASE}",
        f"Ruota: {intent.wheel}",
        f"Ordine: {intent.order}",
        "",
        "Estr  Data        Numeri",
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
    args = build_parser().parse_args(argv)
    request = " ".join(args.request)

    try:
        resolved_backend = backend or build_default_giadaware_backend()
        intent = LottoNaturalQueryCapability(resolved_backend).execute(request)
        repository = SqliteDrawHistoryRepository(args.database)
        rows = execute_draw_history(intent, repository)
        output = render_draw_history(intent, rows)
        if args.database != DEFAULT_DATABASE:
            output = output.replace(
                f"Database: {DEFAULT_DATABASE}",
                f"Database: {args.database}",
                1,
            )
        print(output)
    except (FileNotFoundError, NaturalQueryError, RuntimeError, sqlite3.Error, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0
