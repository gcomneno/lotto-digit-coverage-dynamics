#!/usr/bin/env python3

"""Congela il forecast prequentiale per il prossimo concorso."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from strategies.coverage_completion import (
    current_coverage_state,
)
from strategies.digit_coverage import (
    load_draws_by_wheel,
)
from strategies.prequential_validation import (
    DEFAULT_HORIZONS,
    build_forecast_document,
    default_forecast_path,
    sha256_file,
    utc_now_iso,
    write_forecast_document,
)
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")


def repository_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()


def format_digits(digits: list[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in digits
    ) + "}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Genera un forecast prequentiale immutabile "
            "per il prossimo concorso disponibile."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )

    parser.add_argument(
        "--output",
        type=Path,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        database_path = args.database

        if not database_path.is_file():
            raise FileNotFoundError(
                f"Database non trovato: {database_path}"
            )

        with LottoRepository(database_path) as repository:
            draws_by_wheel = load_draws_by_wheel(repository)

        states = tuple(
            current_coverage_state(draws)
            for draws in draws_by_wheel.values()
        )

        document = build_forecast_document(
            states,
            database_path=database_path,
            database_sha256=sha256_file(database_path),
            repository_commit=repository_commit(),
            generated_at_utc=utc_now_iso(),
            horizons=DEFAULT_HORIZONS,
        )

        target_draw = int(document["target_draw"])
        output_path = (
            args.output
            if args.output is not None
            else default_forecast_path(target_draw)
        )

        forecast_sha256 = write_forecast_document(
            document,
            output_path,
        )

        print("===== FORECAST PREQUENTIALE CONGELATO =====")
        print(f"File:             {output_path}")
        print(
            "Concorso sorgente: "
            f"{document['source_latest_draw']}"
        )
        print(f"Concorso target:   {target_draw}")
        print(
            "Commit modello:    "
            f"{document['repository_commit']}"
        )
        print(
            "Hash database:      "
            f"{document['source_database_sha256']}"
        )
        print(f"Hash forecast:      {forecast_sha256}")
        print()
        print(
            "Ruota       Età  Mancanti       "
            "Entro 1  Entro 2  Entro 3  Entro 5  Attesa"
        )
        print(
            "----------  ---  -------------  "
            "-------  -------  -------  -------  ------"
        )

        for wheel in document["wheels"]:
            completion = wheel[
                "completion_probability_within"
            ]

            print(
                f"{wheel['wheel']:<12}"
                f"{wheel['cycle_age']:<5}"
                f"{format_digits(wheel['missing_digits']):<15}"
                f"{completion['1']:>6.2%}  "
                f"{completion['2']:>6.2%}  "
                f"{completion['3']:>6.2%}  "
                f"{completion['5']:>6.2%}  "
                f"{wheel['expected_remaining_draws']:>6.3f}"
            )

        print()
        print(
            "Il file è immutabile: una seconda generazione "
            "sullo stesso concorso verrà rifiutata."
        )

    except (
        FileExistsError,
        FileNotFoundError,
        RuntimeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
