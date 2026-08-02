#!/usr/bin/env python3

"""Genera e verifica un intervallo di database storici del Lotto."""

from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FROM_YEAR = 1871


@dataclass(frozen=True)
class VerificationSummary:
    expected_count: int
    present_count: int
    integral_count: int
    missing_years: tuple[int, ...]
    invalid_years: tuple[int, ...]
    total_bytes: int


def previous_system_year() -> int:
    return date.today().year - 1


def parse_year(value: str) -> int:
    try:
        year = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"Anno non valido: {value!r}."
        ) from error

    if year < DEFAULT_FROM_YEAR:
        raise argparse.ArgumentTypeError(
            "L'anno deve essere maggiore o uguale "
            f"a {DEFAULT_FROM_YEAR}."
        )

    return year


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Genera e verifica i database storici annuali "
            "del Lotto tramite './lotto.py db update'."
        )
    )

    parser.add_argument(
        "--from-year",
        type=parse_year,
        default=DEFAULT_FROM_YEAR,
        metavar="YYYY",
        help=(
            "Primo anno inclusivo "
            f"(predefinito: {DEFAULT_FROM_YEAR})."
        ),
    )

    parser.add_argument(
        "--to-year",
        type=parse_year,
        default=previous_system_year(),
        metavar="YYYY",
        help=(
            "Ultimo anno inclusivo "
            "(predefinito: anno precedente)."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Scarica e confronta gli archivi senza "
            "creare o modificare database."
        ),
    )

    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help=(
            "Interrompe al primo errore; per impostazione "
            "predefinita continua con gli anni successivi."
        ),
    )

    parser.add_argument(
        "--source-directory",
        type=Path,
        help=(
            "Usa archive-YYYY.html da una directory locale "
            "senza effettuare download."
        ),
    )

    return parser


def resolve_years(
    from_year: int,
    to_year: int,
) -> tuple[int, ...]:
    if from_year > to_year:
        raise ValueError(
            "L'anno iniziale deve essere precedente "
            "o uguale all'anno finale."
        )

    return tuple(
        range(
            from_year,
            to_year + 1,
        )
    )


def database_path_for(
    year: int,
) -> Path:
    return (
        REPOSITORY_ROOT
        / "data"
        / f"lotto-{year}.sqlite3"
    )


def sqlite_is_integral(
    database_path: Path,
) -> bool:
    try:
        with sqlite3.connect(
            f"file:{database_path}?mode=ro",
            uri=True,
        ) as connection:
            result = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()
    except sqlite3.Error:
        return False

    return (
        result is not None
        and result[0] == "ok"
    )


def verify_databases(
    years: Sequence[int],
) -> VerificationSummary:
    missing_years: list[int] = []
    invalid_years: list[int] = []
    total_bytes = 0
    present_count = 0
    integral_count = 0

    for year in years:
        database_path = database_path_for(year)

        if not database_path.is_file():
            missing_years.append(year)
            continue

        present_count += 1
        total_bytes += database_path.stat().st_size

        if sqlite_is_integral(database_path):
            integral_count += 1
        else:
            invalid_years.append(year)

    return VerificationSummary(
        expected_count=len(years),
        present_count=present_count,
        integral_count=integral_count,
        missing_years=tuple(missing_years),
        invalid_years=tuple(invalid_years),
        total_bytes=total_bytes,
    )


def format_size(size: int) -> str:
    units = (
        "B",
        "KiB",
        "MiB",
        "GiB",
    )

    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"

        value /= 1024

    raise AssertionError("Unità dimensionale non raggiungibile.")


def build_update_command(
    arguments: argparse.Namespace,
) -> list[str]:
    command = [
        str(REPOSITORY_ROOT / "lotto.py"),
        "db",
        "update",
        "--from-year",
        str(arguments.from_year),
        "--to-year",
        str(arguments.to_year),
    ]

    if not arguments.fail_fast:
        command.append("--keep-going")

    if arguments.dry_run:
        command.append("--dry-run")

    if arguments.source_directory is not None:
        command.extend(
            [
                "--source-directory",
                str(arguments.source_directory),
            ]
        )

    return command


def print_verification(
    summary: VerificationSummary,
) -> None:
    print()
    print("===== VERIFICA ARCHIVIO STORICO =====")
    print(
        "Database presenti: "
        f"{summary.present_count}/"
        f"{summary.expected_count}"
    )
    print(
        "Database integri: "
        f"{summary.integral_count}/"
        f"{summary.expected_count}"
    )
    print(
        "Spazio occupato: "
        f"{format_size(summary.total_bytes)}"
    )

    if summary.missing_years:
        print(
            "Anni mancanti: "
            + ", ".join(
                str(year)
                for year in summary.missing_years
            )
        )
    else:
        print("Anni mancanti: nessuno")

    if summary.invalid_years:
        print(
            "Integrità non valida: "
            + ", ".join(
                str(year)
                for year in summary.invalid_years
            )
        )
    else:
        print("Integrità non valida: nessuna")


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        years = resolve_years(
            arguments.from_year,
            arguments.to_year,
        )
    except ValueError as error:
        parser.error(str(error))

    command = build_update_command(arguments)

    print("===== GENERAZIONE ARCHIVIO STORICO =====")
    print(
        f"Intervallo: {years[0]}–{years[-1]} "
        f"({len(years)} anni)"
    )
    print(
        "Modalità: "
        + (
            "dry-run"
            if arguments.dry_run
            else "scrittura e verifica"
        )
    )
    print("Comando:")
    print("  " + " ".join(command))
    print()

    started = time.monotonic()

    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=False,
    )

    elapsed = time.monotonic() - started

    print()
    print("===== DURATA =====")
    print(f"{elapsed:.1f} secondi")

    if arguments.dry_run:
        return completed.returncode

    summary = verify_databases(years)
    print_verification(summary)

    verification_failed = (
        bool(summary.missing_years)
        or bool(summary.invalid_years)
    )

    if completed.returncode != 0:
        return completed.returncode

    return 1 if verification_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
