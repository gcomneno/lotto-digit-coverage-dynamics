#!/usr/bin/env python3

"""Aggiorna in sicurezza uno o più archivi annuali del Lotto."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

from import_lotto import (
    CURRENT_DATABASE_PATH,
    Draw,
    WheelResult,
    archive_completeness,
    archive_source_path,
    archive_url,
    create_schema,
    current_system_year,
    destination_database_path,
    download_archive,
    import_draws,
    parse_archive,
    parse_year,
    validate_archive_year,
    validate_draw,
    verify_database,
)


BACKUP_DIRECTORY = Path("_work/backups")


@dataclass(frozen=True)
class YearUpdateResult:
    year: int
    database_path: Path
    remote_draw_count: int
    completeness: str
    action: str
    outcome: str
    message: str = ""


@dataclass(frozen=True)
class RolloverPlan:
    previous_year: int
    current_database_path: Path
    current_draws: tuple[Draw, ...]


def infer_archive_year(
    draws: Sequence[Draw],
) -> int:
    years = {
        date.fromisoformat(draw.date).year
        for draw in draws
    }

    if len(years) != 1:
        raise ValueError(
            "Il database locale contiene estrazioni "
            "appartenenti a più anni."
        )

    return next(iter(years))


def load_database_draws(
    database_path: Path,
) -> tuple[Draw, ...]:
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
                "Integrità SQLite non valida per "
                f"{database_path}: {integrity}."
            )

        draw_rows = connection.execute(
            """
            SELECT id, draw_number, draw_date
            FROM draws
            ORDER BY draw_date DESC, draw_number DESC
            """
        ).fetchall()

        if not draw_rows:
            raise ValueError(
                f"Il database {database_path} "
                "non contiene estrazioni."
            )

        draws: list[Draw] = []

        for draw_id, draw_number, draw_date in draw_rows:
            rows = connection.execute(
                """
                SELECT
                    w.name,
                    w.sort_order,
                    n.position,
                    n.value
                FROM draw_numbers AS n
                JOIN wheels AS w
                    ON w.id = n.wheel_id
                WHERE n.draw_id = ?
                ORDER BY w.sort_order, n.position
                """,
                (draw_id,),
            ).fetchall()

            grouped: dict[
                tuple[str, int],
                list[int],
            ] = {}

            for (
                wheel_name,
                wheel_order,
                _position,
                value,
            ) in rows:
                grouped.setdefault(
                    (wheel_name, wheel_order),
                    [],
                ).append(value)

            wheels = tuple(
                WheelResult(
                    wheel=wheel_name,
                    numbers=tuple(numbers),
                )
                for (
                    wheel_name,
                    _wheel_order,
                ), numbers in grouped.items()
            )

            draw = Draw(
                number=draw_number,
                date=draw_date,
                wheels=wheels,
            )

            validate_draw(draw)
            draws.append(draw)

    return tuple(draws)


def draw_signature(
    draw: Draw,
) -> tuple[object, ...]:
    return (
        draw.number,
        draw.date,
        tuple(
            (
                result.wheel,
                result.numbers,
            )
            for result in draw.wheels
        ),
    )


def archive_signature(
    draws: Sequence[Draw],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        draw_signature(draw)
        for draw in draws
    )


def read_archive(
    year: int,
    source_directory: Path | None,
) -> tuple[
    Path,
    str,
    bytes,
    tuple[Draw, ...],
]:
    source_url = archive_url(year)

    if source_directory is None:
        source_path = archive_source_path(year)
        html_bytes = download_archive(
            source_url,
            source_path,
        )
    else:
        source_path = (
            source_directory
            / archive_source_path(year).name
        )

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Archivio locale assente: {source_path}"
            )

        html_bytes = source_path.read_bytes()

    draws = tuple(
        parse_archive(
            html_bytes.decode(
                "utf-8",
                errors="replace",
            )
        )
    )

    if not draws:
        raise ValueError(
            f"L'archivio {year} non contiene estrazioni."
        )

    validate_archive_year(
        list(draws),
        expected_year=year,
    )

    return (
        source_path,
        source_url,
        html_bytes,
        draws,
    )


def backup_path_for(
    database_path: Path,
    year: int,
) -> Path:
    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )

    return (
        BACKUP_DIRECTORY
        / (
            f"{database_path.stem}"
            f"-before-{year}"
            f"-{timestamp}"
            f"{database_path.suffix}"
        )
    )


def build_database(
    *,
    year: int,
    database_path: Path,
    source_path: Path,
    source_url: str,
    html_bytes: bytes,
    draws: Sequence[Draw],
) -> None:
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    database_path.unlink(
        missing_ok=True,
    )

    with sqlite3.connect(database_path) as connection:
        create_schema(connection)

        import_draws(
            connection,
            list(draws),
            source_hash=hashlib.sha256(
                html_bytes
            ).hexdigest(),
            source_url=source_url,
            source_path=source_path,
            import_limit=len(draws),
            archive_year=year,
            archive_draws=tuple(draws),
        )

        verify_database(
            connection,
            expected_draws=list(draws),
            archive_draws=tuple(draws),
        )


def _limited_preview(
    values: Sequence[str],
) -> str:
    rendered = ", ".join(values[:10])

    if len(values) > 10:
        return (
            f"{rendered} … "
            f"({len(values)} totali)"
        )

    return rendered


def protected_result(
    *,
    year: int,
    database_path: Path,
    remote_draw_count: int,
    completeness: str,
    message: str,
) -> YearUpdateResult:
    return YearUpdateResult(
        year=year,
        database_path=database_path,
        remote_draw_count=remote_draw_count,
        completeness=completeness,
        action="protetto",
        outcome="WARN",
        message=message,
    )


def local_archive_regression(
    local_draws: Sequence[Draw],
    remote_draws: Sequence[Draw],
) -> str | None:
    local_numbers = {
        draw.number
        for draw in local_draws
    }

    remote_numbers = {
        draw.number
        for draw in remote_draws
    }

    lost_numbers = tuple(
        sorted(
            local_numbers - remote_numbers
        )
    )

    if lost_numbers:
        return (
            "La sorgente non contiene più "
            "estrazioni presenti localmente: "
            f"{_limited_preview(tuple(
                str(number)
                for number in lost_numbers
            ))}."
        )

    local_wheel_results = {
        (
            draw.number,
            result.wheel,
        )
        for draw in local_draws
        for result in draw.wheels
    }

    remote_wheel_results = {
        (
            draw.number,
            result.wheel,
        )
        for draw in remote_draws
        for result in draw.wheels
    }

    lost_wheel_results = tuple(
        sorted(
            local_wheel_results
            - remote_wheel_results
        )
    )

    if lost_wheel_results:
        return (
            "La sorgente non contiene più "
            "risultati di ruota presenti localmente: "
            f"{_limited_preview(tuple(
                f'n. {draw_number}/{wheel}'
                for draw_number, wheel
                in lost_wheel_results
            ))}."
        )

    local_dates = {
        draw.number: draw.date
        for draw in local_draws
    }

    remote_dates = {
        draw.number: draw.date
        for draw in remote_draws
    }

    date_conflicts = tuple(
        sorted(
            draw_number
            for draw_number
            in local_dates.keys()
            & remote_dates.keys()
            if (
                local_dates[draw_number]
                != remote_dates[draw_number]
            )
        )
    )

    if date_conflicts:
        return (
            "La sorgente modifica date di "
            "estrazioni già presenti localmente: "
            f"{_limited_preview(tuple(
                (
                    f'n. {draw_number} '
                    f'({local_dates[draw_number]} → '
                    f'{remote_dates[draw_number]})'
                )
                for draw_number
                in date_conflicts
            ))}."
        )

    local_values = {
        (
            draw.number,
            result.wheel,
        ): result.numbers
        for draw in local_draws
        for result in draw.wheels
    }

    remote_values = {
        (
            draw.number,
            result.wheel,
        ): result.numbers
        for draw in remote_draws
        for result in draw.wheels
    }

    value_conflicts = tuple(
        sorted(
            key
            for key
            in local_values.keys()
            & remote_values.keys()
            if local_values[key] != remote_values[key]
        )
    )

    if value_conflicts:
        return (
            "La sorgente modifica numeri già "
            "presenti localmente: "
            f"{_limited_preview(tuple(
                f'n. {draw_number}/{wheel}'
                for draw_number, wheel
                in value_conflicts
            ))}."
        )

    return None


def update_actions(
    local_draws: Sequence[Draw] | None,
    local_year: int | None,
    requested_year: int,
) -> tuple[str, str]:
    if local_draws is None:
        return (
            "creazione",
            "creato",
        )

    if local_year != requested_year:
        return (
            "rollover",
            "rollover",
        )

    return (
        "aggiornamento",
        "aggiornato",
    )


def verify_database_matches(
    database_path: Path,
    expected_draws: Sequence[Draw],
    error_message: str,
) -> None:
    actual_draws = load_database_draws(
        database_path
    )

    if (
        archive_signature(actual_draws)
        != archive_signature(expected_draws)
    ):
        raise RuntimeError(
            error_message
        )


def replace_database_atomically(
    *,
    year: int,
    database_path: Path,
    source_path: Path,
    source_url: str,
    html_bytes: bytes,
    remote_draws: Sequence[Draw],
) -> Path | None:
    temporary_path = database_path.with_suffix(
        database_path.suffix + ".tmp"
    )

    backup_path: Path | None = None

    try:
        build_database(
            year=year,
            database_path=temporary_path,
            source_path=source_path,
            source_url=source_url,
            html_bytes=html_bytes,
            draws=remote_draws,
        )

        verify_database_matches(
            temporary_path,
            remote_draws,
            (
                "La copia temporanea non corrisponde "
                "all'archivio sorgente."
            ),
        )

        if database_path.is_file():
            BACKUP_DIRECTORY.mkdir(
                parents=True,
                exist_ok=True,
            )

            backup_path = backup_path_for(
                database_path,
                year,
            )

            shutil.copy2(
                database_path,
                backup_path,
            )

        database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path.replace(
            database_path
        )

        try:
            verify_database_matches(
                database_path,
                remote_draws,
                (
                    "La verifica finale del database "
                    "non corrisponde alla sorgente."
                ),
            )
        except Exception:
            if backup_path is not None:
                shutil.copy2(
                    backup_path,
                    database_path,
                )
            else:
                database_path.unlink(
                    missing_ok=True,
                )

            raise

    except Exception:
        temporary_path.unlink(
            missing_ok=True,
        )
        raise

    return backup_path


def update_database_year(
    year: int,
    *,
    dry_run: bool = False,
    source_directory: Path | None = None,
    destination_path: Path | None = None,
) -> YearUpdateResult:
    current_year = current_system_year()

    if year < 1871:
        raise ValueError(
            "L'anno deve essere maggiore o uguale a 1871."
        )

    if year > current_year:
        raise ValueError(
            f"L'anno {year} è successivo al {current_year}."
        )

    database_path = (
        destination_database_path(year)
        if destination_path is None
        else destination_path
    )

    (
        source_path,
        source_url,
        html_bytes,
        remote_draws,
    ) = read_archive(
        year,
        source_directory,
    )

    completeness = archive_completeness(
        list(remote_draws)
    )

    local_draws: tuple[Draw, ...] | None = None
    local_year: int | None = None

    if database_path.is_file():
        local_draws = load_database_draws(
            database_path
        )
        local_year = infer_archive_year(
            local_draws
        )

    if (
        local_draws is not None
        and local_year != year
        and database_path.name
        != CURRENT_DATABASE_PATH.name
    ):
        raise ValueError(
            f"Il database destinazione {database_path} "
            f"appartiene all'anno {local_year}, "
            f"non all'anno richiesto {year}. "
            "Il cambio d'anno è consentito soltanto "
            f"per {CURRENT_DATABASE_PATH.name}."
        )

    if (
        local_draws is not None
        and local_year == year
        and archive_signature(local_draws)
        == archive_signature(remote_draws)
    ):
        return YearUpdateResult(
            year=year,
            database_path=database_path,
            remote_draw_count=len(remote_draws),
            completeness=completeness,
            action="invariato",
            outcome="OK",
        )

    if (
        local_draws is not None
        and local_year == year
    ):
        regression = local_archive_regression(
            local_draws,
            remote_draws,
        )

        if regression is not None:
            return protected_result(
                year=year,
                database_path=database_path,
                remote_draw_count=len(remote_draws),
                completeness=completeness,
                message=regression,
            )

    (
        planned_action,
        completed_action,
    ) = update_actions(
        local_draws,
        local_year,
        year,
    )

    if dry_run:
        return YearUpdateResult(
            year=year,
            database_path=database_path,
            remote_draw_count=len(remote_draws),
            completeness=completeness,
            action=f"dry-run:{planned_action}",
            outcome="OK",
        )

    backup_path = replace_database_atomically(
        year=year,
        database_path=database_path,
        source_path=source_path,
        source_url=source_url,
        html_bytes=html_bytes,
        remote_draws=remote_draws,
    )

    message = (
        ""
        if backup_path is None
        else f"Backup: {backup_path}"
    )

    return YearUpdateResult(
        year=year,
        database_path=database_path,
        remote_draw_count=len(remote_draws),
        completeness=completeness,
        action=completed_action,
        outcome="OK",
        message=message,
    )


def detect_rollover(
    requested_years: Sequence[int],
    *,
    current_database_path: Path = CURRENT_DATABASE_PATH,
    system_year: int | None = None,
) -> RolloverPlan | None:
    effective_year = (
        current_system_year()
        if system_year is None
        else system_year
    )

    if effective_year not in requested_years:
        return None

    if not current_database_path.is_file():
        return None

    current_draws = load_database_draws(
        current_database_path
    )

    database_year = infer_archive_year(
        current_draws
    )

    if database_year == effective_year:
        return None

    if database_year > effective_year:
        raise ValueError(
            "Il database corrente appartiene a un "
            f"anno futuro: {database_year}."
        )

    return RolloverPlan(
        previous_year=database_year,
        current_database_path=current_database_path,
        current_draws=current_draws,
    )


def validate_rollover_source(
    current_draws: Sequence[Draw],
    remote_draws: Sequence[Draw],
) -> None:
    current_by_number = {
        draw.number: draw
        for draw in current_draws
    }

    remote_by_number = {
        draw.number: draw
        for draw in remote_draws
    }

    missing_draws = tuple(
        sorted(
            current_by_number.keys()
            - remote_by_number.keys()
        )
    )

    if missing_draws:
        preview = ", ".join(
            str(number)
            for number in missing_draws[:10]
        )

        suffix = (
            f" … ({len(missing_draws)} totali)"
            if len(missing_draws) > 10
            else ""
        )

        raise ValueError(
            "L'archivio definitivo non conserva "
            "estrazioni del database corrente: "
            f"{preview}{suffix}."
        )

    for draw_number, current_draw in (
        current_by_number.items()
    ):
        remote_draw = remote_by_number[
            draw_number
        ]

        if current_draw.date != remote_draw.date:
            raise ValueError(
                "L'archivio definitivo modifica la data "
                f"del concorso n. {draw_number}: "
                f"{current_draw.date} → "
                f"{remote_draw.date}."
            )

        current_wheels = {
            result.wheel: result.numbers
            for result in current_draw.wheels
        }

        remote_wheels = {
            result.wheel: result.numbers
            for result in remote_draw.wheels
        }

        missing_wheels = tuple(
            sorted(
                current_wheels.keys()
                - remote_wheels.keys()
            )
        )

        if missing_wheels:
            raise ValueError(
                "L'archivio definitivo non conserva "
                "risultati di ruota del concorso "
                f"n. {draw_number}: "
                f"{', '.join(missing_wheels)}."
            )

        for wheel, current_numbers in (
            current_wheels.items()
        ):
            remote_numbers = remote_wheels[
                wheel
            ]

            if current_numbers != remote_numbers:
                raise ValueError(
                    "L'archivio definitivo modifica "
                    "i numeri del concorso "
                    f"n. {draw_number}/{wheel}."
                )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scarica, verifica e aggiorna uno o più "
            "database annuali del Lotto."
        )
    )

    parser.add_argument(
        "--year",
        type=parse_year,
        metavar="YYYY",
        help="Aggiorna un singolo anno.",
    )

    parser.add_argument(
        "--from-year",
        type=parse_year,
        metavar="YYYY",
        help="Primo anno dell'intervallo inclusivo.",
    )

    parser.add_argument(
        "--to-year",
        type=parse_year,
        metavar="YYYY",
        help="Ultimo anno dell'intervallo inclusivo.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Scarica e confronta senza modificare "
            "i database."
        ),
    )

    parser.add_argument(
        "--keep-going",
        action="store_true",
        help=(
            "Continua con gli anni successivi "
            "anche dopo un errore."
        ),
    )

    parser.add_argument(
        "--source-directory",
        type=Path,
        help=(
            "Usa archive-YYYY.html da questa directory "
            "senza effettuare download."
        ),
    )

    return parser


def resolve_years(
    arguments: argparse.Namespace,
) -> tuple[int, ...]:
    has_from = arguments.from_year is not None
    has_to = arguments.to_year is not None

    if (
        arguments.year is not None
        and (has_from or has_to)
    ):
        raise ValueError(
            "--year non è compatibile con "
            "--from-year o --to-year."
        )

    if has_from != has_to:
        raise ValueError(
            "--from-year e --to-year devono "
            "essere specificati insieme."
        )

    if arguments.year is not None:
        return (arguments.year,)

    if has_from and has_to:
        if arguments.from_year > arguments.to_year:
            raise ValueError(
                "--from-year non può essere "
                "successivo a --to-year."
            )

        return tuple(
            range(
                arguments.from_year,
                arguments.to_year + 1,
            )
        )

    return (current_system_year(),)


def print_summary(
    results: Sequence[YearUpdateResult],
) -> None:
    print()
    print("===== RIEPILOGO DATABASE =====")
    print(
        "Anno  Destinazione                         "
        "Remoto  Archivio  Azione               Esito"
    )
    print(
        "----  ----------------------------------- "
        "------  --------  -------------------  -----"
    )

    for result in results:
        print(
            f"{result.year:<4}  "
            f"{str(result.database_path):<35} "
            f"{result.remote_draw_count:>6}  "
            f"{result.completeness:<8}  "
            f"{result.action:<19}  "
            f"{result.outcome}"
        )

    messages = [
        result
        for result in results
        if result.message
    ]

    if messages:
        print()
        print("Dettagli:")

        for result in messages:
            print(
                f"- {result.year}: {result.message}"
            )


def failed_result(
    *,
    year: int,
    database_path: Path,
    action: str,
    error: object,
) -> YearUpdateResult:
    return YearUpdateResult(
        year=year,
        database_path=database_path,
        remote_draw_count=0,
        completeness="-",
        action=action,
        outcome="FAILED",
        message=str(error),
    )


def prepare_rollover_source(
    rollover: RolloverPlan | None,
    source_directory: Path | None,
) -> Path | None:
    if rollover is None:
        return None

    (
        source_path,
        _source_url,
        _html_bytes,
        remote_draws,
    ) = read_archive(
        rollover.previous_year,
        source_directory,
    )

    validate_rollover_source(
        rollover.current_draws,
        remote_draws,
    )

    return source_path.parent


def years_with_rollover(
    requested_years: tuple[int, ...],
    rollover: RolloverPlan | None,
) -> tuple[int, ...]:
    if (
        rollover is None
        or rollover.previous_year
        in requested_years
    ):
        return requested_years

    return (
        rollover.previous_year,
        *requested_years,
    )


def source_directory_for_year(
    *,
    year: int,
    default_source_directory: Path | None,
    rollover: RolloverPlan | None,
    rollover_source_directory: Path | None,
) -> Path | None:
    if (
        rollover is not None
        and year == rollover.previous_year
    ):
        return rollover_source_directory

    return default_source_directory


def blocked_rollover_result(
    message: str,
) -> YearUpdateResult:
    return failed_result(
        year=current_system_year(),
        database_path=CURRENT_DATABASE_PATH,
        action="rollover-bloccato",
        error=message,
    )


def run_year_updates(
    years: Sequence[int],
    *,
    dry_run: bool,
    keep_going: bool,
    source_directory: Path | None,
    rollover: RolloverPlan | None,
    rollover_source_directory: Path | None,
) -> list[YearUpdateResult]:
    results: list[YearUpdateResult] = []

    for year in years:
        print()
        print(f"===== ANNO {year} =====")

        annual_source_directory = (
            source_directory_for_year(
                year=year,
                default_source_directory=(
                    source_directory
                ),
                rollover=rollover,
                rollover_source_directory=(
                    rollover_source_directory
                ),
            )
        )

        try:
            result = update_database_year(
                year,
                dry_run=dry_run,
                source_directory=(
                    annual_source_directory
                ),
            )
        except (
            FileNotFoundError,
            OSError,
            RuntimeError,
            shutil.Error,
            sqlite3.Error,
            ValueError,
        ) as error:
            results.append(
                failed_result(
                    year=year,
                    database_path=(
                        destination_database_path(
                            year
                        )
                    ),
                    action="errore",
                    error=error,
                )
            )

            rollover_dependency_failed = (
                rollover is not None
                and year == rollover.previous_year
            )

            if (
                rollover_dependency_failed
                or not keep_going
            ):
                break

            continue

        results.append(result)

        rollover_dependency_warned = (
            rollover is not None
            and year == rollover.previous_year
            and result.outcome != "OK"
        )

        if rollover_dependency_warned:
            results.append(
                blocked_rollover_result(
                    (
                        "L'anno concluso non è stato "
                        "finalizzato in sicurezza: "
                        f"{result.message or result.action}"
                    )
                )
            )
            break

    return results


def results_exit_code(
    results: Sequence[YearUpdateResult],
) -> int:
    return (
        1
        if any(
            result.outcome == "FAILED"
            for result in results
        )
        else 0
    )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        requested_years = resolve_years(
            arguments
        )
    except ValueError as error:
        parser.error(str(error))

    try:
        rollover = detect_rollover(
            requested_years
        )
    except (
        FileNotFoundError,
        OSError,
        sqlite3.Error,
        ValueError,
    ) as error:
        results = [
            blocked_rollover_result(
                str(error)
            )
        ]

        print_summary(results)
        return 1

    try:
        rollover_source_directory = (
            prepare_rollover_source(
                rollover,
                arguments.source_directory,
            )
        )
    except (
        FileNotFoundError,
        OSError,
        sqlite3.Error,
        ValueError,
    ) as error:
        assert rollover is not None

        results = [
            failed_result(
                year=rollover.previous_year,
                database_path=(
                    destination_database_path(
                        rollover.previous_year
                    )
                ),
                action="rollover-bloccato",
                error=error,
            )
        ]

        print_summary(results)
        return 1

    years = years_with_rollover(
        requested_years,
        rollover,
    )

    results = run_year_updates(
        years,
        dry_run=arguments.dry_run,
        keep_going=arguments.keep_going,
        source_directory=(
            arguments.source_directory
        ),
        rollover=rollover,
        rollover_source_directory=(
            rollover_source_directory
        ),
    )

    print_summary(results)

    return results_exit_code(
        results
    )


if __name__ == "__main__":
    raise SystemExit(main())
