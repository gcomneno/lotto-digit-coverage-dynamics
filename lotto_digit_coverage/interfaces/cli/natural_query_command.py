"""CLI adapter for semantic read-only Lotto queries."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from giadaware_ai import AIError

from lotto_digit_coverage.infrastructure.giadaware_ai_read_query import (
    build_default_giadaware_backend,
)
from lotto_digit_coverage.infrastructure.lotto_read_query_pipeline import (
    LottoReadQueryOutcome,
    LottoReadQueryPipeline,
)
from lotto_digit_coverage.interfaces.localization import (
    DEFAULT_PRESENTATION_CATALOG,
    SUPPORTED_LOCALES,
)


DEFAULT_DATABASE = Path("data/lotto-current.sqlite3")
DB_ASK_DEFAULT_LOCALE = "it"


def _text(key: str, locale: str) -> str:
    return DEFAULT_PRESENTATION_CATALOG.resolve(
        key,
        locale,
    ).text


def _requested_locale(
    argv: Sequence[str] | None,
) -> str:
    arguments = list(
        sys.argv[1:] if argv is None else argv
    )

    bootstrap = argparse.ArgumentParser(
        add_help=False
    )
    bootstrap.add_argument(
        "--language",
        choices=SUPPORTED_LOCALES,
        default=DB_ASK_DEFAULT_LOCALE,
    )

    namespace, _ = bootstrap.parse_known_args(
        arguments
    )
    return namespace.language


def build_parser(
    locale: str = DB_ASK_DEFAULT_LOCALE,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lotto.py db ask",
        description=_text(
            "cli.ask.description",
            locale,
        ),
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=_text(
            "cli.ask.database_help",
            locale,
        ),
    )

    parser.add_argument(
        "--language",
        choices=SUPPORTED_LOCALES,
        default=DB_ASK_DEFAULT_LOCALE,
        help=_text(
            "cli.ask.language_help",
            locale,
        ),
    )

    parser.add_argument(
        "request",
        nargs="+",
        help=_text(
            "cli.ask.request_help",
            locale,
        ),
    )

    return parser


def _render_scalar(value: object) -> str:
    if value is None:
        return "NULL"
    return str(value)


def render_outcome(
    outcome: LottoReadQueryOutcome,
    *,
    locale: str,
) -> str:
    lines = [
        (
            f"{_text('cli.ask.status_label', locale)}: "
            f"{outcome.status}"
        )
    ]

    if not outcome.accepted:
        lines.append(
            f"{_text('cli.ask.reason_label', locale)}: "
            f"{outcome.reason or '-'}"
        )
        return "\n".join(lines)

    if (
        outcome.validated_query is None
        or outcome.result is None
    ):
        raise ValueError(
            "accepted outcome is missing authorized result data"
        )

    lines.extend(
        [
            (
                f"{_text('cli.ask.interpretation_label', locale)}: "
                f"{outcome.normalized_interpretation}"
            ),
            (
                f"{_text('cli.ask.query_label', locale)}: "
                f"{outcome.validated_query}"
            ),
            (
                f"{_text('cli.ask.database_label', locale)}: "
                f"{outcome.result.database}"
            ),
            "",
            _text(
                "cli.ask.results_label",
                locale,
            ),
        ]
    )

    if not outcome.result.rows:
        lines.append(
            _text(
                "cli.ask.no_rows",
                locale,
            )
        )
        return "\n".join(lines)

    lines.append(
        " | ".join(outcome.result.columns)
    )
    lines.append(
        "-+-".join(
            "-" * max(3, len(column))
            for column in outcome.result.columns
        )
    )

    for row in outcome.result.rows:
        lines.append(
            " | ".join(
                _render_scalar(value)
                for value in row
            )
        )

    return "\n".join(lines)


def main(
    argv: Sequence[str] | None = None,
    *,
    backend=None,
    current_date: date | None = None,
) -> int:
    locale = _requested_locale(argv)
    args = build_parser(locale).parse_args(argv)
    request = " ".join(args.request)

    try:
        resolved_backend = (
            backend
            or build_default_giadaware_backend()
        )

        pipeline = LottoReadQueryPipeline(
            resolved_backend,
            database=args.database,
            current_date=(
                current_date
                if current_date is not None
                else date.today()
            ),
        )

        outcome = pipeline.execute(
            request,
            language=args.language,
        )

        rendered = render_outcome(
            outcome,
            locale=args.language,
        )

        if outcome.accepted:
            print(rendered)
            return 0

        print(rendered, file=sys.stderr)
        return 2

    except (
        AIError,
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as error:
        prefix = _text(
            "common.error_prefix",
            args.language,
        )
        print(
            f"{prefix}: {error}",
            file=sys.stderr,
        )
        return 1
