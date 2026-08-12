from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from lotto_digit_coverage.application.repositories import (
    DrawRepository,
    RepositoryDataError,
    RepositorySchemaError,
)
from lotto_digit_coverage.domain.draws import (
    DrawSnapshot,
    format_number,
    split_digits,
)
from lotto_digit_coverage.infrastructure.sqlite_lotto_repository import (
    SQLiteLottoRepository,
)
from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import LottoRepository


SCHEMA = """
CREATE TABLE draws (
    id INTEGER PRIMARY KEY,
    draw_number INTEGER NOT NULL,
    draw_date TEXT NOT NULL
);

CREATE TABLE wheels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL
);

CREATE TABLE draw_numbers (
    draw_id INTEGER NOT NULL,
    wheel_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    value INTEGER NOT NULL
);

CREATE VIEW v_draw_numbers AS
SELECT
    d.draw_number,
    d.draw_date,
    w.name AS wheel,
    w.sort_order AS wheel_order,
    n.position,
    n.value,
    printf('%02d', n.value) AS value_padded
FROM draws AS d
JOIN draw_numbers AS n
    ON n.draw_id = d.id
JOIN wheels AS w
    ON w.id = n.wheel_id;
"""


class SQLiteLottoRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary.name) / "fixture.sqlite3"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create_database(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.executescript(SCHEMA)
        return connection

    @staticmethod
    def add_wheel(
        connection: sqlite3.Connection,
        *,
        wheel_id: int,
        name: str,
        order: int,
    ) -> None:
        connection.execute(
            "INSERT INTO wheels(id, name, sort_order) VALUES (?, ?, ?)",
            (wheel_id, name, order),
        )

    @staticmethod
    def add_draw(
        connection: sqlite3.Connection,
        *,
        draw_id: int,
        draw_number: int,
        draw_date: str,
        wheel_id: int,
        numbers: tuple[int, ...],
    ) -> None:
        connection.execute(
            "INSERT INTO draws(id, draw_number, draw_date) VALUES (?, ?, ?)",
            (draw_id, draw_number, draw_date),
        )

        connection.executemany(
            """
            INSERT INTO draw_numbers(draw_id, wheel_id, position, value)
            VALUES (?, ?, ?, ?)
            """,
            (
                (draw_id, wheel_id, position, value)
                for position, value in enumerate(numbers, start=1)
            ),
        )

    def test_legacy_repository_name_is_the_sqlite_adapter(self) -> None:
        self.assertIs(LottoRepository, SQLiteLottoRepository)

    def test_adapter_satisfies_application_contract(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(4, 12, 23, 45, 90),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            self.assertIsInstance(repository, DrawRepository)

    def test_orders_wheels_and_draws_without_assuming_monotone_draw_numbers(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Roma",
            order=8,
        )
        self.add_wheel(
            connection,
            wheel_id=2,
            name="Bari",
            order=1,
        )

        self.add_draw(
            connection,
            draw_id=1,
            draw_number=100,
            draw_date="2025-12-30",
            wheel_id=2,
            numbers=(1, 2, 3, 4, 5),
        )
        self.add_draw(
            connection,
            draw_id=2,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=2,
            numbers=(6, 7, 8, 9, 10),
        )
        self.add_draw(
            connection,
            draw_id=3,
            draw_number=100,
            draw_date="2025-12-30",
            wheel_id=1,
            numbers=(11, 12, 13, 14, 15),
        )
        self.add_draw(
            connection,
            draw_id=4,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(16, 17, 18, 19, 20),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            draws = repository.draws_by_wheel()

        self.assertEqual(tuple(draws), ("Bari", "Roma"))
        self.assertEqual(
            tuple(draw.draw_number for draw in draws["Bari"]),
            (100, 1),
        )
        self.assertEqual(
            tuple(draw.draw_date for draw in draws["Bari"]),
            ("2025-12-30", "2026-01-02"),
        )
        self.assertEqual(draws["Roma"][0].wheel_order, 8)

    def test_latest_draw_uses_date_before_reset_draw_number(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=200,
            draw_date="2025-12-30",
            wheel_id=1,
            numbers=(1, 2, 3, 4, 5),
        )
        self.add_draw(
            connection,
            draw_id=2,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(6, 7, 8, 9, 10),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            latest = repository.latest_draw()

        self.assertEqual(latest, (1, "2026-01-02"))

    def test_resolves_unique_draw_number_to_dated_key(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=77,
            draw_date="2026-06-30",
            wheel_id=1,
            numbers=(1, 2, 3, 4, 5),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            resolved = repository.resolve_draw_number(77)

        self.assertEqual(resolved, (77, "2026-06-30"))

    def test_rejects_ambiguous_draw_number_across_years(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=1,
            draw_date="2025-01-02",
            wheel_id=1,
            numbers=(1, 2, 3, 4, 5),
        )
        self.add_draw(
            connection,
            draw_id=2,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(6, 7, 8, 9, 10),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            with self.assertRaisesRegex(
                RepositoryDataError,
                "ambiguo",
            ):
                repository.resolve_draw_number(1)

    def test_historical_cutoff_is_inclusive_and_date_aware(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=100,
            draw_date="2025-12-30",
            wheel_id=1,
            numbers=(1, 2, 3, 4, 5),
        )
        self.add_draw(
            connection,
            draw_id=2,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(6, 7, 8, 9, 10),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            cutoff = repository.resolve_draw_number(100)
            draws = repository.draws_by_wheel(through=cutoff)

        self.assertEqual(
            tuple(
                (draw.draw_number, draw.draw_date)
                for draw in draws["Bari"]
            ),
            ((100, "2025-12-30"),),
        )

    def test_latest_complete_draw_skips_newer_incomplete_draw(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_wheel(
            connection,
            wheel_id=2,
            name="Roma",
            order=8,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(1, 2, 3, 4, 5),
        )
        self.add_draw(
            connection,
            draw_id=2,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=2,
            numbers=(6, 7, 8, 9, 10),
        )
        self.add_draw(
            connection,
            draw_id=3,
            draw_number=2,
            draw_date="2026-01-04",
            wheel_id=1,
            numbers=(11, 12, 13, 14, 15),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            selected = repository.latest_complete_draw(
                ("Bari", "Roma")
            )

        self.assertEqual(selected, (1, "2026-01-02"))

    def test_latest_complete_draw_requires_all_requested_wheels(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_wheel(
            connection,
            wheel_id=2,
            name="Roma",
            order=8,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(1, 2, 3, 4, 5),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            with self.assertRaises(RepositoryDataError):
                repository.latest_complete_draw(
                    ("Bari", "Roma")
                )

    def test_preserves_number_position_and_leading_zero_semantics(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(4, 38, 58, 70, 85),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            snapshot = repository.draws_by_wheel()["Bari"][0]

        self.assertEqual(snapshot.numbers, (4, 38, 58, 70, 85))
        self.assertEqual(format_number(snapshot.numbers[0]), "04")
        self.assertEqual(split_digits(snapshot.numbers[0]), (0, 4))

    def test_incomplete_wheel_draw_is_rejected(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        self.add_draw(
            connection,
            draw_id=1,
            draw_number=1,
            draw_date="2026-01-02",
            wheel_id=1,
            numbers=(1, 2, 3, 4),
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            with self.assertRaises(RepositoryDataError):
                repository.draws_by_wheel()

    def test_missing_view_column_is_reported_as_schema_error(self) -> None:
        connection = sqlite3.connect(self.database_path)
        connection.executescript(
            """
            CREATE TABLE draws (
                id INTEGER PRIMARY KEY,
                draw_number INTEGER NOT NULL,
                draw_date TEXT NOT NULL
            );
            CREATE TABLE v_draw_numbers (
                draw_number INTEGER,
                draw_date TEXT,
                wheel TEXT,
                wheel_order INTEGER,
                position INTEGER,
                value INTEGER
            );
            """
        )
        connection.close()

        with self.assertRaises(RepositorySchemaError):
            SQLiteLottoRepository(self.database_path)

    def test_corrupt_database_is_normalized_to_repository_schema_error(self) -> None:
        self.database_path.write_bytes(b"this is not a SQLite database")

        with self.assertRaises(RepositorySchemaError):
            SQLiteLottoRepository(self.database_path)

    def test_repository_connection_is_read_only(self) -> None:
        connection = self.create_database()
        self.add_wheel(
            connection,
            wheel_id=1,
            name="Bari",
            order=1,
        )
        connection.commit()
        connection.close()

        with SQLiteLottoRepository(self.database_path) as repository:
            with self.assertRaises(sqlite3.OperationalError):
                repository._connection.execute(
                    "INSERT INTO draws(id, draw_number, draw_date) "
                    "VALUES (1, 1, '2026-01-02')"
                )

    def test_missing_database_keeps_file_not_found_compatibility(self) -> None:
        missing = Path(self.temporary.name) / "missing.sqlite3"

        with self.assertRaises(FileNotFoundError):
            SQLiteLottoRepository(missing)

    def test_digit_coverage_loader_uses_only_repository_contract(self) -> None:
        expected = {
            "Bari": (
                DrawSnapshot(
                    draw_number=1,
                    draw_date="2026-01-02",
                    wheel="Bari",
                    wheel_order=1,
                    numbers=(1, 2, 3, 4, 5),
                ),
            ),
        }

        class FakeRepository:
            def latest_draw(self) -> tuple[int, str]:
                return 1, "2026-01-02"

            def resolve_draw_number(self, draw_number: int) -> tuple[int, str]:
                if draw_number != 1:
                    raise RepositoryDataError("not found")
                return 1, "2026-01-02"

            def latest_complete_draw(
                self,
                required_wheels: tuple[str, ...],
            ) -> tuple[int, str]:
                return 1, "2026-01-02"

            def draws_by_wheel(
                self,
                *,
                through: tuple[int, str] | None = None,
            ) -> dict[str, tuple[DrawSnapshot, ...]]:
                return expected

        fake = FakeRepository()

        self.assertIsInstance(fake, DrawRepository)
        self.assertEqual(
            load_draws_by_wheel(fake),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
