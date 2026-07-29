#!/usr/bin/env python3

"""Aggiorna in sicurezza il database annuale completo del Lotto."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

from import_lotto import (
    Draw,
    archive_database_path,
    archive_source_path,
    archive_url,
    current_system_year,
    download_archive,
    parse_archive,
    parse_year,
    validate_archive_year,
)


BACKUP_DIRECTORY = Path("_work/backups")


@dataclass(frozen=True)
class DatabaseRange:
    count: int
    first_draw: int
    last_draw: int
    latest_date: str


def read_database_range(
    database_path: Path,
) -> DatabaseRange:
    if not database_path.is_file():
        raise FileNotFoundError(
            f"Database assente: {database_path}"
        )

    with sqlite3.connect(database_path) as connection:
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise ValueError(
                "Integrità SQLite non valida: "
                f"{integrity}."
            )

        count, first_draw, last_draw = connection.execute(
            """
            SELECT
                COUNT(*),
                MIN(draw_number),
                MAX(draw_number)
            FROM draws
            """
        ).fetchone()

        if (
            count == 0
            or first_draw is None
            or last_draw is None
        ):
            raise ValueError(
                "Il database non contiene estrazioni."
            )

        draw_numbers = tuple(
            row[0]
            for row in connection.execute(
                """
                SELECT draw_number
                FROM draws
                ORDER BY draw_number
                """
            )
        )

        expected_numbers = tuple(
            range(
                first_draw,
                last_draw + 1,
            )
        )

        if draw_numbers != expected_numbers:
            raise ValueError(
                "Le estrazioni nel database non formano "
                f"l'intervallo continuo "
                f"{first_draw}–{last_draw}."
            )

        latest_date = connection.execute(
            """
            SELECT draw_date
            FROM draws
            WHERE draw_number = ?
            """,
            (last_draw,),
        ).fetchone()[0]

    return DatabaseRange(
        count=count,
        first_draw=first_draw,
        last_draw=last_draw,
        latest_date=latest_date,
    )


def validate_complete_archive(
    draws: Sequence[Draw],
) -> tuple[Draw, ...]:
    if not draws:
        raise ValueError(
            "L'archivio scaricato non contiene estrazioni."
        )

    selected = tuple(draws)
    latest_draw = selected[0].number

    selected_numbers = tuple(
        draw.number
        for draw in selected
    )

    expected_numbers = tuple(
        range(
            latest_draw,
            0,
            -1,
        )
    )

    if selected_numbers != expected_numbers:
        raise ValueError(
            "L'archivio annuale non contiene la "
            f"sequenza completa 1–{latest_draw}."
        )

    return selected


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aggiorna il database annuale completo "
            "del Lotto dall'estrazione 1 "
            "all'ultima disponibile."
        )
    )

    parser.add_argument(
        "--year",
        type=parse_year,
        default=current_system_year(),
        metavar="YYYY",
        help=(
            "Anno da aggiornare "
            "(default: anno corrente)."
        ),
    )

    parser.add_argument(
        "--database",
        type=Path,
        help=(
            "Database destinazione. "
            "Se omesso usa data/lotto-YYYY.sqlite3."
        ),
    )

    parser.add_argument(
        "--source-url",
        help="URL alternativo dell'archivio annuale.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    year: int = args.year

    database_path = (
        args.database
        if args.database is not None
        else archive_database_path(year)
    )

    source_path = archive_source_path(year)

    source_url = (
        args.source_url
        if args.source_url is not None
        else archive_url(year)
    )

    temporary_path = database_path.with_suffix(
        database_path.suffix + ".tmp"
    )

    try:
        current = read_database_range(
            database_path
        )

        print("===== DATABASE CORRENTE =====")
        print(f"Database:            {database_path}")
        print(f"Estrazioni:          {current.count}")
        print(
            "Intervallo:          "
            f"{current.first_draw}–{current.last_draw}"
        )
        print(
            "Ultima estrazione:   "
            f"{current.last_draw} "
            f"del {current.latest_date}"
        )

        print()
        print("===== DOWNLOAD ARCHIVIO =====")
        print(f"Anno:                {year}")
        print(f"URL:                 {source_url}")
        print(f"Destinazione:        {source_path}")

        html_bytes = download_archive(
            source_url,
            source_path,
        )

        print(
            f"Byte scaricati:      {len(html_bytes)}"
        )

        all_draws = parse_archive(
            html_bytes.decode(
                "utf-8",
                errors="replace",
            )
        )

        validate_archive_year(
            all_draws,
            expected_year=year,
        )

        complete_draws = validate_complete_archive(
            all_draws
        )

        latest = complete_draws[0]
        expected_count = len(complete_draws)

        print()
        print("===== ARCHIVIO REMOTO =====")
        print(
            f"Estrazioni rilevate: {expected_count}"
        )
        print(
            "Intervallo completo: "
            f"1–{latest.number}"
        )
        print(
            "Ultima estrazione:   "
            f"{latest.number} del {latest.date}"
        )

        if latest.number < current.last_draw:
            raise ValueError(
                "L'archivio remoto è meno aggiornato "
                "del database locale."
            )

        database_is_complete = (
            current.first_draw == 1
            and current.last_draw == latest.number
            and current.latest_date == latest.date
            and current.count == expected_count
        )

        if database_is_complete:
            print()
            print(
                "Database annuale già completo e "
                "aggiornato: nessuna modifica necessaria."
            )
            return 0

        timestamp = datetime.now().strftime(
            "%Y%m%d-%H%M%S-%f"
        )

        BACKUP_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        backup_path = (
            BACKUP_DIRECTORY
            / (
                f"{database_path.stem}"
                f"-before-{latest.number}"
                f"-{timestamp}"
                f"{database_path.suffix}"
            )
        )

        print()
        print("===== PREPARAZIONE AGGIORNAMENTO =====")
        print(
            "Intervallo destinazione: "
            f"1–{latest.number}"
        )
        print(
            f"Estrazioni attese:    {expected_count}"
        )
        print(f"Backup:              {backup_path}")

        shutil.copy2(
            database_path,
            backup_path,
        )

        temporary_path.unlink(
            missing_ok=True
        )

        shutil.copy2(
            database_path,
            temporary_path,
        )

        importer_path = Path(__file__).with_name(
            "import_lotto.py"
        )

        command = (
            sys.executable,
            str(importer_path),
            "--year",
            str(year),
            "--source",
            str(source_path),
            "--database",
            str(temporary_path),
            "--limit",
            "all",
        )

        print()
        print("===== IMPORTAZIONE TEMPORANEA =====")
        print("Comando:")
        print(" ".join(command))
        print()

        completed = subprocess.run(
            command,
            check=False,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                "L'importatore ha terminato con "
                f"exit code {completed.returncode}."
            )

        updated = read_database_range(
            temporary_path
        )

        if (
            updated.first_draw != 1
            or updated.last_draw != latest.number
            or updated.latest_date != latest.date
            or updated.count != expected_count
        ):
            raise RuntimeError(
                "La verifica della copia aggiornata "
                "non corrisponde all'archivio annuale "
                "completo."
            )

        temporary_path.replace(
            database_path
        )

        final = read_database_range(
            database_path
        )

        print()
        print("===== AGGIORNAMENTO COMPLETATO =====")
        print(f"Database:            {database_path}")
        print(f"Estrazioni:          {final.count}")
        print(
            "Intervallo:          "
            f"{final.first_draw}–{final.last_draw}"
        )
        print(
            "Ultima estrazione:   "
            f"{final.last_draw} "
            f"del {final.latest_date}"
        )
        print(f"Backup conservato:   {backup_path}")

    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        shutil.Error,
        sqlite3.Error,
        ValueError,
    ) as error:
        temporary_path.unlink(
            missing_ok=True
        )

        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
