"""Bounded read-only execution for authorized SQLite queries."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from urllib.parse import quote

from lotto_digit_coverage.infrastructure.sqlite_read_query_authority import (
    AuthorizedReadQuery,
    SqliteReadQueryPolicy,
    _build_read_query_authorizer,
)


class ReadQueryExecutionError(RuntimeError):
    """Authorized query could not be executed within the read-only contract."""


@dataclass(frozen=True, slots=True)
class SqliteReadQueryResult:
    """Deterministic tabular result returned by the SQLite executor."""

    database: Path
    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]


class SqliteReadQueryExecutor:
    """Execute authorized queries with independent SQLite runtime controls."""

    def __init__(
        self,
        *,
        database: Path,
        policy: SqliteReadQueryPolicy,
        max_execution_seconds: float = 2.0,
        progress_steps: int = 1000,
    ) -> None:
        if max_execution_seconds < 0:
            raise ValueError(
                "max_execution_seconds must not be negative"
            )
        if progress_steps <= 0:
            raise ValueError("progress_steps must be positive")

        self._database = database
        self._policy = policy
        self._max_execution_seconds = max_execution_seconds
        self._progress_steps = progress_steps

    def _open_connection(self) -> sqlite3.Connection:
        if not self._database.is_file():
            raise FileNotFoundError(
                f"database not found: {self._database}"
            )

        resolved = self._database.resolve()
        uri = "file:" + quote(str(resolved)) + "?mode=ro"

        connection = sqlite3.connect(
            uri,
            uri=True,
        )

        try:
            connection.execute("PRAGMA query_only=ON")
        except Exception:
            connection.close()
            raise

        return connection

    def execute(
        self,
        query: AuthorizedReadQuery,
    ) -> SqliteReadQueryResult:
        connection = self._open_connection()

        deadline = monotonic() + self._max_execution_seconds

        def progress_handler() -> int:
            return int(monotonic() >= deadline)

        connection.set_progress_handler(
            progress_handler,
            self._progress_steps,
        )
        connection.set_authorizer(
            _build_read_query_authorizer(
                self._policy,
                allow_view_expansion=True,
            )
        )

        try:
            cursor = connection.execute(
                query.sql,
                dict(query.parameters),
            )

            columns = tuple(
                description[0]
                for description in cursor.description or ()
            )

            rows = cursor.fetchmany(
                self._policy.max_result_rows + 1
            )

            if len(rows) > self._policy.max_result_rows:
                raise ReadQueryExecutionError(
                    "query result exceeds the configured row limit"
                )

            return SqliteReadQueryResult(
                database=self._database.resolve(),
                columns=columns,
                rows=tuple(
                    tuple(value for value in row)
                    for row in rows
                ),
            )

        except ReadQueryExecutionError:
            raise
        except sqlite3.Error as error:
            if "interrupted" in str(error).casefold():
                raise ReadQueryExecutionError(
                    "query exceeded the configured execution-time limit"
                ) from error

            raise ReadQueryExecutionError(
                f"read query execution failed: {error}"
            ) from error
        finally:
            connection.close()
