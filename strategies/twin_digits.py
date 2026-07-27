"""Strategia basata sulle cifre che compongono i numeri gemelli."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


TWIN_NUMBERS = frozenset({11, 22, 33, 44, 55, 66, 77, 88})

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


@dataclass(frozen=True)
class TwinEvent:
    """Presenza di un numero gemello in una specifica estrazione e ruota."""

    draw_number: int
    draw_date: str
    wheel: str
    wheel_order: int
    position: int
    twin_number: int

    @property
    def digit(self) -> int:
        return self.twin_number // 11


@dataclass(frozen=True)
class DigitCount:
    """Conteggi della cifra cercata in un insieme di numeri."""

    digit_occurrences: int
    numbers_with_digit: int


@dataclass(frozen=True)
class WindowAnalysis:
    """Analisi cumulativa delle precedenti N estrazioni."""

    window_size: int
    window_mode: str
    available_draws: int
    digit_counts: tuple[int, ...]
    digit_occurrences: int
    numbers_with_digit: int
    draws_with_digit: int
    digit_slots: int
    digit_rate: float
    missing_digit_slots: int
    draws: tuple[DrawSnapshot, ...]

    @property
    def is_complete(self) -> bool:
        required_draws = (
            self.window_size
            if self.window_mode == "cumulative"
            else 1
        )

        return self.available_draws == required_draws


@dataclass(frozen=True)
class TwinAnalysis:
    event: TwinEvent
    windows: tuple[WindowAnalysis, ...]


def format_number(value: int) -> str:
    """Rappresenta ogni numero del Lotto come coppia di cifre."""

    if not 1 <= value <= 90:
        raise ValueError(
            f"Numero del Lotto fuori intervallo 1–90: {value}"
        )

    return f"{value:02d}"


def split_digits(value: int) -> tuple[int, int]:
    """Scompone un numero nelle sue due cifre, includendo lo zero iniziale."""

    formatted = format_number(value)
    return int(formatted[0]), int(formatted[1])


def is_twin_number(value: int) -> bool:
    return value in TWIN_NUMBERS


def count_digit_in_numbers(
    numbers: Iterable[int],
    digit: int,
) -> DigitCount:
    """Conta occorrenze e numeri contenenti la cifra specificata."""

    if not 0 <= digit <= 9:
        raise ValueError(f"Cifra fuori intervallo 0–9: {digit}")

    occurrences = 0
    numbers_with_digit = 0

    for number in numbers:
        digits = split_digits(number)
        count = digits.count(digit)

        occurrences += count

        if count > 0:
            numbers_with_digit += 1

    return DigitCount(
        digit_occurrences=occurrences,
        numbers_with_digit=numbers_with_digit,
    )


def count_all_digits_in_numbers(
    numbers: Iterable[int],
) -> tuple[int, ...]:
    """Conta le presenze di ciascuna cifra da 0 a 9."""

    counts = [0] * 10

    for number in numbers:
        for digit in split_digits(number):
            counts[digit] += 1

    return tuple(counts)



def rank_digit_by_presence(
    digit_counts: Sequence[int],
    digit: int,
) -> float:
    """Calcola il rango medio della cifra tra le cifre 1–8.

    La posizione 1 indica la presenza più alta.

    Esempio:
    se tre cifre sono prime a pari merito, occupano idealmente
    le posizioni 1, 2 e 3 e ricevono tutte rango medio 2.0.
    """

    if len(digit_counts) < 10:
        raise ValueError(
            "digit_counts deve contenere le cifre da 0 a 9"
        )

    if digit not in range(1, 9):
        raise ValueError(
            "La classifica ammette soltanto cifre da 1 a 8"
        )

    target_presence = digit_counts[digit]

    greater_count = sum(
        1
        for compared_digit in range(1, 9)
        if digit_counts[compared_digit] > target_presence
    )

    equal_count = sum(
        1
        for compared_digit in range(1, 9)
        if digit_counts[compared_digit] == target_presence
    )

    return greater_count + (equal_count + 1) / 2


def analyze_event_windows(
    event: TwinEvent,
    previous_draws: Sequence[DrawSnapshot],
    lookback: int = 6,
    window_mode: str = "cumulative",
) -> TwinAnalysis:
    """Costruisce finestre cumulative oppure singole.

    cumulative:
        -3 comprende le precedenti estrazioni -1, -2 e -3.

    single:
        -3 considera soltanto la terza estrazione precedente.
    """

    if lookback <= 0:
        raise ValueError("lookback deve essere maggiore di zero")

    if window_mode not in {"cumulative", "single"}:
        raise ValueError(
            "window_mode deve essere 'cumulative' oppure 'single'"
        )

    windows: list[WindowAnalysis] = []

    for window_size in range(1, lookback + 1):
        if window_mode == "cumulative":
            selected_draws = tuple(
                previous_draws[:window_size]
            )
        else:
            selected_draws = tuple(
                previous_draws[
                    window_size - 1:window_size
                ]
            )

        all_digit_counts = [0] * 10
        digit_occurrences = 0
        numbers_with_digit = 0
        draws_with_digit = 0

        for draw in selected_draws:
            draw_digit_counts = count_all_digits_in_numbers(
                draw.numbers
            )

            for digit, occurrences in enumerate(
                draw_digit_counts
            ):
                all_digit_counts[digit] += occurrences

            count = count_digit_in_numbers(
                draw.numbers,
                event.digit,
            )

            digit_occurrences += count.digit_occurrences
            numbers_with_digit += count.numbers_with_digit

            if count.digit_occurrences > 0:
                draws_with_digit += 1

        available_draws = len(selected_draws)
        digit_slots = available_draws * 5 * 2

        digit_rate = (
            digit_occurrences / digit_slots
            if digit_slots > 0
            else 0.0
        )

        windows.append(
            WindowAnalysis(
                window_size=window_size,
                window_mode=window_mode,
                available_draws=available_draws,
                digit_counts=tuple(all_digit_counts),
                digit_occurrences=digit_occurrences,
                numbers_with_digit=numbers_with_digit,
                draws_with_digit=draws_with_digit,
                digit_slots=digit_slots,
                digit_rate=digit_rate,
                missing_digit_slots=(
                    digit_slots - digit_occurrences
                ),
                draws=selected_draws,
            )
        )

    return TwinAnalysis(
        event=event,
        windows=tuple(windows),
    )


class LottoRepository:
    """Accesso in sola lettura al database delle estrazioni."""

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

        columns = {row["name"] for row in rows}
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

        return int(row["draw_number"]), str(row["draw_date"])

    def twin_events_for_draw(
        self,
        draw_number: int,
    ) -> tuple[TwinEvent, ...]:
        twins = sorted(TWIN_NUMBERS)
        placeholders = ",".join("?" for _ in twins)

        rows = self.connection.execute(
            f"""
            SELECT
                draw_number,
                draw_date,
                wheel,
                wheel_order,
                position,
                value
            FROM v_draw_numbers
            WHERE draw_number = ?
              AND value IN ({placeholders})
            ORDER BY wheel_order, position
            """,
            (draw_number, *twins),
        ).fetchall()

        return tuple(
            TwinEvent(
                draw_number=int(row["draw_number"]),
                draw_date=str(row["draw_date"]),
                wheel=str(row["wheel"]),
                wheel_order=int(row["wheel_order"]),
                position=int(row["position"]),
                twin_number=int(row["value"]),
            )
            for row in rows
        )

    def all_twin_events(self) -> tuple[TwinEvent, ...]:
        twins = sorted(TWIN_NUMBERS)
        placeholders = ",".join("?" for _ in twins)

        rows = self.connection.execute(
            f"""
            SELECT
                draw_number,
                draw_date,
                wheel,
                wheel_order,
                position,
                value
            FROM v_draw_numbers
            WHERE value IN ({placeholders})
            ORDER BY
                draw_date,
                draw_number,
                wheel_order,
                position
            """,
            twins,
        ).fetchall()

        return tuple(
            TwinEvent(
                draw_number=int(row["draw_number"]),
                draw_date=str(row["draw_date"]),
                wheel=str(row["wheel"]),
                wheel_order=int(row["wheel_order"]),
                position=int(row["position"]),
                twin_number=int(row["value"]),
            )
            for row in rows
        )

    def previous_draws_for_event(
        self,
        event: TwinEvent,
        limit: int,
    ) -> tuple[DrawSnapshot, ...]:
        """Recupera le precedenti estrazioni esclusivamente sulla stessa ruota."""

        if limit <= 0:
            raise ValueError("limit deve essere maggiore di zero")

        rows = self.connection.execute(
            """
            SELECT
                draw_number,
                draw_date,
                wheel,
                wheel_order,
                position,
                value
            FROM v_draw_numbers
            WHERE wheel = ?
              AND (
                    draw_date < ?
                    OR (
                        draw_date = ?
                        AND draw_number < ?
                    )
              )
            ORDER BY
                draw_date DESC,
                draw_number DESC,
                position
            """,
            (
                event.wheel,
                event.draw_date,
                event.draw_date,
                event.draw_number,
            ),
        ).fetchall()

        grouped: dict[
            tuple[int, str, str, int],
            list[int],
        ] = {}

        for row in rows:
            key = (
                int(row["draw_number"]),
                str(row["draw_date"]),
                str(row["wheel"]),
                int(row["wheel_order"]),
            )

            grouped.setdefault(key, []).append(
                int(row["value"])
            )

        snapshots: list[DrawSnapshot] = []

        for (
            draw_number,
            draw_date,
            wheel,
            wheel_order,
        ), numbers in grouped.items():
            if len(numbers) != 5:
                raise RuntimeError(
                    f"Estrazione {draw_number}, ruota {wheel}: "
                    f"attesi 5 numeri, trovati {len(numbers)}."
                )

            snapshots.append(
                DrawSnapshot(
                    draw_number=draw_number,
                    draw_date=draw_date,
                    wheel=wheel,
                    wheel_order=wheel_order,
                    numbers=tuple(numbers),
                )
            )

            if len(snapshots) == limit:
                break

        return tuple(snapshots)


def analyze_latest(
    repository: LottoRepository,
    lookback: int = 6,
    window_mode: str = "cumulative",
) -> tuple[TwinAnalysis, ...]:
    draw_number, _ = repository.latest_draw()
    events = repository.twin_events_for_draw(draw_number)

    analyses: list[TwinAnalysis] = []

    for event in events:
        previous_draws = repository.previous_draws_for_event(
            event,
            limit=lookback,
        )

        analyses.append(
            analyze_event_windows(
                event,
                previous_draws,
                lookback=lookback,
                window_mode=window_mode,
            )
        )

    return tuple(analyses)
