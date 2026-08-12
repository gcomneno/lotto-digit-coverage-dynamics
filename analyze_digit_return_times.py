#!/usr/bin/env python3

"""Analisi dei tempi di ritorno delle singole cifre."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from lotto_digit_coverage.application.historical_signals import (
    DigitReturnReport,
    build_digit_return_report,
    streak_bucket as _streak_bucket,
    streak_bucket_sort_key,
    summarize_return,
)
from strategies.digit_return_times import DigitReturnObservation
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")
MAX_EXPLICIT_STREAK = 8


def streak_bucket(absence_streak: int) -> str:
    return _streak_bucket(
        absence_streak,
        maximum_explicit=MAX_EXPLICIT_STREAK,
    )


def bucket_sort_key(bucket: str) -> int:
    return streak_bucket_sort_key(bucket)


def summarize(
    observations: Sequence[DigitReturnObservation],
) -> tuple[int, int, float, float, float]:
    summary = summarize_return(observations)
    return (
        summary.cases,
        summary.hits,
        summary.observed_rate,
        summary.expected_rate,
        summary.delta,
    )


def print_hazard_tables(report: DigitReturnReport) -> None:
    labels = {
        "any": "QUALUNQUE POSIZIONE",
        "tens": "SOLO DECINE",
        "units": "SOLO UNITÀ",
    }

    for table in report.hazard_tables:
        print(f"\n===== {labels[table.position]} =====")
        print()
        print(
            "Assenze  Casi    Hit     Osservato  "
            "Atteso    Delta"
        )
        print(
            "-------  ------  ------  ---------  "
            "--------  --------"
        )

        for group in table.groups:
            summary = group.summary
            print(
                f"{group.key:<9}"
                f"{summary.cases:<8}"
                f"{summary.hits:<8}"
                f"{summary.observed_rate:>8.2%}  "
                f"{summary.expected_rate:>7.2%}  "
                f"{summary.delta:>+7.2%}"
            )


def print_any_position_by_digit(report: DigitReturnReport) -> None:
    print("\n===== QUALUNQUE POSIZIONE: RISULTATI PER CIFRA =====")
    print()
    print(
        "Cifra  Casi    Hit     Osservato  "
        "Baseline   Delta   Max assenza"
    )
    print(
        "-----  ------  ------  ---------  "
        "---------  --------  -----------"
    )

    for group in report.any_position_by_digit:
        summary = group.summary
        print(
            f"{group.key:<7}"
            f"{summary.cases:<8}"
            f"{summary.hits:<8}"
            f"{summary.observed_rate:>8.2%}  "
            f"{summary.expected_rate:>8.2%}  "
            f"{summary.delta:>+7.2%}  "
            f"{group.maximum_absence:>11}"
        )


def print_long_absences(report: DigitReturnReport) -> None:
    print("\n===== QUALUNQUE POSIZIONE: ASSENZE DA 5+ =====")
    print()
    print("Cifra  Casi  Hit  Osservato  Baseline   Delta")
    print("-----  ----  ---  ---------  ---------  --------")

    for group in report.long_absences_by_digit:
        summary = group.summary
        print(
            f"{group.key:<7}"
            f"{summary.cases:<6}"
            f"{summary.hits:<5}"
            f"{summary.observed_rate:>8.2%}  "
            f"{summary.expected_rate:>8.2%}  "
            f"{summary.delta:>+7.2%}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analizza la probabilità empirica di ricomparsa "
            "delle cifre dopo assenze consecutive."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        with LottoRepository(args.database) as repository:
            report = build_digit_return_report(
                repository,
                maximum_explicit_streak=MAX_EXPLICIT_STREAK,
            )

        print("===== TEMPI DI RITORNO DELLE CIFRE =====")
        print(f"Database: {args.database}")
        print(
            "Domanda: dopo k estrazioni consecutive di assenza, "
            "la cifra compare nella successiva?"
        )
        print(
            "Nota: le osservazioni successive della stessa sequenza "
            "non sono indipendenti; il rapporto è descrittivo."
        )

        print_hazard_tables(report)
        print_any_position_by_digit(report)
        print_long_absences(report)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
