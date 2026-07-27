#!/usr/bin/env python3

"""Analisi dei tempi di ritorno delle singole cifre."""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from strategies.digit_return_times import (
    DigitReturnObservation,
    POSITIONS,
    collect_return_observations,
    theoretical_hit_probability,
)
from strategies.twin_digits import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")
MAX_EXPLICIT_STREAK = 8


def streak_bucket(absence_streak: int) -> str:
    if absence_streak <= 0:
        raise ValueError(
            "La durata dell'assenza deve essere positiva."
        )

    if absence_streak <= MAX_EXPLICIT_STREAK:
        return str(absence_streak)

    return f"{MAX_EXPLICIT_STREAK + 1}+"


def bucket_sort_key(bucket: str) -> int:
    if bucket.endswith("+"):
        return int(bucket[:-1])

    return int(bucket)


def summarize(
    observations: Sequence[DigitReturnObservation],
) -> tuple[int, int, float, float, float]:
    total = len(observations)
    hits = sum(observation.hit for observation in observations)

    observed_rate = hits / total if total else 0.0

    expected_rate = (
        statistics.mean(
            theoretical_hit_probability(
                observation.digit,
                observation.position,
            )
            for observation in observations
        )
        if observations
        else 0.0
    )

    return (
        total,
        hits,
        observed_rate,
        expected_rate,
        observed_rate - expected_rate,
    )


def print_hazard_tables(
    observations: Sequence[DigitReturnObservation],
) -> None:
    labels = {
        "any": "QUALUNQUE POSIZIONE",
        "tens": "SOLO DECINE",
        "units": "SOLO UNITÀ",
    }

    for position in POSITIONS:
        selected = tuple(
            observation
            for observation in observations
            if observation.position == position
        )

        grouped: dict[
            str,
            list[DigitReturnObservation],
        ] = defaultdict(list)

        for observation in selected:
            grouped[
                streak_bucket(observation.absence_streak)
            ].append(observation)

        print(f"\n===== {labels[position]} =====")
        print()
        print(
            "Assenze  Casi    Hit     Osservato  "
            "Atteso    Delta"
        )
        print(
            "-------  ------  ------  ---------  "
            "--------  --------"
        )

        for bucket in sorted(
            grouped,
            key=bucket_sort_key,
        ):
            (
                total,
                hits,
                observed,
                expected,
                delta,
            ) = summarize(grouped[bucket])

            print(
                f"{bucket:<9}"
                f"{total:<8}"
                f"{hits:<8}"
                f"{observed:>8.2%}  "
                f"{expected:>7.2%}  "
                f"{delta:>+7.2%}"
            )


def print_any_position_by_digit(
    observations: Sequence[DigitReturnObservation],
) -> None:
    selected = tuple(
        observation
        for observation in observations
        if observation.position == "any"
    )

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

    for digit in range(10):
        digit_observations = tuple(
            observation
            for observation in selected
            if observation.digit == digit
        )

        (
            total,
            hits,
            observed,
            expected,
            delta,
        ) = summarize(digit_observations)

        max_streak = max(
            (
                observation.absence_streak
                for observation in digit_observations
            ),
            default=0,
        )

        print(
            f"{digit:<7}"
            f"{total:<8}"
            f"{hits:<8}"
            f"{observed:>8.2%}  "
            f"{expected:>8.2%}  "
            f"{delta:>+7.2%}  "
            f"{max_streak:>11}"
        )


def print_long_absences(
    observations: Sequence[DigitReturnObservation],
) -> None:
    selected = tuple(
        observation
        for observation in observations
        if observation.position == "any"
        and observation.absence_streak >= 5
    )

    print("\n===== QUALUNQUE POSIZIONE: ASSENZE DA 5+ =====")
    print()
    print(
        "Cifra  Casi  Hit  Osservato  Baseline   Delta"
    )
    print(
        "-----  ----  ---  ---------  ---------  --------"
    )

    for digit in range(10):
        digit_observations = tuple(
            observation
            for observation in selected
            if observation.digit == digit
        )

        if not digit_observations:
            continue

        (
            total,
            hits,
            observed,
            expected,
            delta,
        ) = summarize(digit_observations)

        print(
            f"{digit:<7}"
            f"{total:<6}"
            f"{hits:<5}"
            f"{observed:>8.2%}  "
            f"{expected:>8.2%}  "
            f"{delta:>+7.2%}"
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


def main() -> int:
    args = build_parser().parse_args()

    try:
        with LottoRepository(args.database) as repository:
            observations = collect_return_observations(repository)

        if not observations:
            raise RuntimeError(
                "Nessuna osservazione disponibile."
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

        print_hazard_tables(observations)
        print_any_position_by_digit(observations)
        print_long_absences(observations)

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
