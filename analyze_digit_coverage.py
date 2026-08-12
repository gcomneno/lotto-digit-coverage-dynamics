#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from lotto_digit_coverage.application.historical_signals import (
    DigitCoverageReport,
    build_digit_coverage_report,
)
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-current.sqlite3")


def percentage(value: int, total: int) -> float:
    return value / total * 100 if total else 0.0


def format_digits(digits: Iterable[int]) -> str:
    values = tuple(digits)
    return " ".join(str(digit) for digit in values) if values else "—"


def print_global_summary(report: DigitCoverageReport) -> None:
    print("===== SINTESI GENERALE DELLA COPERTURA 0–9 =====")
    print()
    print(
        "Amp.  Finestre  Complete       1 mancante     "
        "2 mancanti    3+ mancanti   Media  Mediana"
    )
    print(
        "----  -------  -------------  -------------  "
        "-------------  -------------  -----  -------"
    )

    for row in report.global_summary:
        print(
            f"{row.window_size:<5}"
            f"{row.windows:<9}"
            f"{row.complete:>4} ({percentage(row.complete, row.windows):>6.2f}%)  "
            f"{row.one_missing:>4} ({percentage(row.one_missing, row.windows):>6.2f}%)  "
            f"{row.two_missing:>4} ({percentage(row.two_missing, row.windows):>6.2f}%)  "
            f"{row.three_or_more_missing:>4} "
            f"({percentage(row.three_or_more_missing, row.windows):>6.2f}%)  "
            f"{row.average_missing:>5.2f}  "
            f"{row.median_missing:>7.2f}"
        )


def print_missing_digit_frequency(report: DigitCoverageReport) -> None:
    print("\n===== FREQUENZA DI ASSENZA PER CIFRA =====")
    print(
        "La percentuale indica in quante finestre la cifra "
        "risulta completamente assente."
    )

    for window_size, _windows in report.windows_by_size:
        print(
            f"\nFinestra di {window_size} "
            f"{'estrazione' if window_size == 1 else 'estrazioni'}"
        )
        print()
        print("Cifra  Finestre assente  Percentuale")
        print("-----  ---------------  -----------")

        for row in report.digit_absence:
            if row.window_size != window_size:
                continue
            print(
                f"{row.digit:<6}"
                f"{row.absent_windows:<17}"
                f"{percentage(row.absent_windows, row.total_windows):>10.2f}%"
            )


def print_summary_by_wheel(report: DigitCoverageReport) -> None:
    print("\n===== COPERTURA PER RUOTA =====")

    for window_size, _windows in report.windows_by_size:
        print(
            f"\nFinestra di {window_size} "
            f"{'estrazione' if window_size == 1 else 'estrazioni'}"
        )
        print()
        print(
            "Ruota       Finestre  Complete  Max 1 mancante  "
            "Media mancanti"
        )
        print(
            "-----------  -------  --------  --------------  "
            "--------------"
        )

        for row in report.wheel_summary:
            if row.window_size != window_size:
                continue
            print(
                f"{row.wheel:<12}"
                f"{row.windows:<9}"
                f"{percentage(row.complete_windows, row.windows):>7.2f}%  "
                f"{percentage(row.at_most_one_missing_windows, row.windows):>12.2f}%  "
                f"{row.average_missing:>14.2f}"
            )


def print_latest_windows(report: DigitCoverageReport) -> None:
    print("\n===== ULTIMA FINESTRA DISPONIBILE PER RUOTA =====")

    for window_size, _windows in report.windows_by_size:
        print(
            f"\nFinestra di {window_size} "
            f"{'estrazione' if window_size == 1 else 'estrazioni'}"
        )
        print()
        print(
            "Ruota       Concorsi          Presenti              "
            "Assenti  N."
        )
        print(
            "-----------  ----------------  --------------------  "
            "-------  --"
        )

        for row in report.latest_windows:
            if row.window_size != window_size:
                continue
            window = row.window
            draws = ",".join(str(number) for number in window.draw_numbers)
            print(
                f"{row.wheel:<12}"
                f"{draws:<18}"
                f"{format_digits(window.present_digits):<22}"
                f"{format_digits(window.missing_digits):<9}"
                f"{window.missing_count}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analizza la copertura delle cifre 0–9 "
            "nelle estrazioni del Lotto."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    parser.add_argument(
        "--max-window-size",
        type=int,
        default=3,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.max_window_size <= 0:
        print(
            "ERRORE: --max-window-size deve essere positivo.",
            file=sys.stderr,
        )
        return 1

    try:
        with LottoRepository(args.database) as repository:
            report = build_digit_coverage_report(
                repository,
                max_window_size=args.max_window_size,
            )

        print_global_summary(report)
        print_missing_digit_frequency(report)
        print_summary_by_wheel(report)
        print_latest_windows(report)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
