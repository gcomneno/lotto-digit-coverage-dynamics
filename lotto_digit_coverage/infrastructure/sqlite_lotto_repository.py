"""Read-only SQLite implementation of the draw repository contract."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from pathlib import Path

from lotto_digit_coverage.application.repositories import (
    RepositoryDataError,
    RepositoryError,
    RepositorySchemaError,
)
from lotto_digit_coverage.domain.draws import DrawSnapshot


EXPECTED_VIEW_COLUMNS = {
    "draw_number",
    "draw_date",
    "wheel",
    "wheel_order",
    "position",
    "value",
    "value_padded",
}


class SQLiteLottoRepository:
    """Read-only SQLite adapter for Lotto draw analysis."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)

        if not self.database_path.is_file():
            raise FileNotFoundError(
                f"Database non trovato: {self.database_path}"
            )

        uri = f"file:{self.database_path.resolve()}?mode=ro"

        try:
            self._connection = sqlite3.connect(
                uri,
                uri=True,
            )
            self._connection.row_factory = sqlite3.Row
            self._validate_schema()
        except sqlite3.Error as error:
            connection = getattr(self, "_connection", None)

            if connection is not None:
                connection.close()

            raise RepositoryError(
                f"Impossibile leggere il database SQLite: {error}"
            ) from error
        except Exception:
            connection = getattr(self, "_connection", None)

            if connection is not None:
                connection.close()

            raise

    def __enter__(self) -> "SQLiteLottoRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def _validate_schema(self) -> None:
        try:
            rows = self._connection.execute(
                "PRAGMA table_info(v_draw_numbers)"
            ).fetchall()
        except sqlite3.Error as error:
            raise RepositorySchemaError(
                f"Impossibile leggere lo schema SQLite: {error}"
            ) from error

        columns = {
            str(row["name"])
            for row in rows
        }
        missing = EXPECTED_VIEW_COLUMNS - columns

        if missing:
            raise RepositorySchemaError(
                "Schema SQLite incompatibile. "
                "Colonne mancanti in v_draw_numbers: "
                + ", ".join(sorted(missing))
            )

    def latest_draw(self) -> tuple[int, str]:
        try:
            row = self._connection.execute(
                """
                SELECT draw_number, draw_date
                FROM draws
                ORDER BY draw_date DESC, draw_number DESC
                LIMIT 1
                """
            ).fetchone()
        except sqlite3.Error as error:
            raise RepositoryError(
                f"Impossibile leggere l'ultima estrazione: {error}"
            ) from error

        if row is None:
            raise RepositoryDataError(
                "Il database non contiene estrazioni."
            )

        return (
            int(row["draw_number"]),
            str(row["draw_date"]),
        )

    def resolve_draw_number(self, draw_number: int) -> tuple[int, str]:
        try:
            rows = self._connection.execute(
                """
                SELECT DISTINCT draw_number, draw_date
                FROM draws
                WHERE draw_number = ?
                ORDER BY draw_date, draw_number
                """,
                (draw_number,),
            ).fetchall()
        except sqlite3.Error as error:
            raise RepositoryError(
                "Impossibile risolvere il numero di estrazione: "
                f"{error}"
            ) from error

        if not rows:
            raise RepositoryDataError(
                f"Estrazione {draw_number} non trovata."
            )

        if len(rows) > 1:
            dates = ", ".join(
                str(row["draw_date"])
                for row in rows
            )
            raise RepositoryDataError(
                "Numero di estrazione ambiguo: "
                f"{draw_number}; date disponibili: {dates}."
            )

        row = rows[0]
        return int(row["draw_number"]), str(row["draw_date"])

    def latest_complete_draw(
        self,
        required_wheels: Sequence[str],
    ) -> tuple[int, str]:
        normalized_wheels = tuple(
            dict.fromkeys(
                wheel.strip()
                for wheel in required_wheels
                if wheel.strip()
            )
        )

        if not normalized_wheels:
            raise ValueError(
                "latest_complete_draw richiede almeno una ruota."
            )

        placeholders = ", ".join(
            "?"
            for _ in normalized_wheels
        )
        query = f"""
            WITH wheel_counts AS (
                SELECT
                    draw_number,
                    draw_date,
                    wheel,
                    COUNT(*) AS value_count
                FROM v_draw_numbers
                WHERE wheel IN ({placeholders})
                GROUP BY draw_number, draw_date, wheel
            ),
            complete_required AS (
                SELECT
                    draw_number,
                    draw_date
                FROM wheel_counts
                WHERE value_count = 5
                GROUP BY draw_number, draw_date
                HAVING COUNT(*) = ?
            )
            SELECT draw_number, draw_date
            FROM complete_required
            ORDER BY draw_date DESC, draw_number DESC
            LIMIT 1
        """

        try:
            row = self._connection.execute(
                query,
                (*normalized_wheels, len(normalized_wheels)),
            ).fetchone()
        except sqlite3.Error as error:
            raise RepositoryError(
                "Impossibile selezionare l'ultima estrazione completa: "
                f"{error}"
            ) from error

        if row is None:
            raise RepositoryDataError(
                "Nessuna estrazione completa disponibile per: "
                + ", ".join(normalized_wheels)
                + "."
            )

        return int(row["draw_number"]), str(row["draw_date"])

    def draws_by_wheel(
        self,
        *,
        through: tuple[int, str] | None = None,
    ) -> dict[str, tuple[DrawSnapshot, ...]]:
        where_clause = ""
        parameters: tuple[object, ...] = ()

        if through is not None:
            through_number, through_date = through
            where_clause = """
                WHERE
                    draw_date < ?
                    OR (
                        draw_date = ?
                        AND draw_number <= ?
                    )
            """
            parameters = (
                through_date,
                through_date,
                through_number,
            )

        query = f"""
            SELECT
                draw_number,
                draw_date,
                wheel,
                wheel_order,
                position,
                value
            FROM v_draw_numbers
            {where_clause}
            ORDER BY
                wheel_order,
                draw_date,
                draw_number,
                position
        """

        try:
            rows = self._connection.execute(
                query,
                parameters,
            ).fetchall()
        except sqlite3.Error as error:
            raise RepositoryError(
                f"Impossibile leggere le estrazioni: {error}"
            ) from error

        grouped: dict[
            tuple[str, int, int, str],
            list[int],
        ] = {}
        wheel_ordering: dict[str, int] = {}

        for row in rows:
            wheel = str(row["wheel"])
            wheel_order = int(row["wheel_order"])
            previous_order = wheel_ordering.get(wheel)

            if (
                previous_order is not None
                and previous_order != wheel_order
            ):
                raise RepositoryDataError(
                    "Ordine ruota incoerente per "
                    f"{wheel}: {previous_order} e {wheel_order}."
                )

            wheel_ordering[wheel] = wheel_order

            key = (
                wheel,
                wheel_order,
                int(row["draw_number"]),
                str(row["draw_date"]),
            )
            grouped.setdefault(key, []).append(
                int(row["value"])
            )

        by_wheel: dict[str, list[DrawSnapshot]] = {}

        for (
            wheel,
            wheel_order,
            draw_number,
            draw_date,
        ), numbers in grouped.items():
            if len(numbers) != 5:
                raise RepositoryDataError(
                    f"Estrazione {draw_number}, ruota {wheel}: "
                    f"attesi 5 numeri, trovati {len(numbers)}."
                )

            by_wheel.setdefault(wheel, []).append(
                DrawSnapshot(
                    draw_number=draw_number,
                    draw_date=draw_date,
                    wheel=wheel,
                    wheel_order=wheel_order,
                    numbers=tuple(numbers),
                )
            )

        return {
            wheel: tuple(
                sorted(
                    draws,
                    key=lambda draw: (
                        draw.draw_date,
                        draw.draw_number,
                    ),
                )
            )
            for wheel, draws in sorted(
                by_wheel.items(),
                key=lambda item: wheel_ordering[item[0]],
            )
        }
