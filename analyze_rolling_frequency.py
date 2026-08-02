#!/usr/bin/env python3

"""Backtest walk-forward delle frequenze rolling delle cifre."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass, fields
from math import comb
from pathlib import Path
from typing import Mapping, Sequence

from strategies.digit_coverage import (
    load_draws_by_wheel,
)
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
)
from strategies.rolling_frequency import (
    WalkForwardObservation,
    build_walk_forward_experiment,
    merge_draw_histories,
    simulate_equal_size_random_baseline,
    summarize_walk_forward_observations,
)


DEFAULT_DATABASES = (
    Path("data/lotto-2023.sqlite3"),
    Path("data/lotto-2024.sqlite3"),
    Path("data/lotto-2025.sqlite3"),
    Path("data/lotto-current.sqlite3"),
)

DEFAULT_WINDOW_SIZES = (
    3,
    6,
    8,
    12,
)

DEFAULT_PERIODS = (
    (
        "development",
        "2023-01-01",
        "2025-12-31",
    ),
    (
        "held-out",
        "2026-01-01",
        "2026-12-31",
    ),
)

DEFAULT_REPETITIONS = 1_000
DEFAULT_SEED = 20_260_731

DEFAULT_CSV_OUTPUT = Path(
    "_work/rolling-frequency-backtest.csv"
)

DEFAULT_JSON_OUTPUT = Path(
    "_work/rolling-frequency-backtest.json"
)


@dataclass(frozen=True)
class RollingFrequencyResultRow:
    window_size: int
    period: str
    start_date: str
    end_date: str
    repetitions: int
    seed: int
    observation_count: int
    candidate_number_count: int
    covered_ambo_count: int
    observed_hit_number_count: int
    theoretical_hit_number_count: float
    random_mean_hit_number_count: float
    observed_to_random_number_ratio: float
    empirical_p_value_hit_number: float
    observed_hit_ambo_count: int
    theoretical_hit_ambo_count: float
    random_mean_hit_ambo_count: float
    observed_to_random_ambo_ratio: float
    empirical_p_value_hit_ambo: float


def safe_ratio(
    numerator: float,
    denominator: float,
) -> float:
    if denominator == 0.0:
        return 0.0

    return numerator / denominator


def load_merged_draws(
    databases: Sequence[Path],
) -> dict[str, tuple[DrawSnapshot, ...]]:
    if not databases:
        raise ValueError(
            "Serve almeno un database."
        )

    archives = []

    for database in databases:
        with LottoRepository(database) as repository:
            archives.append(
                load_draws_by_wheel(repository)
            )

    return merge_draw_histories(
        tuple(archives)
    )


def build_result_rows(
    experiment: Mapping[
        int,
        Sequence[WalkForwardObservation],
    ],
    *,
    window_sizes: Sequence[int],
    periods: Sequence[
        tuple[str, str, str]
    ],
    repetitions: int,
    base_seed: int,
) -> tuple[RollingFrequencyResultRow, ...]:
    rows: list[RollingFrequencyResultRow] = []

    for window_size in window_sizes:
        if window_size not in experiment:
            raise ValueError(
                "Esperimento mancante per la finestra "
                f"{window_size}."
            )

        observations = experiment[window_size]

        for period_index, (
            period,
            start_date,
            end_date,
        ) in enumerate(periods):
            seed = (
                base_seed
                + window_size * 100
                + period_index
            )

            summary = (
                summarize_walk_forward_observations(
                    observations,
                    window_size=window_size,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            baseline = (
                simulate_equal_size_random_baseline(
                    observations,
                    window_size=window_size,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    repetitions=repetitions,
                    seed=seed,
                )
            )

            theoretical_hit_number_count = (
                summary.candidate_number_count
                * 5
                / 90
            )

            theoretical_hit_ambo_count = (
                summary.covered_ambo_count
                * comb(5, 2)
                / comb(90, 2)
            )

            rows.append(
                RollingFrequencyResultRow(
                    window_size=window_size,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    repetitions=repetitions,
                    seed=seed,
                    observation_count=(
                        summary.observation_count
                    ),
                    candidate_number_count=(
                        summary.candidate_number_count
                    ),
                    covered_ambo_count=(
                        summary.covered_ambo_count
                    ),
                    observed_hit_number_count=(
                        summary.hit_number_count
                    ),
                    theoretical_hit_number_count=(
                        theoretical_hit_number_count
                    ),
                    random_mean_hit_number_count=(
                        baseline.mean_hit_number_count
                    ),
                    observed_to_random_number_ratio=(
                        safe_ratio(
                            summary.hit_number_count,
                            baseline.mean_hit_number_count,
                        )
                    ),
                    empirical_p_value_hit_number=(
                        baseline
                        .empirical_p_value_hit_number
                    ),
                    observed_hit_ambo_count=(
                        summary.hit_ambo_count
                    ),
                    theoretical_hit_ambo_count=(
                        theoretical_hit_ambo_count
                    ),
                    random_mean_hit_ambo_count=(
                        baseline.mean_hit_ambo_count
                    ),
                    observed_to_random_ambo_ratio=(
                        safe_ratio(
                            summary.hit_ambo_count,
                            baseline.mean_hit_ambo_count,
                        )
                    ),
                    empirical_p_value_hit_ambo=(
                        baseline.empirical_p_value_hit_ambo
                    ),
                )
            )

    return tuple(rows)


def write_csv(
    rows: Sequence[RollingFrequencyResultRow],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = tuple(
        field.name
        for field in fields(
            RollingFrequencyResultRow
        )
    )

    with output.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            lineterminator="\n",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                asdict(row)
            )


def write_json(
    rows: Sequence[RollingFrequencyResultRow],
    *,
    databases: Sequence[Path],
    repetitions: int,
    base_seed: int,
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = {
        "database_paths": [
            str(database)
            for database in databases
        ],
        "row_count": len(rows),
        "window_sizes": sorted(
            {
                row.window_size
                for row in rows
            }
        ),
        "periods": [],
        "repetitions": repetitions,
        "base_seed": base_seed,
        "rows": [
            asdict(row)
            for row in rows
        ],
    }

    unique_periods: list[dict[str, str]] = []

    for row in rows:
        period = {
            "name": row.period,
            "start_date": row.start_date,
            "end_date": row.end_date,
        }

        if period not in unique_periods:
            unique_periods.append(period)

    document["periods"] = unique_periods

    output.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def render_table(
    rows: Sequence[RollingFrequencyResultRow],
) -> str:
    lines = [
        (
            "N   Periodo       Obs.   Cand.  "
            "Hit n.  Cas. n.  Rap. n.  p num.   "
            "Hit ambi  Cas. ambi  Rap. a.  p ambo"
        ),
        (
            "--  ------------  -----  -----  "
            "------  -------  -------  -------  "
            "--------  ---------  -------  -------"
        ),
    ]

    for row in rows:
        lines.append(
            f"{row.window_size:<3} "
            f"{row.period:<12} "
            f"{row.observation_count:>5} "
            f"{row.candidate_number_count:>6} "
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
            "Esegue il backtest walk-forward delle cifre "
            "più frequenti su finestre rolling e lo "
            "confronta con rose casuali della stessa "
            "dimensione."
        )
    )

    parser.add_argument(
        "--database",
        action="append",
        type=Path,
        dest="databases",
        help=(
            "Database SQLite. Ripetere l'opzione "
            "per più archivi."
        ),
    )

    parser.add_argument(
        "--window-size",
        action="append",
        type=int,
        dest="window_sizes",
        help=(
            "Ampiezza della finestra rolling. "
            "Ripetere per più finestre."
        ),
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_REPETITIONS,
        help=(
            "Numero di repliche casuali per ogni "
            "finestra e periodo."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed base deterministico.",
    )

    parser.add_argument(
        "--csv-output",
        type=Path,
        default=DEFAULT_CSV_OUTPUT,
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    databases = tuple(
        args.databases
        if args.databases
        else DEFAULT_DATABASES
    )

    window_sizes = tuple(
        args.window_sizes
        if args.window_sizes
        else DEFAULT_WINDOW_SIZES
    )

    try:
        draws_by_wheel = load_merged_draws(
            databases
        )

        experiment = build_walk_forward_experiment(
            draws_by_wheel,
            window_sizes=window_sizes,
        )

        rows = build_result_rows(
            experiment,
            window_sizes=tuple(
                sorted(set(window_sizes))
            ),
            periods=DEFAULT_PERIODS,
            repetitions=args.repetitions,
            base_seed=args.seed,
        )

        write_csv(
            rows,
            args.csv_output,
        )

        write_json(
            rows,
            databases=databases,
            repetitions=args.repetitions,
            base_seed=args.seed,
            output=args.json_output,
        )

        print(
            "===== BACKTEST WALK-FORWARD "
            "DELLE FREQUENZE ROLLING ====="
        )
        print()
        print(
            f"Database:   {len(databases)}"
        )
        print(
            f"Ruote:      {len(draws_by_wheel)}"
        )
        print(
            "Finestre:   "
            + ", ".join(
                str(window_size)
                for window_size
                in sorted(set(window_sizes))
            )
        )
        print(
            f"Repliche:   {args.repetitions}"
        )
        print(
            f"Seed base:  {args.seed}"
        )
        print()
        print(render_table(rows))
        print()
        print(
            "Nota: il confronto è descrittivo e "
            "non dimostra capacità predittiva."
        )
        print()
        print(
            f"CSV:  {args.csv_output}"
        )
        print(
            f"JSON: {args.json_output}"
        )

    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
