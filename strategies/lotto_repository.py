"""Primitive generiche per numeri, estrazioni e database del Lotto."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


EXPECTED_VIEW_COLUMNS = {
    "draw_number",
    "draw_date",
    "wheel",
    "wheel_order",
    "position",
    "value",
    "value_padded",
}


@dataclass(frozen=True)
class DrawSnapshot:
    """Cinque numeri estratti su una singola ruota."""

    draw_number: int
    draw_date: str
    wheel: str
    wheel_order: int
    numbers: tuple[int, ...]


def format_number(value: int) -> str:
    """Rappresenta ogni numero del Lotto come coppia di cifre."""

    if not 1 <= value <= 90:
        raise ValueError(
            f"Numero del Lotto fuori intervallo 1–90: {value}"
        )

    return f"{value:02d}"


def split_digits(value: int) -> tuple[int, int]:
    """Scompone un numero nelle due cifre, incluso lo zero iniziale."""

    formatted = format_number(value)
    return int(formatted[0]), int(formatted[1])


class LottoRepository:
    """Accesso generico in sola lettura al database delle estrazioni."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)

        if not self.database_path.is_file():
            raise FileNotFoundError(
                f"Database non trovato: {self.database_path}"
            )

        uri = f"file:{self.database_path.resolve()}?mode=ro"

        self.connection = sqlite3.connect(
            uri,
            uri=True,
        )
        self.connection.row_factory = sqlite3.Row

        self._validate_schema()

    def __enter__(self) -> "LottoRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def _validate_schema(self) -> None:
        rows = self.connection.execute(
            "PRAGMA table_info(v_draw_numbers)"
        ).fetchall()

        columns = {
            row["name"]
            for row in rows
        }

        missing = EXPECTED_VIEW_COLUMNS - columns

        if missing:
            raise RuntimeError(
                "Schema SQLite incompatibile. "
                "Colonne mancanti in v_draw_numbers: "
                + ", ".join(sorted(missing))
            )

    def latest_draw(self) -> tuple[int, str]:
        row = self.connection.execute(
            """
            SELECT draw_number, draw_date
            FROM draws
            ORDER BY draw_date DESC, draw_number DESC
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "Il database non contiene estrazioni."
            )

        return (
            int(row["draw_number"]),
            str(row["draw_date"]),
        )
