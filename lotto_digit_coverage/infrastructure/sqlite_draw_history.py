"""Read-only SQLite implementation for deterministic draw-history queries."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote

from lotto_digit_coverage.application.natural_query import DrawHistoryRow


class SqliteDrawHistoryRepository:
    def __init__(self, database: Path) -> None:
        self._database = database

    def load_wheel_history(
        self,
        wheel: str,
        *,
        from_draw: int | None,
        to_draw: int | None,
    ) -> tuple[DrawHistoryRow, ...]:
        if not self._database.is_file():
            raise FileNotFoundError(f"database assente: {self._database}")

        conditions = ["wheel = ?"]
        parameters: list[object] = [wheel]
        if from_draw is not None:
            conditions.append("draw_number >= ?")
            parameters.append(from_draw)
        if to_draw is not None:
            conditions.append("draw_number <= ?")
            parameters.append(to_draw)

        sql = f"""
            SELECT draw_number, draw_date, position, value
            FROM v_draw_numbers
            WHERE {' AND '.join(conditions)}
            ORDER BY draw_number ASC, position ASC
        """

        database_uri = "file:" + quote(str(self._database.resolve())) + "?mode=ro"
        with sqlite3.connect(database_uri, uri=True) as connection:
            raw_rows = connection.execute(sql, parameters).fetchall()

        grouped: dict[tuple[int, str], list[int]] = {}
        for draw_number, draw_date, _position, value in raw_rows:
            key = int(draw_number), str(draw_date)
            grouped.setdefault(key, []).append(int(value))

        rows: list[DrawHistoryRow] = []
        for (draw_number, draw_date), values in grouped.items():
            if len(values) != 5:
                raise ValueError(
                    f"estrazione {draw_number} del {draw_date} su {wheel}: "
                    f"attesi 5 numeri, trovati {len(values)}."
                )
            rows.append(
                DrawHistoryRow(
                    draw_number=draw_number,
                    draw_date=draw_date,
                    numbers=tuple(values),
                )
            )
        return tuple(rows)
