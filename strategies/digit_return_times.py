"""Tempi di ritorno e rischio condizionato delle singole cifre."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
    split_digits,
)


DigitPosition = Literal["any", "tens", "units"]
POSITIONS: tuple[DigitPosition, ...] = (
    "any",
    "tens",
    "units",
)


@dataclass(frozen=True)
class DigitReturnObservation:
    """Esito successivo dopo una sequenza di assenze."""

    wheel: str
    wheel_order: int
    digit: int
    position: DigitPosition
    absence_streak: int
    target_draw: int
    target_date: str
    hit: bool


def validate_digit(digit: int) -> None:
    if digit not in range(10):
        raise ValueError(
            f"Cifra non valida: {digit}. Atteso 0–9."
        )


def validate_position(position: str) -> DigitPosition:
    if position not in POSITIONS:
        raise ValueError(
            f"Posizione non valida: {position!r}. "
            f"Valori ammessi: {', '.join(POSITIONS)}."
        )

    return position  # type: ignore[return-value]


def number_contains_digit(
    number: int,
    digit: int,
    position: DigitPosition,
) -> bool:
    validate_digit(digit)
    validate_position(position)

    tens, units = split_digits(number)

    if position == "tens":
        return tens == digit

    if position == "units":
        return units == digit

    return digit in (tens, units)


def draw_contains_digit(
    draw: DrawSnapshot,
    digit: int,
    position: DigitPosition,
) -> bool:
    return any(
        number_contains_digit(
            number,
            digit,
            position,
        )
        for number in draw.numbers
    )


def matching_numbers(
    digit: int,
    position: DigitPosition,
) -> tuple[int, ...]:
    """Numeri 1–90 che contengono la cifra nella posizione richiesta."""

    validate_digit(digit)
    validate_position(position)

    return tuple(
        number
        for number in range(1, 91)
        if number_contains_digit(
            number,
            digit,
            position,
        )
    )


def theoretical_hit_probability(
    digit: int,
    position: DigitPosition,
) -> float:
    """
    Probabilità che almeno uno dei cinque numeri estratti
    contenga la cifra nella posizione richiesta.
    """

    matching_count = len(
        matching_numbers(
            digit,
            position,
        )
    )

    return 1.0 - (
        math.comb(90 - matching_count, 5)
        / math.comb(90, 5)
    )


def build_return_observations(
    draws: Sequence[DrawSnapshot],
    position: DigitPosition,
) -> tuple[DigitReturnObservation, ...]:
    """
    Costruisce la funzione di rischio empirica.

    Se una cifra manca consecutivamente:
    - dopo la prima assenza, la seconda estrazione è osservata con k=1;
    - se manca ancora, la terza è osservata con k=2;
    - e così via fino alla ricomparsa o alla fine dell'archivio.
    """

    validate_position(position)

    if not draws:
        return ()

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    if any(draw.wheel != wheel for draw in draws):
        raise ValueError(
            "Le osservazioni non possono mescolare ruote."
        )

    ordered_draws = tuple(
        sorted(
            draws,
            key=lambda draw: (
                draw.draw_date,
                draw.draw_number,
            ),
        )
    )

    observations: list[DigitReturnObservation] = []

    for digit in range(10):
        absence_streak = 0

        for draw in ordered_draws:
            present = draw_contains_digit(
                draw,
                digit,
                position,
            )

            if absence_streak > 0:
                observations.append(
                    DigitReturnObservation(
                        wheel=wheel,
                        wheel_order=wheel_order,
                        digit=digit,
                        position=position,
                        absence_streak=absence_streak,
                        target_draw=draw.draw_number,
                        target_date=draw.draw_date,
                        hit=present,
                    )
                )

            if present:
                absence_streak = 0
            else:
                absence_streak += 1

    return tuple(observations)


def collect_return_observations(
    repository: LottoRepository,
    positions: Sequence[DigitPosition] = POSITIONS,
) -> tuple[DigitReturnObservation, ...]:
    """Carica tutte le osservazioni per ruota e posizione."""

    normalized_positions = tuple(
        validate_position(position)
        for position in positions
    )

    draws_by_wheel = load_draws_by_wheel(repository)
    observations: list[DigitReturnObservation] = []

    for draws in draws_by_wheel.values():
        for position in normalized_positions:
            observations.extend(
                build_return_observations(
                    draws,
                    position,
                )
            )

    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.position,
                observation.digit,
                observation.wheel_order,
                observation.target_date,
                observation.target_draw,
            ),
        )
    )
