"""Analisi della copertura delle cifre 0–9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from strategies.twin_digits import (
    DrawSnapshot,
    LottoRepository,
    split_digits,
)


ALL_DIGITS = frozenset(range(10))


@dataclass(frozen=True)
class DigitCoverageWindow:
    """Copertura delle cifre in una finestra di estrazioni."""

    wheel: str
    wheel_order: int
    window_size: int
    draw_numbers: tuple[int, ...]
    start_date: str
    end_date: str
    digit_counts: tuple[int, ...]

    @property
    def present_digits(self) -> tuple[int, ...]:
        return tuple(
            digit
            for digit, count in enumerate(self.digit_counts)
            if count > 0
        )

    @property
    def missing_digits(self) -> tuple[int, ...]:
        return tuple(
            digit
            for digit, count in enumerate(self.digit_counts)
            if count == 0
        )

    @property
    def missing_count(self) -> int:
        return len(self.missing_digits)

    @property
    def total_digit_slots(self) -> int:
        return sum(self.digit_counts)


def count_all_digits(
    draws: Sequence[DrawSnapshot],
) -> tuple[int, ...]:
    """Conta tutte le cifre 0–9 presenti nelle estrazioni."""

    counts = [0] * 10

    for draw in draws:
        if len(draw.numbers) != 5:
            raise ValueError(
                f"Estrazione {draw.draw_number}, ruota {draw.wheel}: "
                f"attesi 5 numeri, trovati {len(draw.numbers)}."
            )

        for number in draw.numbers:
            tens, units = split_digits(number)
            counts[tens] += 1
            counts[units] += 1

    return tuple(counts)


def build_coverage_windows(
    draws: Sequence[DrawSnapshot],
    window_size: int,
) -> tuple[DigitCoverageWindow, ...]:
    """Crea tutte le finestre mobili consecutive della ruota."""

    if window_size <= 0:
        raise ValueError("window_size deve essere positivo")

    if not draws or len(draws) < window_size:
        return ()

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    for draw in draws:
        if draw.wheel != wheel:
            raise ValueError(
                "Una finestra di copertura non può mescolare ruote."
            )

        if draw.wheel_order != wheel_order:
            raise ValueError(
                "Ordine ruota incoerente nelle estrazioni."
            )

    windows: list[DigitCoverageWindow] = []

    for start_index in range(
        0,
        len(draws) - window_size + 1,
    ):
        selected = tuple(
            draws[start_index:start_index + window_size]
        )

        windows.append(
            DigitCoverageWindow(
                wheel=wheel,
                wheel_order=wheel_order,
                window_size=window_size,
                draw_numbers=tuple(
                    draw.draw_number
                    for draw in selected
                ),
                start_date=selected[0].draw_date,
                end_date=selected[-1].draw_date,
                digit_counts=count_all_digits(selected),
            )
        )

    return tuple(windows)


def load_draws_by_wheel(
    repository: LottoRepository,
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """Carica tutte le estrazioni ordinate per ruota e data."""

    rows = repository.connection.execute(
        """
        SELECT
            draw_number,
            draw_date,
            wheel,
            wheel_order,
            position,
            value
        FROM v_draw_numbers
        ORDER BY
            wheel_order,
            draw_date,
            draw_number,
            position
        """
    ).fetchall()

    grouped: dict[
        tuple[str, int, int, str],
        list[int],
    ] = {}

    wheel_ordering: dict[str, int] = {}

    for row in rows:
        wheel = str(row["wheel"])
        wheel_order = int(row["wheel_order"])

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
            raise RuntimeError(
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


def analyze_digit_coverage(
    repository: LottoRepository,
    max_window_size: int = 3,
) -> dict[int, tuple[DigitCoverageWindow, ...]]:
    """Analizza tutte le ruote per finestre da 1 a N."""

    if max_window_size <= 0:
        raise ValueError(
            "max_window_size deve essere positivo"
        )

    draws_by_wheel = load_draws_by_wheel(repository)

    result: dict[int, tuple[DigitCoverageWindow, ...]] = {}

    for window_size in range(1, max_window_size + 1):
        windows: list[DigitCoverageWindow] = []

        for draws in draws_by_wheel.values():
            windows.extend(
                build_coverage_windows(
                    draws,
                    window_size,
                )
            )

        result[window_size] = tuple(windows)

    return result
