from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from import_lotto import (
    Draw,
    WheelResult,
    archive_completeness,
    create_schema,
    import_draws,
    missing_draw_numbers,
    validate_draw,
    verify_database,
)


HISTORICAL_WHEELS = (
    "Firenze",
    "Milano",
    "Napoli",
    "Palermo",
    "Roma",
    "Torino",
    "Venezia",
)


def result(wheel: str) -> WheelResult:
    return WheelResult(
        wheel=wheel,
        numbers=(1, 2, 3, 4, 5),
    )


def draw(
    number: int,
    wheels: tuple[str, ...],
) -> Draw:
    return Draw(
        number=number,
        date=f"1874-01-{number:02d}",
        wheels=tuple(
            result(wheel)
            for wheel in wheels
        ),
    )


class HistoricalLottoImportTests(unittest.TestCase):
    def test_accepts_historical_wheel_subset(
        self,
    ) -> None:
        validate_draw(
            draw(
                1,
                HISTORICAL_WHEELS,
            )
        )

    def test_accepts_wheel_configuration_change(
        self,
    ) -> None:
        validate_draw(
            draw(
                1,
                HISTORICAL_WHEELS,
            )
        )
        validate_draw(
            draw(
                2,
                (
                    "Bari",
                    *HISTORICAL_WHEELS,
                ),
            )
        )

    def test_rejects_draw_without_wheels(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "nessuna ruota",
        ):
            validate_draw(
                draw(1, ())
            )

    def test_rejects_duplicate_wheel(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "ruote duplicate",
        ):
            validate_draw(
                draw(
                    1,
                    (
                        "Roma",
                        "Roma",
                    ),
                )
            )

    def test_classifies_missing_draws_as_partial(
        self,
    ) -> None:
        draws = [
            draw(3, HISTORICAL_WHEELS),
            draw(1, HISTORICAL_WHEELS),
        ]

        self.assertEqual(
            missing_draw_numbers(draws),
            (2,),
        )
        self.assertEqual(
            archive_completeness(draws),
            "partial",
        )

    def test_imports_mixed_historical_layout(
        self,
    ) -> None:
        draws = [
            draw(
                2,
                (
                    "Bari",
                    *HISTORICAL_WHEELS,
                ),
            ),
            draw(
                1,
                HISTORICAL_WHEELS,
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            database = (
                Path(directory)
                / "lotto-1874.sqlite3"
            )

            with sqlite3.connect(database) as connection:
                create_schema(connection)
                import_draws(
                    connection,
                    draws,
                    source_hash="test-hash",
                    source_url="https://example.test/1874",
                    source_path=Path("archive-1874.html"),
                    import_limit=len(draws),
                    archive_year=1874,
                )
                verify_database(
                    connection,
                    expected_draws=draws,
                )

                wheel_results = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM (
                        SELECT draw_id, wheel_id
                        FROM draw_numbers
                        GROUP BY draw_id, wheel_id
                    )
                    """
                ).fetchone()[0]

                self.assertEqual(
                    wheel_results,
                    15,
                )

    def test_limited_import_preserves_source_completeness(
        self,
    ) -> None:
        complete_archive = [
            draw(3, HISTORICAL_WHEELS),
            draw(2, HISTORICAL_WHEELS),
            draw(1, HISTORICAL_WHEELS),
        ]

        selected_draws = complete_archive[:2]

        with tempfile.TemporaryDirectory() as directory:
            database = (
                Path(directory)
                / "limited.sqlite3"
            )

            with sqlite3.connect(database) as connection:
                create_schema(connection)
                import_draws(
                    connection,
                    selected_draws,
                    source_hash="limited-hash",
                    source_url="https://example.test/limited",
                    source_path=Path("limited.html"),
                    import_limit=len(selected_draws),
                    archive_year=1874,
                    archive_draws=complete_archive,
                )
                verify_database(
                    connection,
                    expected_draws=selected_draws,
                    archive_draws=complete_archive,
                )

                metadata = dict(
                    connection.execute(
                        "SELECT key, value FROM metadata"
                    )
                )

                self.assertEqual(
                    metadata["archive_completeness"],
                    "complete",
                )
                self.assertEqual(
                    metadata["archive_draw_count"],
                    "3",
                )
                self.assertEqual(
                    metadata["stored_draw_count"],
                    "2",
                )
                self.assertEqual(
                    metadata["missing_draw_count"],
                    "0",
                )

    def test_imports_partial_archive_with_metadata(
        self,
    ) -> None:
        draws = [
            draw(3, HISTORICAL_WHEELS),
            draw(1, HISTORICAL_WHEELS),
        ]

        with tempfile.TemporaryDirectory() as directory:
            database = (
                Path(directory)
                / "partial.sqlite3"
            )

            with sqlite3.connect(database) as connection:
                create_schema(connection)
                import_draws(
                    connection,
                    draws,
                    source_hash="partial-hash",
                    source_url="https://example.test/partial",
                    source_path=Path("partial.html"),
                    import_limit=len(draws),
                    archive_year=1874,
                )
                verify_database(
                    connection,
                    expected_draws=draws,
                )

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
                    metadata["missing_draw_count"],
                    "1",
                )
                self.assertEqual(
                    metadata["missing_draw_numbers"],
                    "2",
                )


if __name__ == "__main__":
    unittest.main()
