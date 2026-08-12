#!/usr/bin/env python3

"""Confronto tra attesa residua Markov e durata osservata."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from lotto_digit_coverage.application.historical_markov import (
    MarkovResidualReport,
    ResidualGroup,
    build_markov_residual_report,
    expectation_band,
    expectation_band_sort_key,
    summarize_residual,
)
from strategies.coverage_markov_residuals import MarkovResidualObservation
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def band_sort_key(label: str) -> int:
    return expectation_band_sort_key(label)


def summarize(
    observations: Sequence[MarkovResidualObservation],
) -> tuple[int, float, float, float, float, float]:
    """Compatibility tuple for callers that predate the application report."""

    summary = summarize_residual(observations)
    return (
        summary.states,
        summary.actual_mean,
        summary.predicted_mean,
        summary.bias,
        summary.mean_absolute_error,
        summary.root_mean_square_error,
    )


def _format_group_key(key: object) -> str:
    if isinstance(key, frozenset):
        return format_digits(key)
    return str(key)


def print_group_table(
    title: str,
    groups: Sequence[ResidualGroup],
) -> None:
    print(f"\n===== {title} =====")
    print()
    print(
        "Gruppo          Stati   Reale     Prevista  "
        "Bias      MAE      RMSE"
    )
    print(
        "--------------  ------  --------  --------  "
        "--------  -------  -------"
    )

    for group in groups:
        summary = group.summary
        print(
            f"{_format_group_key(group.key):<16}"
            f"{summary.states:<8}"
            f"{summary.actual_mean:>6.3f}  "
            f"{summary.predicted_mean:>7.3f}  "
            f"{summary.bias:>+7.3f}  "
            f"{summary.mean_absolute_error:>7.3f}  "
            f"{summary.root_mean_square_error:>7.3f}"
        )


def print_exact_states(report: MarkovResidualReport) -> None:
    print(
        f"\n===== STATI ESATTI CON ALMENO "
        f"{report.minimum_state_cases} CASI ====="
    )
    print()
    print(
        "Mancanti        Stati   Reale     Prevista  "
        "Bias      MAE"
    )
    print(
        "--------------  ------  --------  --------  "
        "--------  -------"
    )

    for group in report.exact_states:
        summary = group.summary
        print(
            f"{_format_group_key(group.key):<16}"
            f"{summary.states:<8}"
            f"{summary.actual_mean:>6.3f}  "
            f"{summary.predicted_mean:>7.3f}  "
            f"{summary.bias:>+7.3f}  "
            f"{summary.mean_absolute_error:>7.3f}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta l'attesa residua teorica Markov "
            "con la durata residua osservata."
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
        default=20,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        with LottoRepository(args.database) as repository:
            report = build_markov_residual_report(
                repository,
                minimum_state_cases=args.minimum_state_cases,
            )

        print("===== VALIDAZIONE ATTESA RESIDUA MARKOV =====")
        print(f"Database: {args.database}")
        print(
            "Sono inclusi solo stati con completamento successivo "
            "osservabile nell'archivio."
        )
        print(
            "Le osservazioni dello stesso ciclo sono dipendenti: "
            "il confronto è descrittivo."
        )
        print(f"Stati osservati: {len(report.observations)}")

        overall = report.overall
        print("\n===== RISULTATO COMPLESSIVO =====")
        print(f"Stati:                  {overall.states}")
        print(f"Durata residua reale:   {overall.actual_mean:.3f}")
        print(f"Durata prevista Markov: {overall.predicted_mean:.3f}")
        print(f"Bias reale - prevista:  {overall.bias:+.3f}")
        print(
            "Errore assoluto medio:  "
            f"{overall.mean_absolute_error:.3f}"
        )
        print(f"RMSE:                    {overall.root_mean_square_error:.3f}")

        print_group_table(
            "PER NUMERO DI CIFRE MANCANTI",
            report.by_missing_count,
        )
        print_group_table(
            "PER FASCIA DI ATTESA PREVISTA",
            report.by_expectation_band,
        )
        print_exact_states(report)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
