#!/usr/bin/env python3

"""Probabilità di completamento dei cicli naturali di copertura 0–9."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from lotto_digit_coverage.application.historical_markov import (
    CompletionGroup,
    CoverageCompletionReport,
    age_bucket,
    bucket_order,
    build_coverage_completion_report,
    completed_cycle_lengths,
    summarize_completion,
)
from strategies.coverage_completion import CoverageCompletionObservation
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")


def summarize(
    observations: Sequence[CoverageCompletionObservation],
) -> tuple[int, int, float, float, float]:
    """Compatibility tuple for callers that predate the application report."""

    summary = summarize_completion(observations)
    return (
        summary.cases,
        summary.completions,
        summary.observed_probability,
        summary.theoretical_probability,
        summary.delta,
    )


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(str(digit) for digit in sorted(digits)) + "}"


def _format_group_key(key: object) -> str:
    if isinstance(key, frozenset):
        return format_digits(key)
    return str(key)


def print_group_table(
    title: str,
    groups: Sequence[CompletionGroup],
    *,
    key_label: str,
) -> None:
    print(f"\n===== {title} =====")
    print()
    print(
        f"{key_label:<12}"
        "Casi    Chiusure  Osservato  Teorico   Delta"
    )
    print(
        f"{'-' * 12}  "
        "------  --------  ---------  --------  --------"
    )

    for group in groups:
        summary = group.summary
        print(
            f"{_format_group_key(group.key):<14}"
            f"{summary.cases:<8}"
            f"{summary.completions:<10}"
            f"{summary.observed_probability:>8.2%}  "
            f"{summary.theoretical_probability:>7.2%}  "
            f"{summary.delta:>+7.2%}"
        )


def print_single_missing(report: CoverageCompletionReport) -> None:
    print("\n===== QUANDO MANCA UNA SOLA CIFRA =====")
    print()
    print(
        "Cifra  Casi    Chiusure  Osservato  "
        "Teorico   Delta"
    )
    print(
        "-----  ------  --------  ---------  "
        "--------  --------"
    )

    for group in report.single_missing:
        summary = group.summary
        print(
            f"{group.key:<7}"
            f"{summary.cases:<8}"
            f"{summary.completions:<10}"
            f"{summary.observed_probability:>8.2%}  "
            f"{summary.theoretical_probability:>7.2%}  "
            f"{summary.delta:>+7.2%}"
        )


def print_exact_states(report: CoverageCompletionReport) -> None:
    print(
        f"\n===== STATI ESATTI CON ALMENO "
        f"{report.minimum_state_cases} CASI ====="
    )
    print()
    print(
        "Mancanti      Casi    Chiusure  Osservato  "
        "Teorico   Delta"
    )
    print(
        "------------  ------  --------  ---------  "
        "--------  --------"
    )

    for group in report.exact_states:
        summary = group.summary
        print(
            f"{_format_group_key(group.key):<14}"
            f"{summary.cases:<8}"
            f"{summary.completions:<10}"
            f"{summary.observed_probability:>8.2%}  "
            f"{summary.theoretical_probability:>7.2%}  "
            f"{summary.delta:>+7.2%}"
        )


def print_residual_duration(report: CoverageCompletionReport) -> None:
    print("\n===== DISTANZA RESIDUA DAL COMPLETAMENTO =====")
    print()
    print(
        "Sono inclusi soltanto gli stati appartenenti a cicli "
        "completati entro l'archivio."
    )
    print(
        "Stati esclusi perché censurati a destra: "
        f"{report.right_censored_states}"
    )
    print()
    print("Mancanti  Stati   Media residua  Mediana  Min–Max")
    print("--------  ------  -------------  -------  -------")

    for row in report.residual_rows:
        print(
            f"{row.missing_count:<10}"
            f"{row.states:<8}"
            f"{row.mean_remaining:>11.2f}  "
            f"{row.median_remaining:>7.1f}  "
            f"{row.minimum_remaining}–{row.maximum_remaining}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analizza probabilità e distanza residua "
            "dei cicli naturali di copertura."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    parser.add_argument(
        "--minimum-state-cases",
        type=int,
        default=10,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        with LottoRepository(args.database) as repository:
            report = build_coverage_completion_report(
                repository,
                minimum_state_cases=args.minimum_state_cases,
            )

        print("===== MATURITÀ DEI CICLI DI COPERTURA =====")
        print(f"Database: {args.database}")
        print(
            "Ciclo naturale: ripartenza dopo ogni copertura completa 0–9."
        )
        print(
            "Il primo ciclo di ogni ruota è escluso perché iniziato "
            "prima dell'archivio."
        )
        print(f"Stati incompleti osservati: {len(report.observations)}")

        print_group_table(
            "PROBABILITÀ PER NUMERO DI CIFRE MANCANTI",
            report.by_missing_count,
            key_label="Mancanti",
        )
        print_group_table(
            "PROBABILITÀ PER ETÀ DEL CICLO",
            report.by_cycle_age,
            key_label="Estrazioni",
        )
        print_single_missing(report)
        print_exact_states(report)
        print_residual_duration(report)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
