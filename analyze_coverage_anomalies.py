#!/usr/bin/env python3
"""Rilevatore descrittivo delle anomalie di copertura."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from lotto_digit_coverage.application.historical_anomalies import (
    ALL_CATEGORIES,
    AnomalyEvent,
    TransitionObservation,
    anomaly_identity,
    build_all_transitions,
    build_coverage_anomaly_report,
    build_transition_observations,
    detect_anomalies,
    detect_persistence_anomalies,
    detect_recurrence_anomalies,
    detect_transition_anomalies,
    format_state,
    make_primary_event,
    severity_for_probability,
    summary_document,
    surprisal,
    transition_surprise_probability,
    validate_anomalies,
)
from lotto_digit_coverage.infrastructure.historical_archives import (
    load_merged_coverage_draws,
)


DEFAULT_DATABASES = (
    Path("data/lotto-2023.sqlite3"),
    Path("data/lotto-2024.sqlite3"),
    Path("data/lotto-2025.sqlite3"),
    Path("data/lotto-current.sqlite3"),
)
DEFAULT_OUTPUT_PREFIX = Path("_work/coverage-anomalies-2023-2026")
DEFAULT_THRESHOLD = 0.01
DEFAULT_RECURRENCE_WINDOW = 10
DEFAULT_RECURRENCE_THRESHOLD = 0.01


def csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".17g")
    return value


def write_csv(events: Sequence[AnomalyEvent], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(AnomalyEvent.__dataclass_fields__)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for event in events:
            writer.writerow({key: csv_value(value) for key, value in asdict(event).items()})


def write_json(
    events: Sequence[AnomalyEvent],
    *,
    label: str,
    databases: Sequence[Path],
    threshold: float,
    recurrence_window: int,
    recurrence_threshold: float,
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "report_format_version": 1,
        "report_type": "coverage-anomalies",
        "label": label,
        "databases": [str(path) for path in databases],
        "primary_threshold": threshold,
        "recurrence_window": recurrence_window,
        "recurrence_threshold": recurrence_threshold,
        "definitions": {
            "A1": (
                "Prima soglia di persistenza superata in ciascun ciclo: il ciclo "
                "resta aperto per h passi da uno stato sorgente S con "
                "P(tau_S > h) <= primary_threshold."
            ),
            "A2": "Chiusura immediata S -> {} con probabilità <= primary_threshold.",
            "A3": (
                "Transizione di progresso non terminale S -> T. La soglia usa "
                "la massa delle transizioni non terminali non più probabili "
                "dell'esito osservato; atom_probability conserva K(S,T)."
            ),
            "A4": (
                "Ripetizione sulla stessa ruota della stessa chiave primaria "
                "entro recurrence_window transizioni valide. La probabilità "
                "è un limite superiore conservativo condizionato alla prima anomalia."
            ),
        },
        "recurrence_probability_note": (
            "A4 usa un limite superiore di Bonferroni sulla ricorrenza entro "
            "la finestra, condizionato al fatto che la prima anomalia sia già "
            "avvenuta. pair_probability registra separatamente il prodotto "
            "dei due punteggi primari e non è usato come p-value di finestra."
        ),
        "summary": summary_document(events),
        "events": [asdict(event) for event in events],
    }
    output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render_summary(events: Sequence[AnomalyEvent]) -> str:
    summary = summary_document(events)
    counts = summary["category_counts"]
    return "\n".join(
        (
            f"Eventi totali:        {summary['event_count']}",
            "Categorie:           "
            + ", ".join(f"{category}={counts[category]}" for category in ALL_CATEGORIES),
            f"Firme uniche:        {summary['unique_signatures']}",
            f"Duplicati esatti:    {summary['duplicate_event_count']}",
            f"Overlap primari:     {summary['primary_transition_overlap_count']}",
        )
    )


def render_top_events(events: Sequence[AnomalyEvent], limit: int = 15) -> str:
    ordered = sorted(
        events,
        key=lambda item: (
            item.conditional_probability,
            item.target_date,
            item.wheel_order,
        ),
    )[:limit]
    lines = [
        "Cat Data       Ruota       P(evento)  I      Firma",
        "--- ---------- ----------- ---------- ------ ----------------",
    ]
    for event in ordered:
        lines.append(
            f"{event.category:<3} {event.target_date:<10} {event.wheel:<11} "
            f"{event.conditional_probability:>10.6%} {event.surprisal:>6.3f} "
            f"{event.signature}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rileva quattro categorie descrittive di anomalie della copertura."
    )
    parser.add_argument("--database", action="append", type=Path, dest="databases")
    parser.add_argument("--label", default="historical-2023-2026")
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument(
        "--recurrence-window", type=int, default=DEFAULT_RECURRENCE_WINDOW
    )
    parser.add_argument(
        "--recurrence-threshold", type=float, default=DEFAULT_RECURRENCE_THRESHOLD
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    databases = tuple(args.databases if args.databases else DEFAULT_DATABASES)
    csv_output = args.output_prefix.with_suffix(".csv")
    json_output = args.output_prefix.with_suffix(".json")

    try:
        report = build_coverage_anomaly_report(
            load_merged_coverage_draws(databases),
            threshold=args.threshold,
            recurrence_window=args.recurrence_window,
            recurrence_threshold=args.recurrence_threshold,
        )
        write_csv(report.events, csv_output)
        write_json(
            report.events,
            label=args.label,
            databases=databases,
            threshold=args.threshold,
            recurrence_window=args.recurrence_window,
            recurrence_threshold=args.recurrence_threshold,
            output=json_output,
        )
        print("===== ANOMALIE DI COPERTURA =====")
        print(f"Segmento:             {args.label}")
        print(f"Transizioni valide:   {len(report.transitions)}")
        print(render_summary(report.events))
        print("\n===== EVENTI PIÙ RARI =====")
        print(render_top_events(report.events))
        print(f"\nCSV:  {csv_output}")
        print(f"JSON: {json_output}")
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
