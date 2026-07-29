#!/usr/bin/env python3

"""Validazione descrittiva della calibrazione del modello Markov."""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Hashable, Sequence

from strategies.coverage_markov_validation import (
    MarkovCalibrationObservation,
    collect_calibration_observations,
)
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")
DEFAULT_HORIZONS = (1, 2, 3, 5)


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def probability_band(probability: float) -> str:
    if not 0.0 <= probability <= 1.0:
        raise ValueError(
            "La probabilità deve essere compresa tra 0 e 1."
        )

    if probability < 0.10:
        return "0–10%"
    if probability < 0.25:
        return "10–25%"
    if probability < 0.50:
        return "25–50%"
    if probability < 0.75:
        return "50–75%"
    if probability < 0.90:
        return "75–90%"

    return "90–100%"


def band_sort_key(label: str) -> int:
    order = {
        "0–10%": 0,
        "10–25%": 1,
        "25–50%": 2,
        "50–75%": 3,
        "75–90%": 4,
        "90–100%": 5,
    }

    return order[label]


def summarize(
    observations: Sequence[MarkovCalibrationObservation],
) -> tuple[int, int, float, float, float, float]:
    total = len(observations)
    hits = sum(
        observation.completed_within
        for observation in observations
    )

    observed = hits / total if total else 0.0

    predicted = (
        statistics.mean(
            observation.predicted_probability
            for observation in observations
        )
        if observations
        else 0.0
    )

    brier = (
        statistics.mean(
            (
                float(observation.completed_within)
                - observation.predicted_probability
            )
            ** 2
            for observation in observations
        )
        if observations
        else 0.0
    )

    return (
        total,
        hits,
        observed,
        predicted,
        observed - predicted,
        brier,
    )


def grouped_calibration_error(
    groups: dict[
        Hashable,
        list[MarkovCalibrationObservation],
    ],
) -> float:
    total = sum(len(items) for items in groups.values())

    if total == 0:
        return 0.0

    return sum(
        len(items)
        / total
        * abs(summarize(items)[4])
        for items in groups.values()
    )


def print_overall(
    observations: Sequence[MarkovCalibrationObservation],
) -> None:
    groups: dict[
        int,
        list[MarkovCalibrationObservation],
    ] = defaultdict(list)

    for observation in observations:
        groups[observation.horizon].append(observation)

    print("\n===== CALIBRAZIONE COMPLESSIVA =====")
    print()
    print(
        "Entro  Casi    Chiusure  Osservato  "
        "Previsto   Delta    Brier"
    )
    print(
        "-----  ------  --------  ---------  "
        "---------  --------  -------"
    )

    for horizon in sorted(groups):
        (
            total,
            hits,
            observed,
            predicted,
            delta,
            brier,
        ) = summarize(groups[horizon])

        print(
            f"{horizon:<7}"
            f"{total:<8}"
            f"{hits:<10}"
            f"{observed:>8.2%}  "
            f"{predicted:>8.2%}  "
            f"{delta:>+7.2%}  "
            f"{brier:>7.4f}"
        )


def print_probability_bands(
    observations: Sequence[MarkovCalibrationObservation],
) -> None:
    by_horizon: dict[
        int,
        list[MarkovCalibrationObservation],
    ] = defaultdict(list)

    for observation in observations:
        by_horizon[observation.horizon].append(observation)

    for horizon in sorted(by_horizon):
        groups: dict[
            str,
            list[MarkovCalibrationObservation],
        ] = defaultdict(list)

        for observation in by_horizon[horizon]:
            groups[
                probability_band(
                    observation.predicted_probability
                )
            ].append(observation)

        print(
            f"\n===== FASCE DI PROBABILITÀ: ENTRO {horizon} ====="
        )
        print()
        print(
            "Fascia    Casi    Chiusure  Osservato  "
            "Previsto   Delta"
        )
        print(
            "--------  ------  --------  ---------  "
            "---------  --------"
        )

        for band in sorted(
            groups,
            key=band_sort_key,
        ):
            (
                total,
                hits,
                observed,
                predicted,
                delta,
                _,
            ) = summarize(groups[band])

            print(
                f"{band:<10}"
                f"{total:<8}"
                f"{hits:<10}"
                f"{observed:>8.2%}  "
                f"{predicted:>8.2%}  "
                f"{delta:>+7.2%}"
            )

        print(
            "\nErrore medio assoluto ponderato "
            f"per fasce: {grouped_calibration_error(groups):.2%}"
        )


def print_exact_states(
    observations: Sequence[MarkovCalibrationObservation],
    *,
    horizon: int,
    minimum_cases: int,
) -> None:
    groups: dict[
        frozenset[int],
        list[MarkovCalibrationObservation],
    ] = defaultdict(list)

    for observation in observations:
        if observation.horizon != horizon:
            continue

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
        f"\n===== STATI ESATTI: ENTRO {horizon}, "
        f"ALMENO {minimum_cases} CASI ====="
    )
    print()
    print(
        "Mancanti      Casi    Chiusure  Osservato  "
        "Previsto   Delta"
    )
    print(
        "------------  ------  --------  ---------  "
        "---------  --------"
    )

    for state, items in eligible:
        (
            total,
            hits,
            observed,
            predicted,
            delta,
            _,
        ) = summarize(items)

        print(
            f"{format_digits(state):<14}"
            f"{total:<8}"
            f"{hits:<10}"
            f"{observed:>8.2%}  "
            f"{predicted:>8.2%}  "
            f"{delta:>+7.2%}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta le probabilità Markov con i "
            "completamenti osservati nell'archivio."
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
            observations = collect_calibration_observations(
                repository,
                horizons=DEFAULT_HORIZONS,
            )

        if not observations:
            raise RuntimeError(
                "Nessuna osservazione di calibrazione disponibile."
            )

        print("===== VALIDAZIONE DEL MODELLO MARKOV =====")
        print(f"Database: {args.database}")
        print(
            "Orizzonti: "
            + ", ".join(
                str(horizon)
                for horizon in DEFAULT_HORIZONS
            )
        )
        print(
            "Le osservazioni sono sovrapposte e dipendenti: "
            "il rapporto valuta calibrazione descrittiva, "
            "non significatività inferenziale."
        )
        print(
            f"Osservazioni totali: {len(observations)}"
        )

        print_overall(observations)
        print_probability_bands(observations)

        print_exact_states(
            observations,
            horizon=1,
            minimum_cases=args.minimum_state_cases,
        )

        print_exact_states(
            observations,
            horizon=3,
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
