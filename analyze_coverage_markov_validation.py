#!/usr/bin/env python3

"""Validazione descrittiva della calibrazione del modello Markov."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Hashable, Sequence
from pathlib import Path

from lotto_digit_coverage.application.historical_markov import (
    CalibrationBandReport,
    CalibrationGroup,
    MarkovValidationReport,
    build_markov_validation_report,
    grouped_calibration_error as _grouped_calibration_error,
    probability_band,
    probability_band_sort_key,
    summarize_calibration,
)
from strategies.coverage_markov_validation import MarkovCalibrationObservation
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")
DEFAULT_HORIZONS = (1, 2, 3, 5)


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def band_sort_key(label: str) -> int:
    return probability_band_sort_key(label)


def summarize(
    observations: Sequence[MarkovCalibrationObservation],
) -> tuple[int, int, float, float, float, float]:
    """Compatibility tuple for callers that predate the application report."""

    summary = summarize_calibration(observations)
    return (
        summary.cases,
        summary.completions,
        summary.observed_probability,
        summary.predicted_probability,
        summary.delta,
        summary.brier_score,
    )


def grouped_calibration_error(
    groups: dict[Hashable, list[MarkovCalibrationObservation]],
) -> float:
    return _grouped_calibration_error(groups)


def _format_group_key(key: object) -> str:
    if isinstance(key, frozenset):
        return format_digits(key)
    return str(key)


def print_overall(report: MarkovValidationReport) -> None:
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

    for group in report.overall:
        summary = group.summary
        print(
            f"{group.key:<7}"
            f"{summary.cases:<8}"
            f"{summary.completions:<10}"
            f"{summary.observed_probability:>8.2%}  "
            f"{summary.predicted_probability:>8.2%}  "
            f"{summary.delta:>+7.2%}  "
            f"{summary.brier_score:>7.4f}"
        )


def print_probability_band_report(band_report: CalibrationBandReport) -> None:
    print(
        f"\n===== FASCE DI PROBABILITÀ: ENTRO "
        f"{band_report.horizon} ====="
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

    for group in band_report.groups:
        summary = group.summary
        print(
            f"{group.key:<10}"
            f"{summary.cases:<8}"
            f"{summary.completions:<10}"
            f"{summary.observed_probability:>8.2%}  "
            f"{summary.predicted_probability:>8.2%}  "
            f"{summary.delta:>+7.2%}"
        )

    print(
        "\nErrore medio assoluto ponderato per fasce: "
        f"{band_report.weighted_absolute_error:.2%}"
    )


def print_exact_state_groups(
    groups: Sequence[CalibrationGroup],
    *,
    horizon: int,
    minimum_cases: int,
) -> None:
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

    for group in groups:
        summary = group.summary
        print(
            f"{_format_group_key(group.key):<14}"
            f"{summary.cases:<8}"
            f"{summary.completions:<10}"
            f"{summary.observed_probability:>8.2%}  "
            f"{summary.predicted_probability:>8.2%}  "
            f"{summary.delta:>+7.2%}"
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


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        with LottoRepository(args.database) as repository:
            report = build_markov_validation_report(
                repository,
                horizons=DEFAULT_HORIZONS,
                minimum_state_cases=args.minimum_state_cases,
            )

        print("===== VALIDAZIONE DEL MODELLO MARKOV =====")
        print(f"Database: {args.database}")
        print(
            "Orizzonti: "
            + ", ".join(str(horizon) for horizon in report.horizons)
        )
        print(
            "Le osservazioni sono sovrapposte e dipendenti: "
            "il rapporto valuta calibrazione descrittiva, "
            "non significatività inferenziale."
        )
        print(f"Osservazioni totali: {len(report.observations)}")

        print_overall(report)
        for band_report in report.probability_bands:
            print_probability_band_report(band_report)
        print_exact_state_groups(
            report.exact_states_h1,
            horizon=1,
            minimum_cases=report.minimum_state_cases,
        )
        print_exact_state_groups(
            report.exact_states_h3,
            horizon=3,
            minimum_cases=report.minimum_state_cases,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
