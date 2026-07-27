#!/usr/bin/env python3

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from strategies.digit_coverage import (
    DigitCoverageWindow,
    analyze_digit_coverage,
)
from strategies.twin_digits import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")


def percentage(value: int, total: int) -> float:
    return value / total * 100 if total else 0.0


def format_digits(digits: Iterable[int]) -> str:
    values = tuple(digits)
    return " ".join(str(digit) for digit in values) if values else "—"


def print_global_summary(
    analysis: dict[int, tuple[DigitCoverageWindow, ...]],
) -> None:
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

    for window_size, windows in analysis.items():
        total = len(windows)
        missing_distribution = Counter(
            window.missing_count
            for window in windows
        )

        complete = missing_distribution[0]
        one_missing = missing_distribution[1]
        two_missing = missing_distribution[2]
        three_or_more = sum(
            count
            for missing_count, count
            in missing_distribution.items()
            if missing_count >= 3
        )

        missing_counts = [
            window.missing_count
            for window in windows
        ]

        average = statistics.mean(missing_counts)
        median = statistics.median(missing_counts)

        print(
            f"{window_size:<5}"
            f"{total:<9}"
            f"{complete:>4} ({percentage(complete, total):>6.2f}%)  "
            f"{one_missing:>4} ({percentage(one_missing, total):>6.2f}%)  "
            f"{two_missing:>4} ({percentage(two_missing, total):>6.2f}%)  "
            f"{three_or_more:>4} ({percentage(three_or_more, total):>6.2f}%)  "
            f"{average:>5.2f}  "
            f"{median:>7.2f}"
        )


def print_missing_digit_frequency(
    analysis: dict[int, tuple[DigitCoverageWindow, ...]],
) -> None:
    print("\n===== FREQUENZA DI ASSENZA PER CIFRA =====")
    print(
        "La percentuale indica in quante finestre la cifra "
        "risulta completamente assente."
    )

    for window_size, windows in analysis.items():
        total = len(windows)
        absence_counts = Counter(
            digit
            for window in windows
            for digit in window.missing_digits
        )

        ranking = sorted(
            range(10),
            key=lambda digit: (
                -absence_counts[digit],
                digit,
            ),
        )

        print(
            f"\nFinestra di {window_size} "
            f"{'estrazione' if window_size == 1 else 'estrazioni'}"
        )
        print()
        print("Cifra  Finestre assente  Percentuale")
        print("-----  ---------------  -----------")

        for digit in ranking:
            count = absence_counts[digit]

            print(
                f"{digit:<6}"
                f"{count:<17}"
                f"{percentage(count, total):>10.2f}%"
            )


def print_summary_by_wheel(
    analysis: dict[int, tuple[DigitCoverageWindow, ...]],
) -> None:
    print("\n===== COPERTURA PER RUOTA =====")

    for window_size, windows in analysis.items():
        grouped: dict[str, list[DigitCoverageWindow]] = defaultdict(list)

        for window in windows:
            grouped[window.wheel].append(window)

        wheel_order = {
            window.wheel: window.wheel_order
            for window in windows
        }

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

        for wheel in sorted(
            grouped,
            key=lambda name: wheel_order[name],
        ):
            wheel_windows = grouped[wheel]
            total = len(wheel_windows)

            complete = sum(
                window.missing_count == 0
                for window in wheel_windows
            )

            at_most_one_missing = sum(
                window.missing_count <= 1
                for window in wheel_windows
            )

            average_missing = statistics.mean(
                window.missing_count
                for window in wheel_windows
            )

            print(
                f"{wheel:<12}"
                f"{total:<9}"
                f"{percentage(complete, total):>7.2f}%  "
                f"{percentage(at_most_one_missing, total):>12.2f}%  "
                f"{average_missing:>14.2f}"
            )


def print_latest_windows(
    analysis: dict[int, tuple[DigitCoverageWindow, ...]],
) -> None:
    print("\n===== ULTIMA FINESTRA DISPONIBILE PER RUOTA =====")

    for window_size, windows in analysis.items():
        latest_by_wheel: dict[str, DigitCoverageWindow] = {}

        for window in windows:
            current = latest_by_wheel.get(window.wheel)

            window_key = (
                window.end_date,
                window.draw_numbers[-1],
            )

            current_key = (
                current.end_date,
                current.draw_numbers[-1],
            ) if current is not None else ("", -1)

            if current is None or window_key > current_key:
                latest_by_wheel[window.wheel] = window

        wheel_order = {
            window.wheel: window.wheel_order
            for window in windows
        }

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

        for wheel in sorted(
            latest_by_wheel,
            key=lambda name: wheel_order[name],
        ):
            window = latest_by_wheel[wheel]
            draws = ",".join(
                str(draw_number)
                for draw_number in window.draw_numbers
            )

            print(
                f"{wheel:<12}"
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


def main() -> int:
    args = build_parser().parse_args()

    if args.max_window_size <= 0:
        print(
            "ERRORE: --max-window-size deve essere positivo.",
            file=sys.stderr,
        )
        return 1

    try:
        with LottoRepository(args.database) as repository:
            analysis = analyze_digit_coverage(
                repository,
                max_window_size=args.max_window_size,
            )

        print_global_summary(analysis)
        print_missing_digit_frequency(analysis)
        print_summary_by_wheel(analysis)
        print_latest_windows(analysis)

    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
