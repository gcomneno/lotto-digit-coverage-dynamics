#!/usr/bin/env python3

"""Probabilità di completamento dei cicli naturali di copertura 0–9."""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from strategies.coverage_completion import (
    CoverageCompletionObservation,
    collect_completion_observations,
    exact_completion_probability,
)
from strategies.twin_digits import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")


def summarize(
    observations: Sequence[CoverageCompletionObservation],
) -> tuple[int, int, float, float, float]:
    total = len(observations)
    hits = sum(observation.completed_next for observation in observations)

    observed = hits / total if total else 0.0
    expected = (
        statistics.mean(
            exact_completion_probability(
                observation.missing_digits
            )
            for observation in observations
        )
        if observations
        else 0.0
    )

    return total, hits, observed, expected, observed - expected


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(str(digit) for digit in sorted(digits)) + "}"


def age_bucket(draws_in_cycle: int) -> str:
    if draws_in_cycle <= 4:
        return str(draws_in_cycle)

    return "5+"


def bucket_order(bucket: str) -> int:
    return int(bucket.rstrip("+"))


def completed_cycle_lengths(
    observations: Sequence[CoverageCompletionObservation],
) -> dict[tuple[str, int], int]:
    lengths: dict[tuple[str, int], int] = {}

    for observation in observations:
        if not observation.completed_next:
            continue

        key = (
            observation.wheel,
            observation.cycle_number,
        )

        lengths[key] = observation.draws_in_cycle + 1

    return lengths


def print_summary_table(
    title: str,
    groups: dict[object, list[CoverageCompletionObservation]],
    *,
    key_formatter=str,
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

    for key in sorted(groups):
        total, hits, observed, expected, delta = summarize(groups[key])

        print(
            f"{key_formatter(key):<14}"
            f"{total:<8}"
            f"{hits:<10}"
            f"{observed:>8.2%}  "
            f"{expected:>7.2%}  "
            f"{delta:>+7.2%}"
        )


def print_exact_states(
    observations: Sequence[CoverageCompletionObservation],
    minimum_cases: int,
) -> None:
    groups: dict[
        frozenset[int],
        list[CoverageCompletionObservation],
    ] = defaultdict(list)

    for observation in observations:
        groups[observation.missing_digits].append(observation)

    eligible = [
        (state, items)
        for state, items in groups.items()
        if len(items) >= minimum_cases
    ]

    eligible.sort(
        key=lambda item: (
            len(item[0]),
            -len(item[1]),
            tuple(sorted(item[0])),
        )
    )

    print(
        f"\n===== STATI ESATTI CON ALMENO {minimum_cases} CASI ====="
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

    for state, items in eligible:
        total, hits, observed, expected, delta = summarize(items)

        print(
            f"{format_digits(state):<14}"
            f"{total:<8}"
            f"{hits:<10}"
            f"{observed:>8.2%}  "
            f"{expected:>7.2%}  "
            f"{delta:>+7.2%}"
        )


def print_single_missing(
    observations: Sequence[CoverageCompletionObservation],
) -> None:
    groups: dict[int, list[CoverageCompletionObservation]] = defaultdict(list)

    for observation in observations:
        if len(observation.missing_digits) != 1:
            continue

        digit = next(iter(observation.missing_digits))
        groups[digit].append(observation)

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

    for digit in range(10):
        items = groups.get(digit, [])
        total, hits, observed, expected, delta = summarize(items)

        print(
            f"{digit:<7}"
            f"{total:<8}"
            f"{hits:<10}"
            f"{observed:>8.2%}  "
            f"{expected:>7.2%}  "
            f"{delta:>+7.2%}"
        )


def print_residual_duration(
    observations: Sequence[CoverageCompletionObservation],
) -> None:
    lengths = completed_cycle_lengths(observations)

    residuals: dict[int, list[int]] = defaultdict(list)
    censored = 0

    for observation in observations:
        key = (
            observation.wheel,
            observation.cycle_number,
        )

        cycle_length = lengths.get(key)

        if cycle_length is None:
            censored += 1
            continue

        residuals[len(observation.missing_digits)].append(
            cycle_length - observation.draws_in_cycle
        )

    print("\n===== DISTANZA RESIDUA DAL COMPLETAMENTO =====")
    print()
    print(
        "Sono inclusi soltanto gli stati appartenenti a cicli "
        "completati entro l'archivio."
    )
    print(f"Stati esclusi perché censurati a destra: {censored}")
    print()
    print(
        "Mancanti  Stati   Media residua  Mediana  Min–Max"
    )
    print(
        "--------  ------  -------------  -------  -------"
    )

    for missing_count in sorted(residuals):
        values = residuals[missing_count]

        print(
            f"{missing_count:<10}"
            f"{len(values):<8}"
            f"{statistics.mean(values):>11.2f}  "
            f"{statistics.median(values):>7.1f}  "
            f"{min(values)}–{max(values)}"
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


def main() -> int:
    args = build_parser().parse_args()

    try:
        with LottoRepository(args.database) as repository:
            observations = collect_completion_observations(repository)

        if not observations:
            raise RuntimeError(
                "Nessuna osservazione di copertura disponibile."
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
        print(f"Stati incompleti osservati: {len(observations)}")

        by_missing_count: dict[
            int,
            list[CoverageCompletionObservation],
        ] = defaultdict(list)

        by_cycle_age: dict[
            str,
            list[CoverageCompletionObservation],
        ] = defaultdict(list)

        for observation in observations:
            by_missing_count[
                len(observation.missing_digits)
            ].append(observation)

            by_cycle_age[
                age_bucket(observation.draws_in_cycle)
            ].append(observation)

        print_summary_table(
            "PROBABILITÀ PER NUMERO DI CIFRE MANCANTI",
            by_missing_count,
            key_label="Mancanti",
        )

        print_summary_table(
            "PROBABILITÀ PER ETÀ DEL CICLO",
            by_cycle_age,
            key_formatter=str,
            key_label="Estrazioni",
        )

        print_single_missing(observations)

        print_exact_states(
            observations,
            minimum_cases=args.minimum_state_cases,
        )

        print_residual_duration(observations)

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
