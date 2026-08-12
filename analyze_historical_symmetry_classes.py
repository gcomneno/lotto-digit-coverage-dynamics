#!/usr/bin/env python3

"""Confronto empirico one-step delle 27 classi strutturali."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from lotto_digit_coverage.application.historical_symmetry import (
    ClassObservation,
    EmpiricalClassRow,
    build_all_observations,
    build_class_observations,
    build_empirical_rows,
    build_historical_symmetry_report,
    class_identifier,
    format_state,
    ordered_draws,
    validate_rows,
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
DEFAULT_CSV_OUTPUT = Path("_work/historical-symmetry-classes.csv")
DEFAULT_JSON_OUTPUT = Path("_work/historical-symmetry-classes.json")


def load_merged_draws(database_paths: Sequence[Path]):
    """Compatibility composition helper; persistence lives in infrastructure."""
    return load_merged_coverage_draws(database_paths)


def csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".17g")
    return value


def write_csv(rows: Sequence[EmpiricalClassRow], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    documents = [asdict(row) for row in rows]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(documents[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        for document in documents:
            writer.writerow({key: csv_value(value) for key, value in document.items()})


def write_json(
    rows: Sequence[EmpiricalClassRow],
    observations: Sequence[ClassObservation],
    database_paths: Sequence[Path],
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    observed_dates = [observation.target_date for observation in observations]
    document = {
        "report_format_version": 1,
        "report_type": "historical-symmetry-class-one-step-comparison",
        "segment": (
            f"{min(observed_dates)[:4]}-{max(observed_dates)[:4]}"
            if observed_dates
            else None
        ),
        "database_paths": [str(path) for path in database_paths],
        "first_target_date": min(observed_dates) if observed_dates else None,
        "last_target_date": max(observed_dates) if observed_dates else None,
        "class_count": len(rows),
        "observation_count": len(observations),
        "interpretation": (
            "Descriptive pooled comparison. Wheels share the draw calendar "
            "and are not assumed independent."
        ),
        "rows": [asdict(row) for row in rows],
    }
    output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render_table(rows: Sequence[EmpiricalClassRow]) -> str:
    lines = [
        "Classe             Stato       N      Hit    Teoria    Osservata   Diff. pp",
        "------------------ --------- ------ ------ --------- ----------- --------",
    ]
    for row in rows:
        observed = (
            "—" if row.observed_frequency is None else f"{row.observed_frequency:9.3%}"
        )
        difference = (
            "—"
            if row.difference_percentage_points is None
            else f"{row.difference_percentage_points:+8.3f}"
        )
        lines.append(
            f"{row.class_id:<18} {row.canonical_state:<9} "
            f"{row.observations:>6} {row.observed_completions:>6} "
            f"{row.theoretical_probability:>9.3%} {observed:>11} {difference:>8}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Confronta le frequenze storiche one-step delle 27 classi strutturali."
    )
    parser.add_argument("--database", action="append", type=Path, dest="databases")
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    databases = tuple(args.databases if args.databases else DEFAULT_DATABASES)
    try:
        draws_by_wheel = load_merged_coverage_draws(databases)
        report = build_historical_symmetry_report(draws_by_wheel)
        write_csv(report.rows, args.csv_output)
        write_json(report.rows, report.observations, databases, args.json_output)
        print(f"Ruote:        {report.wheel_count}")
        print(f"Osservazioni: {len(report.observations)}")
        print(f"Classi:       {len(report.rows)}")
        print()
        print(render_table(report.rows))
        print()
        print(f"CSV:  {args.csv_output}")
        print(f"JSON: {args.json_output}")
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
