#!/usr/bin/env python3

"""Statistiche recenti sulle cifre mancanti intercettate."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence

from strategies.cli_table import Column
from strategies.coverage_hit_statistics import (
    CoverageHitObservation,
    CoverageHitSummary,
    build_coverage_hit_experiment,
    select_latest_targets,
    summarize_coverage_hits,
)
from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")
DEFAULT_TARGET_COUNT = 10


COLUMNS: tuple[Column[CoverageHitSummary], ...] = (
    Column(
        key="top",
        label="TOP",
        getter=lambda summary: summary.most_present_count,
    ),
    Column(
        key="missing",
        label="Manc.",
        getter=lambda summary: summary.missing_count,
    ),
    Column(
        key="threshold",
        label="Soglia",
        getter=lambda summary: summary.threshold,
    ),
    Column(
        key="markov",
        label="Markov",
        getter=lambda summary: (
            summary.mean_completion_within_one
        ),
    ),
    Column(
        key="expected",
        label="Atteso",
        getter=lambda summary: (
            summary.mean_threshold_probability
        ),
    ),
    Column(
        key="cases",
        label="Casi",
        getter=lambda summary: summary.attempts,
    ),
    Column(
        key="obtained",
        label="Ottenute",
        getter=lambda summary: summary.obtained,
    ),
    Column(
        key="missed",
        label="Mancate",
        getter=lambda summary: summary.missed,
    ),
    Column(
        key="success_rate",
        label="Successo",
        getter=lambda summary: summary.success_rate,
    ),
    Column(
        key="excess",
        label="Scarto",
        getter=lambda summary: summary.success_excess,
    ),
    Column(
        key="mean_hit_digits",
        label="Cifre/caso",
        getter=lambda summary: summary.mean_hit_digits,
    ),
    Column(
        key="evidence",
        label="Evidenza",
        # Ordine semantico della forza del campione,
        # non ordine alfabetico dell'etichetta.
        getter=lambda summary: summary.attempts,
    ),
)

COLUMNS_BY_KEY = {
    column.key: column
    for column in COLUMNS
}


def resolve_sort_specification(
    specification: str,
) -> tuple[
    tuple[Column[CoverageHitSummary], bool],
    ...,
]:
    """Converte una specifica CLI in colonne e direzioni."""

    tokens = tuple(
        item.strip()
        for item in specification.split(",")
        if item.strip()
    )

    if not tokens:
        raise ValueError(
            "La specifica di ordinamento non può essere vuota."
        )

    resolved = []

    for token in tokens:
        descending = token.startswith("-")
        key = token[1:] if descending else token

        if not key:
            raise ValueError(
                "Nome colonna mancante nella specifica "
                "di ordinamento."
            )

        column = COLUMNS_BY_KEY.get(key)

        if column is None:
            raise ValueError(
                "Colonna di ordinamento sconosciuta: "
                f"{key}"
            )

        resolved.append(
            (column, descending)
        )

    return tuple(resolved)


def sort_summaries(
    summaries: Sequence[CoverageHitSummary],
    specification: str,
) -> tuple[CoverageHitSummary, ...]:
    """Ordina stabilmente il riepilogo secondo la specifica CLI."""

    result = list(summaries)
    resolved = resolve_sort_specification(
        specification
    )

    for column, descending in reversed(resolved):
        result.sort(
            key=column.getter,
            reverse=descending,
        )

    return tuple(result)


def format_sort_specification(
    specification: str,
) -> str:
    """Descrive in forma leggibile l'ordinamento applicato."""

    return ", ".join(
        (
            f"{column.label} "
            f"{'↓' if descending else '↑'}"
        )
        for column, descending
        in resolve_sort_specification(specification)
    )


def print_sort_columns() -> None:
    """Mostra le colonne utilizzabili con --sort."""

    print("Colonne disponibili per --sort")
    print()

    for column in COLUMNS:
        print(
            f"{column.key:<18} "
            f"{column.label}"
        )

    print()
    print("Esempi:")
    print("  --sort=-cases")
    print("  --sort=missing,-success_rate")
    print("  --sort=evidence,-excess")


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def write_summary_csv(
    destination: Path,
    summaries: Sequence[CoverageHitSummary],
) -> None:
    """Esporta il riepilogo in CSV con valori numerici grezzi."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = (
        "top",
        "missing",
        "threshold",
        "markov_probability",
        "expected_probability",
        "cases",
        "obtained",
        "missed",
        "success_rate",
        "excess",
        "mean_hit_digits",
        "evidence_level",
    )

    with destination.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
        )
        writer.writeheader()

        for summary in summaries:
            writer.writerow(
                {
                    "top": summary.most_present_count,
                    "missing": summary.missing_count,
                    "threshold": max(
                        1,
                        summary.missing_count - 1,
                    ),
                    "markov_probability": (
                        summary.mean_completion_within_one
                    ),
                    "expected_probability": (
                        summary.mean_threshold_probability
                    ),
                    "cases": summary.attempts,
                    "obtained": summary.obtained,
                    "missed": summary.missed,
                    "success_rate": summary.success_rate,
                    "excess": summary.success_excess,
                    "mean_hit_digits": (
                        summary.mean_hit_digits
                    ),
                    "evidence_level": (
                        summary.evidence_level
                    ),
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica sulle ultime estrazioni se compare "
            "il numero minimo richiesto di cifre Mancanti: "
            "N-1 quando N > 1, altrimenti 1."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    parser.add_argument(
        "--last",
        type=int,
        default=DEFAULT_TARGET_COUNT,
        metavar="N",
        help=(
            "Numero di estrazioni target recenti "
            "da includere (default: 10)."
        ),
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Mostra anche ogni osservazione per ruota.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        metavar="FILE",
        help=(
            "Esporta la statistica riepilogativa in CSV "
            "con valori numerici ordinabili."
        ),
    )
    parser.add_argument(
        "--sort",
        default="missing,top",
        metavar="COLONNE",
        help=(
            "Ordina il riepilogo con una lista di colonne "
            "separate da virgola. "
            "Prefisso '-' = ordine decrescente.\n\n"
            "Esempi: "
            "--sort=-cases | "
            "--sort=missing,-success_rate | "
            "--sort=evidence,-excess"
        ),
    )
    parser.add_argument(
        "--list-sort-columns",
        action="store_true",
        help=(
            "Elenca tutte le colonne disponibili "
            "per --sort ed esce."
        ),
    )

    return parser


def print_details(
    observations: Sequence[CoverageHitObservation],
) -> None:
    print("===== DETTAGLIO WALK-FORWARD =====")
    print(
        f"{'Target':<8}"
        f"{'Data':<12}"
        f"{'Ruota':<12}"
        f"{'TOP':<6}"
        f"{'Manc.':<7}"
        f"{'Soglia':<8}"
        f"{'Entro 1':<10}"
        f"{'Atteso':<10}"
        f"{'Mancanti':<18}"
        f"{'Colpite':<18}"
        "Esito"
    )
    print(
        f"{'------':<8}"
        f"{'----------':<12}"
        f"{'----------':<12}"
        f"{'---':<6}"
        f"{'-----':<7}"
        f"{'------':<8}"
        f"{'-------':<10}"
        f"{'-------':<10}"
        f"{'-------------':<18}"
        f"{'-------------':<18}"
        "-------"
    )

    for observation in observations:
        print(
            f"{observation.target_draw:<8}"
            f"{observation.target_date:<12}"
            f"{observation.wheel:<12}"
            f"{observation.most_present_count:<6}"
            f"{observation.missing_count:<7}"
            f"{observation.required_hit_count:<8}"
            f"{observation.completion_within_one:<9.2%} "
            f"{observation.threshold_probability:<9.2%} "
            f"{format_digits(observation.missing_digits):<18}"
            f"{format_digits(observation.hit_digits):<18}"
            f"{'OTTENUTA' if observation.obtained else 'MANCATA'}"
        )

    print()


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()

    if arguments.last <= 0:
        parser.error("--last deve essere un intero positivo.")

    if arguments.list_sort_columns:
        print_sort_columns()
        return 0

    try:
        sort_description = format_sort_specification(
            arguments.sort
        )
    except ValueError as error:
        parser.error(str(error))

    with LottoRepository(
        arguments.database
    ) as repository:
        draws_by_wheel = load_draws_by_wheel(
            repository
        )

    all_observations = build_coverage_hit_experiment(
        draws_by_wheel
    )
    observations = select_latest_targets(
        all_observations,
        target_count=arguments.last,
    )

    if not observations:
        raise RuntimeError(
            "Nessuna osservazione walk-forward disponibile."
        )

    target_keys = sorted(
        {
            (
                observation.target_date,
                observation.target_draw,
            )
            for observation in observations
        }
    )

    print(
        f"Database: {arguments.database}"
    )
    print(
        "Estrazioni target analizzate: "
        f"{len(target_keys)}"
    )
    print(
        "Intervallo: "
        f"{target_keys[0][1]} del {target_keys[0][0]} "
        "→ "
        f"{target_keys[-1][1]} del {target_keys[-1][0]}"
    )
    print(
        "Definizione ottenuta: vengono intercettate "
        "almeno N-1 cifre Mancanti; con N=1 "
        "è richiesta l'unica cifra mancante."
    )
    print(
        "Nota: Markov rappresenta la probabilità media "
        "di copertura completa; Atteso rappresenta invece "
        "la probabilità teorica esatta della soglia qui contata."
    )
    print()

    if arguments.details:
        print_details(observations)

    summaries = sort_summaries(
        summarize_coverage_hits(
            observations
        ),
        arguments.sort,
    )

    print(
        f"Ordinamento: {sort_description}"
    )
    print()
    print("===== STATISTICA PER FASCIA =====")
    print(
        f"{'TOP':>3}  "
        f"{'Manc.':>5}  "
        f"{'Soglia':>6}  "
        f"{'Markov':>8}  "
        f"{'Atteso':>8}  "
        f"{'Casi':>5}  "
        f"{'Ottenute':>8}  "
        f"{'Mancate':>7}  "
        f"{'Successo':>8}  "
        f"{'Scarto':>8}  "
        f"{'Cifre/caso':>10}  "
        f"{'Evidenza':>11}"
    )
    print(
        f"{'---':>3}  "
        f"{'-----':>5}  "
        f"{'------':>6}  "
        f"{'-------':>8}  "
        f"{'-------':>8}  "
        f"{'-----':>5}  "
        f"{'--------':>8}  "
        f"{'-------':>7}  "
        f"{'--------':>8}  "
        f"{'--------':>8}  "
        f"{'----------':>10}  "
        f"{'-----------':>11}"
    )

    for summary in summaries:
        print(
            f"{summary.most_present_count:>3}  "
            f"{summary.missing_count:>5}  "
            f"{max(1, summary.missing_count - 1):>6}  "
            f"{summary.mean_completion_within_one:>7.2%}  "
            f"{summary.mean_threshold_probability:>7.2%}  "
            f"{summary.attempts:>5}  "
            f"{summary.obtained:>8}  "
            f"{summary.missed:>7}  "
            f"{summary.success_rate:>7.2%}  "
            f"{summary.success_excess:>+7.2%}  "
            f"{summary.mean_hit_digits:>10.3f}  "
            f"{summary.evidence_level:>11}"
        )

    total_attempts = len(observations)
    total_obtained = sum(
        observation.obtained
        for observation in observations
    )

    print()
    print(
        "Totale osservazioni ruota-target: "
        f"{total_attempts}"
    )
    print(
        "Totale ottenute: "
        f"{total_obtained}/{total_attempts} "
        f"({total_obtained / total_attempts:.2%})"
    )

    if arguments.csv is not None:
        write_summary_csv(
            arguments.csv,
            summaries,
        )
        print(
            f"CSV esportato: {arguments.csv}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
