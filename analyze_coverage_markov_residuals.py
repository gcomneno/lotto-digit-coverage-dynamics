#!/usr/bin/env python3

"""Confronto tra attesa residua Markov e durata osservata."""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Hashable, Sequence

from strategies.coverage_markov_residuals import (
    MarkovResidualObservation,
    collect_residual_observations,
)
from strategies.twin_digits import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def expectation_band(value: float) -> str:
    if value < 1.75:
        return "<1.75"
    if value < 2.25:
        return "1.75–2.25"
    if value < 2.75:
        return "2.25–2.75"
    if value < 3.25:
        return "2.75–3.25"

    return "3.25+"


def band_sort_key(label: str) -> int:
    order = {
        "<1.75": 0,
        "1.75–2.25": 1,
        "2.25–2.75": 2,
        "2.75–3.25": 3,
        "3.25+": 4,
    }

    return order[label]


def summarize(
    observations: Sequence[MarkovResidualObservation],
) -> tuple[int, float, float, float, float, float]:
    total = len(observations)

    if not observations:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0

    actual_mean = statistics.mean(
        observation.actual_remaining
        for observation in observations
    )

    predicted_mean = statistics.mean(
        observation.predicted_remaining
        for observation in observations
    )

    errors = tuple(
        observation.actual_remaining
        - observation.predicted_remaining
        for observation in observations
    )

    bias = statistics.mean(errors)
    mae = statistics.mean(abs(error) for error in errors)
    rmse = math.sqrt(
        statistics.mean(error * error for error in errors)
    )

    return (
        total,
        actual_mean,
        predicted_mean,
        bias,
        mae,
        rmse,
    )


def print_group_table(
    title: str,
    groups: dict[
        Hashable,
        list[MarkovResidualObservation],
    ],
    *,
    key_formatter=str,
    sort_key=None,
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

    keys = sorted(
        groups,
        key=sort_key,
    )

    for key in keys:
        (
            total,
            actual,
            predicted,
            bias,
            mae,
            rmse,
        ) = summarize(groups[key])

        print(
            f"{key_formatter(key):<16}"
            f"{total:<8}"
            f"{actual:>6.3f}  "
            f"{predicted:>7.3f}  "
            f"{bias:>+7.3f}  "
            f"{mae:>7.3f}  "
            f"{rmse:>7.3f}"
        )


def print_exact_states(
    observations: Sequence[MarkovResidualObservation],
    minimum_cases: int,
) -> None:
    groups: dict[
        frozenset[int],
        list[MarkovResidualObservation],
    ] = defaultdict(list)

    for observation in observations:
        groups[observation.missing_digits].append(observation)

    eligible = {
        state: items
        for state, items in groups.items()
        if len(items) >= minimum_cases
    }

    ordered_states = sorted(
        eligible,
        key=lambda state: (
            len(state),
            -len(eligible[state]),
            tuple(sorted(state)),
        ),
    )

    print(
        f"\n===== STATI ESATTI CON ALMENO {minimum_cases} CASI ====="
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

    for state in ordered_states:
        (
            total,
            actual,
            predicted,
            bias,
            mae,
            _,
        ) = summarize(eligible[state])

        print(
            f"{format_digits(state):<16}"
            f"{total:<8}"
            f"{actual:>6.3f}  "
            f"{predicted:>7.3f}  "
            f"{bias:>+7.3f}  "
            f"{mae:>7.3f}"
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


def main() -> int:
    args = build_parser().parse_args()

    try:
        with LottoRepository(args.database) as repository:
            observations = collect_residual_observations(repository)

        if not observations:
            raise RuntimeError(
                "Nessuna osservazione residua disponibile."
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
        print(f"Stati osservati: {len(observations)}")

        (
            total,
            actual,
            predicted,
            bias,
            mae,
            rmse,
        ) = summarize(observations)

        print("\n===== RISULTATO COMPLESSIVO =====")
        print(f"Stati:                  {total}")
        print(f"Durata residua reale:   {actual:.3f}")
        print(f"Durata prevista Markov: {predicted:.3f}")
        print(f"Bias reale - prevista:  {bias:+.3f}")
        print(f"Errore assoluto medio:  {mae:.3f}")
        print(f"RMSE:                    {rmse:.3f}")

        by_missing_count: dict[
            int,
            list[MarkovResidualObservation],
        ] = defaultdict(list)

        by_expectation_band: dict[
            str,
            list[MarkovResidualObservation],
        ] = defaultdict(list)

        for observation in observations:
            by_missing_count[
                len(observation.missing_digits)
            ].append(observation)

            by_expectation_band[
                expectation_band(
                    observation.predicted_remaining
                )
            ].append(observation)

        print_group_table(
            "PER NUMERO DI CIFRE MANCANTI",
            by_missing_count,
        )

        print_group_table(
            "PER FASCIA DI ATTESA PREVISTA",
            by_expectation_band,
            sort_key=band_sort_key,
        )

        print_exact_states(
            observations,
            minimum_cases=args.minimum_state_cases,
        )

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
