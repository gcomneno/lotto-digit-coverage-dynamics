#!/usr/bin/env python3

"""Backtest walk-forward delle frequenze rolling delle cifre."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, fields
from pathlib import Path
from typing import Sequence

from lotto_digit_coverage.application.historical_rolling import (
    RollingFrequencyResultRow,
    build_result_rows,
    build_rolling_frequency_report,
    safe_ratio,
)
from lotto_digit_coverage.infrastructure.historical_archives import (
    load_merged_rolling_draws,
)


DEFAULT_DATABASES = (
    Path("data/lotto-2023.sqlite3"),
    Path("data/lotto-2024.sqlite3"),
    Path("data/lotto-2025.sqlite3"),
    Path("data/lotto-current.sqlite3"),
)
DEFAULT_WINDOW_SIZES = (3, 6, 8, 12)
DEFAULT_PERIODS = (
    ("development", "2023-01-01", "2025-12-31"),
    ("held-out", "2026-01-01", "2026-12-31"),
)
DEFAULT_REPETITIONS = 1_000
DEFAULT_SEED = 20_260_731
DEFAULT_CSV_OUTPUT = Path("_work/rolling-frequency-backtest.csv")
DEFAULT_JSON_OUTPUT = Path("_work/rolling-frequency-backtest.json")


def load_merged_draws(databases: Sequence[Path]):
    """Compatibility helper preserving the frozen rolling merge semantics."""
    return load_merged_rolling_draws(databases)


def write_csv(rows: Sequence[RollingFrequencyResultRow], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = tuple(field.name for field in fields(RollingFrequencyResultRow))
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(
    rows: Sequence[RollingFrequencyResultRow],
    *,
    databases: Sequence[Path],
    repetitions: int,
    base_seed: int,
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    unique_periods: list[dict[str, str]] = []
    for row in rows:
        period = {
            "name": row.period,
            "start_date": row.start_date,
            "end_date": row.end_date,
        }
        if period not in unique_periods:
            unique_periods.append(period)
    document = {
        "database_paths": [str(database) for database in databases],
        "row_count": len(rows),
        "window_sizes": sorted({row.window_size for row in rows}),
        "periods": unique_periods,
        "repetitions": repetitions,
        "base_seed": base_seed,
        "rows": [asdict(row) for row in rows],
    }
    output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render_table(rows: Sequence[RollingFrequencyResultRow]) -> str:
    lines = [
        (
            "N   Periodo       Obs.   Cand.  Hit n.  Cas. n.  Rap. n.  p num.   "
            "Hit ambi  Cas. ambi  Rap. a.  p ambo"
        ),
        (
            "--  ------------  -----  -----  ------  -------  -------  -------  "
            "--------  ---------  -------  -------"
        ),
    ]
    for row in rows:
        lines.append(
            f"{row.window_size:<3} {row.period:<12} "
            f"{row.observation_count:>5} {row.candidate_number_count:>6} "
            f"{row.observed_hit_number_count:>6} "
            f"{row.random_mean_hit_number_count:>7.2f} "
            f"{row.observed_to_random_number_ratio:>7.3f} "
            f"{row.empirical_p_value_hit_number:>7.4f} "
            f"{row.observed_hit_ambo_count:>8} "
            f"{row.random_mean_hit_ambo_count:>9.2f} "
            f"{row.observed_to_random_ambo_ratio:>7.3f} "
            f"{row.empirical_p_value_hit_ambo:>7.4f}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Esegue il backtest walk-forward delle cifre più frequenti su "
            "finestre rolling e lo confronta con rose casuali della stessa dimensione."
        )
    )
    parser.add_argument("--database", action="append", type=Path, dest="databases")
    parser.add_argument(
        "--window-size", action="append", type=int, dest="window_sizes"
    )
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    databases = tuple(args.databases if args.databases else DEFAULT_DATABASES)
    window_sizes = tuple(
        args.window_sizes if args.window_sizes else DEFAULT_WINDOW_SIZES
    )
    try:
        draws_by_wheel = load_merged_rolling_draws(databases)
        report = build_rolling_frequency_report(
            draws_by_wheel,
            window_sizes=window_sizes,
            periods=DEFAULT_PERIODS,
            repetitions=args.repetitions,
            base_seed=args.seed,
        )
        write_csv(report.rows, args.csv_output)
        write_json(
            report.rows,
            databases=databases,
            repetitions=report.repetitions,
            base_seed=report.base_seed,
            output=args.json_output,
        )
        print("===== BACKTEST WALK-FORWARD DELLE FREQUENZE ROLLING =====")
        print()
        print(f"Database:   {len(databases)}")
        print(f"Ruote:      {report.wheel_count}")
        print("Finestre:   " + ", ".join(str(size) for size in report.window_sizes))
        print(f"Repliche:   {report.repetitions}")
        print(f"Seed base:  {report.base_seed}")
        print()
        print(render_table(report.rows))
        print()
        print("Nota: il confronto è descrittivo e non dimostra capacità predittiva.")
        print()
        print(f"CSV:  {args.csv_output}")
        print(f"JSON: {args.json_output}")
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
