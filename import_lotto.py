#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


SOURCE_URL = (
    "https://www.estrazionedellotto.it/risultati/archivio-lotto-2026"
)

EXPECTED_WHEELS = (
    "Bari",
    "Cagliari",
    "Firenze",
    "Genova",
    "Milano",
    "Napoli",
    "Palermo",
    "Roma",
    "Torino",
    "Venezia",
    "Nazionale",
)

SOURCE_PATH = Path("_work/archive-2026.html")
DATABASE_PATH = Path("data/lotto-2026.sqlite3")
IMPORT_LIMIT = 60


@dataclass(frozen=True)
class WheelResult:
    wheel: str
    numbers: tuple[int, ...]


@dataclass(frozen=True)
class Draw:
    number: int
    date: str
    wheels: tuple[WheelResult, ...]


class LottoArchiveParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

        self.draws: list[Draw] = []

        self.current_draw: dict | None = None
        self.draw_div_depth = 0

        self.current_row: dict | None = None
        self.capture: str | None = None
        self.buffer: list[str] = []

    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        for name, value in attrs:
            if name == "class" and value:
                return set(value.split())
        return set()

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        classes = self._classes(attrs)

        if tag == "div" and "lottoDraws" in classes:
            if self.current_draw is not None:
                raise ValueError(
                    "Trovato un nuovo blocco lottoDraws "
                    "prima della chiusura del precedente."
                )

            self.current_draw = {
                "number": None,
                "date": None,
                "wheels": [],
            }
            self.draw_div_depth = 1
            return

        if self.current_draw is None:
            return

        if tag == "div":
            self.draw_div_depth += 1
            return

        if tag == "span":
            self.capture = "draw_number"
            self.buffer = []
            return

        if tag == "strong":
            self.capture = "draw_date"
            self.buffer = []
            return

        if tag == "ul" and "ballRow" in classes:
            if self.current_row is not None:
                raise ValueError("Riga di ruota annidata in modo inatteso.")

            self.current_row = {
                "wheel": None,
                "numbers": [],
            }
            return

        if tag == "li" and self.current_row is not None:
            if "wheelTitle" in classes:
                self.capture = "wheel"
                self.buffer = []
            elif "ball" in classes:
                self.capture = "ball"
                self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.capture is not None:
            self.buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.current_draw is None:
            return

        if tag == "span" and self.capture == "draw_number":
            text = " ".join("".join(self.buffer).split())
            match = re.search(
                r"Estrazione\s+n\.?\s*(\d+)",
                text,
                flags=re.IGNORECASE,
            )

            if match:
                self.current_draw["number"] = int(match.group(1))

            self.capture = None
            self.buffer = []
            return

        if tag == "strong" and self.capture == "draw_date":
            text = " ".join("".join(self.buffer).split())
            match = re.search(r"(\d{2}/\d{2}/\d{4})", text)

            if match:
                parsed_date = datetime.strptime(
                    match.group(1),
                    "%d/%m/%Y",
                ).date()
                self.current_draw["date"] = parsed_date.isoformat()

            self.capture = None
            self.buffer = []
            return

        if tag == "li" and self.capture in {"wheel", "ball"}:
            text = " ".join("".join(self.buffer).split())

            if self.capture == "wheel":
                self.current_row["wheel"] = text
            else:
                if not text.isdigit():
                    raise ValueError(
                        f"Numero non valido incontrato: {text!r}"
                    )
                self.current_row["numbers"].append(int(text))

            self.capture = None
            self.buffer = []
            return

        if tag == "ul" and self.current_row is not None:
            wheel = self.current_row["wheel"]
            numbers = tuple(self.current_row["numbers"])

            if wheel is not None:
                self.current_draw["wheels"].append(
                    WheelResult(
                        wheel=wheel,
                        numbers=numbers,
                    )
                )

            self.current_row = None
            return

        if tag == "div":
            self.draw_div_depth -= 1

            if self.draw_div_depth == 0:
                number = self.current_draw["number"]
                date = self.current_draw["date"]
                wheels = tuple(self.current_draw["wheels"])

                if number is None or date is None:
                    raise ValueError(
                        "Blocco estrazione privo di numero o data."
                    )

                self.draws.append(
                    Draw(
                        number=number,
                        date=date,
                        wheels=wheels,
                    )
                )
                self.current_draw = None


def validate_draw(draw: Draw) -> None:
    wheel_names = tuple(result.wheel for result in draw.wheels)

    if wheel_names != EXPECTED_WHEELS:
        raise ValueError(
            f"Estrazione {draw.number}: ruote inattese.\n"
            f"Attese:    {EXPECTED_WHEELS}\n"
            f"Rilevate:  {wheel_names}"
        )

    for result in draw.wheels:
        if len(result.numbers) != 5:
            raise ValueError(
                f"Estrazione {draw.number}, ruota {result.wheel}: "
                f"rilevati {len(result.numbers)} numeri invece di 5."
            )

        if len(set(result.numbers)) != 5:
            raise ValueError(
                f"Estrazione {draw.number}, ruota {result.wheel}: "
                "numeri duplicati."
            )

        invalid_numbers = [
            number
            for number in result.numbers
            if not 1 <= number <= 90
        ]

        if invalid_numbers:
            raise ValueError(
                f"Estrazione {draw.number}, ruota {result.wheel}: "
                f"numeri fuori intervallo 1–90: {invalid_numbers}"
            )


def parse_archive(html: str) -> list[Draw]:
    parser = LottoArchiveParser()
    parser.feed(html)
    parser.close()

    unique_draws: dict[int, Draw] = {}

    for draw in parser.draws:
        validate_draw(draw)

        previous = unique_draws.get(draw.number)

        if previous is not None and previous != draw:
            raise ValueError(
                f"Estrazione {draw.number} presente più volte "
                "con contenuti differenti."
            )

        unique_draws[draw.number] = draw

    return sorted(
        unique_draws.values(),
        key=lambda draw: (draw.date, draw.number),
        reverse=True,
    )


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY,
            draw_number INTEGER NOT NULL UNIQUE
                CHECK (draw_number > 0),
            draw_date TEXT NOT NULL,
            source_url TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS wheels (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            sort_order INTEGER NOT NULL UNIQUE
                CHECK (sort_order BETWEEN 1 AND 11)
        );

        CREATE TABLE IF NOT EXISTS draw_numbers (
            draw_id INTEGER NOT NULL,
            wheel_id INTEGER NOT NULL,
            position INTEGER NOT NULL
                CHECK (position BETWEEN 1 AND 5),
            value INTEGER NOT NULL
                CHECK (value BETWEEN 1 AND 90),

            PRIMARY KEY (draw_id, wheel_id, position),
            UNIQUE (draw_id, wheel_id, value),

            FOREIGN KEY (draw_id)
                REFERENCES draws(id)
                ON DELETE CASCADE,

            FOREIGN KEY (wheel_id)
                REFERENCES wheels(id)
                ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_draws_date
            ON draws(draw_date DESC);

        CREATE INDEX IF NOT EXISTS idx_draw_numbers_value
            ON draw_numbers(value);

        DROP VIEW IF EXISTS v_draw_numbers;

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
    )


def import_draws(
    connection: sqlite3.Connection,
    draws: list[Draw],
    source_hash: str,
) -> None:
    imported_at = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    with connection:
        for sort_order, wheel_name in enumerate(
            EXPECTED_WHEELS,
            start=1,
        ):
            connection.execute(
                """
                INSERT INTO wheels(name, sort_order)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    sort_order = excluded.sort_order
                """,
                (wheel_name, sort_order),
            )

        selected_numbers = [draw.number for draw in draws]
        placeholders = ",".join("?" for _ in selected_numbers)

        connection.execute(
            f"""
            DELETE FROM draws
            WHERE draw_number NOT IN ({placeholders})
            """,
            selected_numbers,
        )

        wheel_ids = {
            name: wheel_id
            for wheel_id, name in connection.execute(
                "SELECT id, name FROM wheels"
            )
        }

        for draw in draws:
            connection.execute(
                """
                INSERT INTO draws(
                    draw_number,
                    draw_date,
                    source_url,
                    imported_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(draw_number) DO UPDATE SET
                    draw_date = excluded.draw_date,
                    source_url = excluded.source_url,
                    imported_at = excluded.imported_at
                """,
                (
                    draw.number,
                    draw.date,
                    SOURCE_URL,
                    imported_at,
                ),
            )

            draw_id = connection.execute(
                """
                SELECT id
                FROM draws
                WHERE draw_number = ?
                """,
                (draw.number,),
            ).fetchone()[0]

            connection.execute(
                "DELETE FROM draw_numbers WHERE draw_id = ?",
                (draw_id,),
            )

            for result in draw.wheels:
                wheel_id = wheel_ids[result.wheel]

                connection.executemany(
                    """
                    INSERT INTO draw_numbers(
                        draw_id,
                        wheel_id,
                        position,
                        value
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    [
                        (
                            draw_id,
                            wheel_id,
                            position,
                            value,
                        )
                        for position, value in enumerate(
                            result.numbers,
                            start=1,
                        )
                    ],
                )

        metadata = {
            "source_url": SOURCE_URL,
            "source_file": str(SOURCE_PATH),
            "source_sha256": source_hash,
            "imported_at_utc": imported_at,
            "import_limit": str(IMPORT_LIMIT),
            "first_draw_number": str(draws[-1].number),
            "last_draw_number": str(draws[0].number),
        }

        connection.executemany(
            """
            INSERT INTO metadata(key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value
            """,
            metadata.items(),
        )


def verify_database(connection: sqlite3.Connection) -> None:
    draw_count = connection.execute(
        "SELECT COUNT(*) FROM draws"
    ).fetchone()[0]

    wheel_count = connection.execute(
        "SELECT COUNT(*) FROM wheels"
    ).fetchone()[0]

    number_count = connection.execute(
        "SELECT COUNT(*) FROM draw_numbers"
    ).fetchone()[0]

    wheel_result_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT draw_id, wheel_id
            FROM draw_numbers
            GROUP BY draw_id, wheel_id
        )
        """
    ).fetchone()[0]

    expected_numbers = IMPORT_LIMIT * 11 * 5
    expected_wheel_results = IMPORT_LIMIT * 11

    if draw_count != IMPORT_LIMIT:
        raise ValueError(
            f"Database: attese {IMPORT_LIMIT} estrazioni, "
            f"trovate {draw_count}."
        )

    if wheel_count != 11:
        raise ValueError(
            f"Database: attese 11 ruote, trovate {wheel_count}."
        )

    if wheel_result_count != expected_wheel_results:
        raise ValueError(
            f"Database: attesi {expected_wheel_results} "
            f"risultati di ruota, trovati {wheel_result_count}."
        )

    if number_count != expected_numbers:
        raise ValueError(
            f"Database: attesi {expected_numbers} numeri, "
            f"trovati {number_count}."
        )

    print("===== VERIFICA DATABASE =====")
    print(f"Estrazioni:          {draw_count}")
    print(f"Ruote:               {wheel_count}")
    print(f"Risultati di ruota:  {wheel_result_count}")
    print(f"Numeri registrati:   {number_count}")
    print("Integrità SQLite:    ", end="")

    integrity = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    print(integrity)

    print("\n===== ESTRAZIONE PIÙ RECENTE =====")

    rows = connection.execute(
        """
        SELECT
            wheel,
            GROUP_CONCAT(value_padded, ' ')
        FROM (
            SELECT
                wheel,
                wheel_order,
                position,
                value_padded
            FROM v_draw_numbers
            WHERE draw_number = (
                SELECT MAX(draw_number)
                FROM draws
            )
            ORDER BY wheel_order, position
        )
        GROUP BY wheel, wheel_order
        ORDER BY wheel_order
        """
    ).fetchall()

    latest = connection.execute(
        """
        SELECT draw_number, draw_date
        FROM draws
        ORDER BY draw_date DESC, draw_number DESC
        LIMIT 1
        """
    ).fetchone()

    print(f"Concorso:            n. {latest[0]}")
    print(f"Data:                {latest[1]}")

    for wheel, numbers in rows:
        print(f"{wheel:<10} {numbers}")


def main() -> int:
    if not SOURCE_PATH.is_file():
        print(
            f"ERRORE: file sorgente assente: {SOURCE_PATH}",
            file=sys.stderr,
        )
        return 1

    html_bytes = SOURCE_PATH.read_bytes()
    html = html_bytes.decode("utf-8", errors="replace")
    source_hash = hashlib.sha256(html_bytes).hexdigest()

    all_draws = parse_archive(html)

    if len(all_draws) < IMPORT_LIMIT:
        raise ValueError(
            f"L'archivio contiene soltanto {len(all_draws)} "
            f"estrazioni valide; ne servono {IMPORT_LIMIT}."
        )

    selected_draws = all_draws[:IMPORT_LIMIT]

    selected_numbers = [draw.number for draw in selected_draws]
    expected_sequence = list(
        range(
            max(selected_numbers),
            min(selected_numbers) - 1,
            -1,
        )
    )

    if selected_numbers != expected_sequence:
        raise ValueError(
            "Le 60 estrazioni selezionate non formano "
            "una sequenza numerica continua."
        )

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        create_schema(connection)
        import_draws(connection, selected_draws, source_hash)
        verify_database(connection)
    finally:
        connection.close()

    print("\n===== IMPORTAZIONE COMPLETATA =====")
    print(f"Archivio analizzato: {len(all_draws)} estrazioni")
    print(
        "Intervallo importato: "
        f"n. {selected_draws[-1].number}–"
        f"{selected_draws[0].number}"
    )
    print(f"Database:            {DATABASE_PATH.resolve()}")
    print(f"SHA-256 sorgente:    {source_hash}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
