from __future__ import annotations

import argparse
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from update_lotto_databases import (
    RolloverPlan,
    YearUpdateResult,
    detect_rollover,
    load_database_draws,
    main,
    resolve_years,
    update_database_year,
    validate_rollover_source,
)


WHEELS = (
    "Firenze",
    "Milano",
)


def archive_html(
    year: int,
    draw_numbers: tuple[int, ...],
    wheels: tuple[str, ...] = WHEELS,
    number_offset: int = 0,
    date_offset_days: int = 0,
) -> str:
    blocks: list[str] = []

    for number in sorted(
        draw_numbers,
        reverse=True,
    ):
        draw_date = (
            date(year, 1, 1)
            + timedelta(
                days=(
                    number
                    - 1
                    + date_offset_days
                )
            )
        )

        rows: list[str] = []

        for wheel_index, wheel in enumerate(
            wheels,
            start=1,
        ):
            values = tuple(
                (
                    wheel_index * 10
                    + offset
                    + number_offset
                )
                for offset in range(1, 6)
            )

            rows.append(
                '<ul class="ballRow">'
                f'<li class="wheelTitle h4">{wheel}</li>'
                + "".join(
                    f'<li class="ball">{value}</li>'
                    for value in values
                )
                + "</ul>"
            )

        blocks.append(
            '<div class="lottoDraws">'
            '<p class="lottoBG">'
            f"<strong>del {draw_date:%d/%m/%Y}</strong>"
            f"<span>Estrazione n. {number}</span>"
            "</p>"
            + "".join(rows)
            + "</div>"
        )

    return "<html><body>" + "".join(blocks) + "</body></html>"


def write_archive(
    directory: Path,
    year: int,
    draw_numbers: tuple[int, ...],
    wheels: tuple[str, ...] = WHEELS,
    number_offset: int = 0,
    date_offset_days: int = 0,
) -> Path:
    path = directory / f"archive-{year}.html"
    path.write_text(
        archive_html(
            year,
            draw_numbers,
            wheels,
            number_offset,
            date_offset_days,
        ),
        encoding="utf-8",
    )
    return path


def archive_draw_for_rollover(
    year: int,
    number: int,
) -> object:
    from import_lotto import (
        Draw,
        WheelResult,
    )

    return Draw(
        number=number,
        date=f"{year}-01-{number:02d}",
        wheels=(
            WheelResult(
                wheel="Firenze",
                numbers=(
                    1,
                    2,
                    3,
                    4,
                    5,
                ),
            ),
        ),
    )


def arguments(
    *,
    year: int | None = None,
    from_year: int | None = None,
    to_year: int | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        year=year,
        from_year=from_year,
        to_year=to_year,
    )


class UpdateLottoDatabasesTests(unittest.TestCase):
    def test_resolves_inclusive_range(
        self,
    ) -> None:
        self.assertEqual(
            resolve_years(
                arguments(
                    from_year=1871,
                    to_year=1874,
                )
            ),
            (1871, 1872, 1873, 1874),
        )

    def test_rejects_incomplete_range(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "specificati insieme",
        ):
            resolve_years(
                arguments(
                    from_year=1871,
                )
            )

    def test_rejects_reverse_range(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "successivo",
        ):
            resolve_years(
                arguments(
                    from_year=1874,
                    to_year=1871,
                )
            )

    def test_creates_partial_historical_database(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 3),
            )

            result = update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "creato",
            )
            self.assertEqual(
                result.completeness,
                "partial",
            )
            self.assertEqual(
                len(load_database_draws(database)),
                2,
            )

            with sqlite3.connect(database) as connection:
                metadata = dict(
                    connection.execute(
                        "SELECT key, value FROM metadata"
                    )
                )

            self.assertEqual(
                metadata["archive_completeness"],
                "partial",
            )
            self.assertEqual(
                metadata["missing_draw_numbers"],
                "2",
            )

    def test_detects_unchanged_database(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 2, 3),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            result = update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "invariato",
            )

    def test_protects_more_complete_local_database(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 2, 3),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            write_archive(
                sources,
                1871,
                (1, 3),
            )

            result = update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "protetto",
            )
            self.assertEqual(
                result.outcome,
                "WARN",
            )
            self.assertEqual(
                {
                    draw.number
                    for draw in load_database_draws(
                        database
                    )
                },
                {1, 2, 3},
            )

    def test_protects_local_wheel_results_missing_remotely(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 2, 3),
                wheels=(
                    "Firenze",
                    "Milano",
                ),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            write_archive(
                sources,
                1871,
                (1, 2, 3),
                wheels=(
                    "Firenze",
                ),
            )

            result = update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "protetto",
            )
            self.assertEqual(
                result.outcome,
                "WARN",
            )
            self.assertIn(
                "risultati di ruota",
                result.message,
            )

            local_draws = load_database_draws(
                database
            )

            self.assertEqual(
                {
                    result.wheel
                    for draw in local_draws
                    for result in draw.wheels
                },
                {
                    "Firenze",
                    "Milano",
                },
            )

    def test_protects_changed_remote_numbers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 2, 3),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            original_draws = load_database_draws(
                database
            )

            write_archive(
                sources,
                1871,
                (1, 2, 3),
                number_offset=1,
            )

            result = update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "protetto",
            )
            self.assertEqual(
                result.outcome,
                "WARN",
            )
            self.assertIn(
                "modifica numeri",
                result.message,
            )
            self.assertEqual(
                load_database_draws(database),
                original_draws,
            )

    def test_protects_changed_remote_dates(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 2, 3),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            original_draws = load_database_draws(
                database
            )

            write_archive(
                sources,
                1871,
                (1, 2, 3),
                date_offset_days=1,
            )

            result = update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "protetto",
            )
            self.assertEqual(
                result.outcome,
                "WARN",
            )
            self.assertIn(
                "modifica date",
                result.message,
            )
            self.assertEqual(
                load_database_draws(database),
                original_draws,
            )

    def test_dry_run_does_not_create_database(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1,),
            )

            result = update_database_year(
                1871,
                dry_run=True,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "dry-run:creazione",
            )
            self.assertFalse(
                database.exists()
            )

    def test_rolls_current_database_to_new_year(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-current.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 2),
            )
            write_archive(
                sources,
                1872,
                (1,),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            result = update_database_year(
                1872,
                source_directory=sources,
                destination_path=database,
            )

            self.assertEqual(
                result.action,
                "rollover",
            )

            years = {
                draw.date[:4]
                for draw in load_database_draws(
                    database
                )
            }

            self.assertEqual(
                years,
                {"1872"},
            )

    def test_rejects_wrong_year_in_historical_destination(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()

            database = (
                root
                / "lotto-1872.sqlite3"
            )

            write_archive(
                sources,
                1871,
                (1, 2),
            )
            write_archive(
                sources,
                1872,
                (1,),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            original_draws = load_database_draws(
                database
            )

            with self.assertRaisesRegex(
                ValueError,
                "cambio d'anno",
            ):
                update_database_year(
                    1872,
                    source_directory=sources,
                    destination_path=database,
                )

            self.assertEqual(
                load_database_draws(database),
                original_draws,
            )

    def test_detects_previous_year_in_current_database(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            current_database = (
                root
                / "lotto-current.sqlite3"
            )

            write_archive(
                sources,
                1871,
                (1, 2, 3),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=current_database,
            )

            plan = detect_rollover(
                (1872,),
                current_database_path=(
                    current_database
                ),
                system_year=1872,
            )

            self.assertIsNotNone(plan)
            assert plan is not None

            self.assertEqual(
                plan.previous_year,
                1871,
            )
            self.assertEqual(
                len(plan.current_draws),
                3,
            )

    def test_rollover_source_must_preserve_current_data(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            database = root / "lotto-1871.sqlite3"

            write_archive(
                sources,
                1871,
                (1, 2, 3),
            )

            update_database_year(
                1871,
                source_directory=sources,
                destination_path=database,
            )

            current_draws = load_database_draws(
                database
            )

            write_archive(
                sources,
                1871,
                (1, 3),
            )

            _, _, _, incomplete_draws = (
                __import__(
                    "update_lotto_databases"
                ).read_archive(
                    1871,
                    sources,
                )
            )

            with self.assertRaisesRegex(
                ValueError,
                "non conserva estrazioni",
            ):
                validate_rollover_source(
                    current_draws,
                    incomplete_draws,
                )

    def test_main_rebuilds_previous_year_before_current(
        self,
    ) -> None:
        previous_draws = (
            archive_draw_for_rollover(
                1871,
                1,
            ),
        )

        plan = RolloverPlan(
            previous_year=1871,
            current_database_path=Path(
                "data/lotto-current.sqlite3"
            ),
            current_draws=previous_draws,
        )

        historical_result = YearUpdateResult(
            year=1871,
            database_path=Path(
                "data/lotto-1871.sqlite3"
            ),
            remote_draw_count=1,
            completeness="complete",
            action="creato",
            outcome="OK",
        )

        current_result = YearUpdateResult(
            year=1872,
            database_path=Path(
                "data/lotto-current.sqlite3"
            ),
            remote_draw_count=1,
            completeness="complete",
            action="rollover",
            outcome="OK",
        )

        with (
            patch(
                "update_lotto_databases.current_system_year",
                return_value=1872,
            ),
            patch(
                "update_lotto_databases.detect_rollover",
                return_value=plan,
            ),
            patch(
                "update_lotto_databases.read_archive",
                return_value=(
                    Path(
                        "sources/archive-1871.html"
                    ),
                    "https://example.test/1871",
                    b"archive",
                    previous_draws,
                ),
            ),
            patch(
                "update_lotto_databases.update_database_year",
                side_effect=(
                    historical_result,
                    current_result,
                ),
            ) as updater,
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 0)

        self.assertEqual(
            [
                call.args[0]
                for call in updater.call_args_list
            ],
            [1871, 1872],
        )

        self.assertEqual(
            updater.call_args_list[0].kwargs[
                "source_directory"
            ],
            Path("sources"),
        )

        self.assertIsNone(
            updater.call_args_list[1].kwargs[
                "source_directory"
            ]
        )

    def test_rollover_warning_blocks_current_update(
        self,
    ) -> None:
        previous_draws = (
            archive_draw_for_rollover(
                1871,
                1,
            ),
        )

        plan = RolloverPlan(
            previous_year=1871,
            current_database_path=Path(
                "data/lotto-current.sqlite3"
            ),
            current_draws=previous_draws,
        )

        warning = YearUpdateResult(
            year=1871,
            database_path=Path(
                "data/lotto-1871.sqlite3"
            ),
            remote_draw_count=1,
            completeness="complete",
            action="protetto",
            outcome="WARN",
            message=(
                "La sorgente modifica dati storici."
            ),
        )

        with (
            patch(
                "update_lotto_databases.current_system_year",
                return_value=1872,
            ),
            patch(
                "update_lotto_databases.detect_rollover",
                return_value=plan,
            ),
            patch(
                "update_lotto_databases.read_archive",
                return_value=(
                    Path(
                        "sources/archive-1871.html"
                    ),
                    "https://example.test/1871",
                    b"archive",
                    previous_draws,
                ),
            ),
            patch(
                "update_lotto_databases.update_database_year",
                return_value=warning,
            ) as updater,
        ):
            exit_code = main(
                [
                    "--keep-going",
                ]
            )

        self.assertEqual(
            exit_code,
            1,
        )
        self.assertEqual(
            updater.call_count,
            1,
        )
        self.assertEqual(
            updater.call_args.args[0],
            1871,
        )

    def test_unsafe_rollover_blocks_current_update(
        self,
    ) -> None:
        previous_draws = (
            archive_draw_for_rollover(
                1871,
                1,
            ),
            archive_draw_for_rollover(
                1871,
                2,
            ),
        )

        incomplete_draws = (
            archive_draw_for_rollover(
                1871,
                1,
            ),
        )

        plan = RolloverPlan(
            previous_year=1871,
            current_database_path=Path(
                "data/lotto-current.sqlite3"
            ),
            current_draws=previous_draws,
        )

        with (
            patch(
                "update_lotto_databases.current_system_year",
                return_value=1872,
            ),
            patch(
                "update_lotto_databases.detect_rollover",
                return_value=plan,
            ),
            patch(
                "update_lotto_databases.read_archive",
                return_value=(
                    Path(
                        "sources/archive-1871.html"
                    ),
                    "https://example.test/1871",
                    b"archive",
                    incomplete_draws,
                ),
            ),
            patch(
                "update_lotto_databases.update_database_year",
            ) as updater,
        ):
            exit_code = main(
                [
                    "--keep-going",
                ]
            )

        self.assertEqual(exit_code, 1)
        updater.assert_not_called()

    def test_keep_going_processes_later_years(
        self,
    ) -> None:
        success = YearUpdateResult(
            year=1872,
            database_path=Path("one.sqlite3"),
            remote_draw_count=1,
            completeness="complete",
            action="creato",
            outcome="OK",
        )

        with patch(
            "update_lotto_databases.update_database_year",
            side_effect=(
                FileNotFoundError("mancante"),
                success,
            ),
        ) as updater:
            exit_code = main(
                [
                    "--from-year",
                    "1871",
                    "--to-year",
                    "1872",
                    "--keep-going",
                ]
            )

        self.assertEqual(
            updater.call_count,
            2,
        )
        self.assertEqual(
            exit_code,
            1,
        )


if __name__ == "__main__":
    unittest.main()
