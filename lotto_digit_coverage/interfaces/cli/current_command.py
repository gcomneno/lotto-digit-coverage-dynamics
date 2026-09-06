"""Direct CLI command adapter for current coverage status."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import analyze_current_coverage as legacy
from lotto_digit_coverage.application.current import build_current_coverage_report
from lotto_digit_coverage.interfaces.cli.current import render_current_report
from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    DEFAULT_PRESENTATION_CATALOG,
    SUPPORTED_LOCALES,
)
from strategies.current_coverage_signal import (
    DEFAULT_HISTORICAL_SUMMARY,
    load_historical_coverage_classes,
)
from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import LottoRepository


def _text(key: str, locale: str) -> str:
    return DEFAULT_PRESENTATION_CATALOG.resolve(key, locale).text


def _requested_locale(arguments: Sequence[str]) -> str:
    bootstrap = argparse.ArgumentParser(add_help=False)
    bootstrap.add_argument(
        "--language",
        default=CANONICAL_LOCALE,
    )
    namespace, _ = bootstrap.parse_known_args(arguments)
    return namespace.language


def build_parser(locale: str = CANONICAL_LOCALE) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=_text("cli.current.description", locale))
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help=_text("cli.current.checkpoint_help", locale),
    )
    parser.add_argument(
        "--without-checkpoint",
        action="store_true",
        help=_text("cli.current.without_checkpoint_help", locale),
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=legacy.DEFAULT_DATABASE,
        help=_text("cli.current.database_help", locale),
    )
    parser.add_argument(
        "--language",
        choices=SUPPORTED_LOCALES,
        default=CANONICAL_LOCALE,
        help=_text("cli.current.language_help", locale),
    )
    cutoff_group = parser.add_mutually_exclusive_group()
    cutoff_group.add_argument(
        "--to",
        dest="to_date",
        type=legacy.parse_iso_date,
        metavar="YYYY-MM-DD",
        help=_text("cli.current.to_help", locale),
    )
    cutoff_group.add_argument(
        "--to_num",
        "--to-num",
        dest="to_draw_number",
        type=legacy.parse_draw_number,
        metavar="N",
        help=_text("cli.current.to_num_help", locale),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    locale = _requested_locale(arguments)

    try:
        args = build_parser(locale).parse_args(arguments)
    except SystemExit as error:
        return int(error.code or 0)

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
            locale=args.language,
        )
    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        print(
            f"{_text('common.error_prefix', args.language)}: {error}",
            file=sys.stderr,
        )
        return 1

    return 0
