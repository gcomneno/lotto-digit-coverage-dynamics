from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lotto_digit_coverage.infrastructure.sqlite_read_query_authority import (
    AuthorizedReadQuery,
    SqliteReadQueryPolicy,
)
from lotto_digit_coverage.infrastructure.sqlite_read_query_executor import (
    ReadQueryExecutionError,
    SqliteReadQueryExecutor,
)


class SqliteReadQueryExecutorTests(unittest.TestCase):
    def _policy(
        self,
        *,
        max_result_rows: int = 500,
    ) -> SqliteReadQueryPolicy:
        return SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                        "value_padded",
                    }
                )
            },
            functions=frozenset({"count"}),
            max_result_rows=max_result_rows,
        )

    def _create_database(
        self,
        directory: Path,
        *,
        row_count: int = 3,
    ) -> Path:
        database = directory / "lotto.sqlite3"

        with sqlite3.connect(database) as connection:
            connection.execute(
                """
                CREATE TABLE v_draw_numbers (
                    draw_number INTEGER,
                    draw_date TEXT,
                    wheel TEXT,
                    wheel_order INTEGER,
                    position INTEGER,
                    value INTEGER
                )
                """
            )

            connection.executemany(
                """
                INSERT INTO v_draw_numbers (
                    draw_number,
                    draw_date,
                    wheel,
                    wheel_order,
                    position,
                    value
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        index,
                        f"2026-09-{index:02d}",
                        "Napoli",
                        6,
                        1,
                        index,
                    )
                    for index in range(1, row_count + 1)
                ],
            )

        return database

    def _create_production_view_database(
        self,
        directory: Path,
    ) -> Path:
        database = directory / "lotto-view.sqlite3"

        with sqlite3.connect(database) as connection:
            connection.execute(
                """
                CREATE TABLE draws (
                    id INTEGER PRIMARY KEY,
                    draw_number INTEGER NOT NULL,
                    draw_date TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE wheels (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    sort_order INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE draw_numbers (
                    draw_id INTEGER NOT NULL,
                    wheel_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    value INTEGER NOT NULL
                )
                """
            )

            connection.execute(
                "INSERT INTO draws VALUES (?, ?, ?)",
                (1, 150, "2026-09-18"),
            )
            connection.execute(
                "INSERT INTO wheels VALUES (?, ?, ?)",
                (1, "Napoli", 6),
            )
            connection.executemany(
                "INSERT INTO draw_numbers VALUES (?, ?, ?, ?)",
                [
                    (1, 1, position, value)
                    for position, value in enumerate(
                        (18, 2, 3, 4, 81),
                        1,
                    )
                ],
            )

            connection.execute(
                """
                CREATE VIEW v_draw_numbers AS
                SELECT
                    d.draw_number,
                    d.draw_date,
                    w.name AS wheel,
                    w.sort_order AS wheel_order,
                    n.position,
                    n.value,
                    printf('%02d', n.value) AS value_padded
                FROM draws d
                JOIN draw_numbers n ON n.draw_id = d.id
                JOIN wheels w ON w.id = n.wheel_id
                """
            )

        return database

    def test_executes_authorized_read_query_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_database(Path(temporary))

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            query = AuthorizedReadQuery(
                sql=(
                    "SELECT draw_number, wheel, value "
                    "FROM v_draw_numbers "
                    "ORDER BY draw_number "
                    "LIMIT 10"
                ),
                parameters={},
            )

            result = executor.execute(query)

            self.assertEqual(result.database, database.resolve())
            self.assertEqual(
                result.columns,
                ("draw_number", "wheel", "value"),
            )
            self.assertEqual(
                result.rows,
                (
                    (1, "Napoli", 1),
                    (2, "Napoli", 2),
                    (3, "Napoli", 3),
                ),
            )

    def test_executes_through_declared_production_view(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_production_view_database(
                Path(temporary)
            )

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            query = AuthorizedReadQuery(
                sql=(
                    "SELECT draw_number, draw_date, wheel, "
                    "position, value, value_padded "
                    "FROM v_draw_numbers "
                    "WHERE wheel = :wheel "
                    "ORDER BY position "
                    "LIMIT 5"
                ),
                parameters={"wheel": "Napoli"},
            )

            result = executor.execute(query)

            self.assertEqual(
                result.columns,
                (
                    "draw_number",
                    "draw_date",
                    "wheel",
                    "position",
                    "value",
                    "value_padded",
                ),
            )
            self.assertEqual(
                result.rows,
                (
                    (150, "2026-09-18", "Napoli", 1, 18, "18"),
                    (150, "2026-09-18", "Napoli", 2, 2, "02"),
                    (150, "2026-09-18", "Napoli", 3, 3, "03"),
                    (150, "2026-09-18", "Napoli", 4, 4, "04"),
                    (150, "2026-09-18", "Napoli", 5, 81, "81"),
                ),
            )

    def test_runtime_authorizer_rejects_direct_underlying_table_read(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_production_view_database(
                Path(temporary)
            )

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            forged = AuthorizedReadQuery(
                sql="SELECT draw_number FROM draws LIMIT 1",
                parameters={},
            )

            with self.assertRaises(ReadQueryExecutionError):
                executor.execute(forged)

    def test_empty_result_is_returned_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_database(
                Path(temporary),
                row_count=3,
            )

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            query = AuthorizedReadQuery(
                sql=(
                    "SELECT draw_number, wheel, value "
                    "FROM v_draw_numbers "
                    "WHERE value = :value "
                    "ORDER BY draw_number "
                    "LIMIT 10"
                ),
                parameters={"value": 90},
            )

            result = executor.execute(query)

            self.assertEqual(
                result.columns,
                ("draw_number", "wheel", "value"),
            )
            self.assertEqual(result.rows, ())

    def test_connection_uses_read_only_uri(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_database(Path(temporary))
            real_connect = sqlite3.connect
            observed: dict[str, object] = {}

            def recording_connect(
                target: str,
                *args: object,
                **kwargs: object,
            ) -> sqlite3.Connection:
                observed["target"] = target
                observed["uri"] = kwargs.get("uri")
                return real_connect(target, *args, **kwargs)

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            with patch(
                "lotto_digit_coverage.infrastructure."
                "sqlite_read_query_executor.sqlite3.connect",
                side_effect=recording_connect,
            ):
                connection = executor._open_connection()
                connection.close()

            self.assertTrue(str(observed["target"]).startswith("file:"))
            self.assertIn("mode=ro", str(observed["target"]))
            self.assertIs(observed["uri"], True)

    def test_connection_enables_query_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_database(Path(temporary))

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            connection = executor._open_connection()

            try:
                query_only = connection.execute(
                    "PRAGMA query_only"
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(query_only, 1)

    def test_missing_database_is_not_created(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "missing.sqlite3"

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            query = AuthorizedReadQuery(
                sql="SELECT draw_number FROM v_draw_numbers LIMIT 1",
                parameters={},
            )

            with self.assertRaises(FileNotFoundError):
                executor.execute(query)

            self.assertFalse(database.exists())

    def test_runtime_authorizer_rejects_forged_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_database(Path(temporary))

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
            )

            forged = AuthorizedReadQuery(
                sql="DELETE FROM v_draw_numbers",
                parameters={},
            )

            with self.assertRaises(ReadQueryExecutionError):
                executor.execute(forged)

    def test_rejects_result_larger_than_policy_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_database(
                Path(temporary),
                row_count=3,
            )

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(max_result_rows=2),
            )

            query = AuthorizedReadQuery(
                sql=(
                    "SELECT draw_number "
                    "FROM v_draw_numbers "
                    "ORDER BY draw_number "
                    "LIMIT 3"
                ),
                parameters={},
            )

            with self.assertRaises(ReadQueryExecutionError):
                executor.execute(query)

    def test_interrupts_query_after_execution_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = self._create_database(
                Path(temporary),
                row_count=40,
            )

            executor = SqliteReadQueryExecutor(
                database=database,
                policy=self._policy(),
                max_execution_seconds=0.0,
                progress_steps=1,
            )

            query = AuthorizedReadQuery(
                sql=(
                    "SELECT count(*) "
                    "FROM v_draw_numbers AS a "
                    "CROSS JOIN v_draw_numbers AS b "
                    "CROSS JOIN v_draw_numbers AS c "
                    "CROSS JOIN v_draw_numbers AS d "
                    "LIMIT 1"
                ),
                parameters={},
            )

            with self.assertRaises(ReadQueryExecutionError):
                executor.execute(query)


if __name__ == "__main__":
    unittest.main()
