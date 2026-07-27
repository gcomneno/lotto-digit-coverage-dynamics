"""Enumeratore indipendente delle transizioni di copertura."""

from __future__ import annotations

import math
from collections import defaultdict
from functools import lru_cache
from typing import Iterable


DIGIT_COUNT = 10
ALL_DIGITS_MASK = (1 << DIGIT_COUNT) - 1
NUMBERS_PER_DRAW = 5
MIN_NUMBER = 1
MAX_NUMBER = 90
TOTAL_DRAW_COMBINATIONS = math.comb(
    MAX_NUMBER,
    NUMBERS_PER_DRAW,
)

DigitState = frozenset[int]


def number_digit_mask(number: int) -> int:
    """
    Restituisce la maschera delle cifre nella rappresentazione
    a due caratteri del numero.
    """

    if not MIN_NUMBER <= number <= MAX_NUMBER:
        raise ValueError(
            "Il numero deve essere compreso tra 1 e 90."
        )

    mask = 0

    for character in f"{number:02d}":
        mask |= 1 << int(character)

    return mask


def digits_to_mask(digits: Iterable[int]) -> int:
    mask = 0

    for digit in digits:
        if not isinstance(digit, int):
            raise TypeError(
                "Le cifre devono essere interi."
            )

        if not 0 <= digit < DIGIT_COUNT:
            raise ValueError(
                "Le cifre devono essere comprese tra 0 e 9."
            )

        mask |= 1 << digit

    return mask


def mask_to_state(mask: int) -> DigitState:
    if not isinstance(mask, int):
        raise TypeError(
            "La maschera deve essere un intero."
        )

    if not 0 <= mask <= ALL_DIGITS_MASK:
        raise ValueError(
            "Maschera di cifre non valida."
        )

    return frozenset(
        digit
        for digit in range(DIGIT_COUNT)
        if mask & (1 << digit)
    )


def all_digit_states() -> tuple[DigitState, ...]:
    return tuple(
        mask_to_state(mask)
        for mask in range(
            ALL_DIGITS_MASK + 1
        )
    )


@lru_cache(maxsize=1)
def draw_digit_mask_counts() -> tuple[
    tuple[int, int],
    ...,
]:
    """
    Conta esattamente quante cinquine producono ogni unione
    possibile di cifre.

    La DP processa i numeri 1–90 uno alla volta. Lo stato
    ``layers[k][mask]`` contiene il numero di modi per scegliere
    k numeri la cui unione di cifre è ``mask``.

    Non usa inclusione–esclusione e non enumera materialmente
    tutte le combinazioni.
    """

    layers: list[defaultdict[int, int]] = [
        defaultdict(int)
        for _ in range(
            NUMBERS_PER_DRAW + 1
        )
    ]

    layers[0][0] = 1

    for number in range(
        MIN_NUMBER,
        MAX_NUMBER + 1,
    ):
        digit_mask = number_digit_mask(number)

        for selected in range(
            NUMBERS_PER_DRAW - 1,
            -1,
            -1,
        ):
            current_layer = tuple(
                layers[selected].items()
            )

            for observed_mask, count in current_layer:
                layers[selected + 1][
                    observed_mask | digit_mask
                ] += count

    result = tuple(
        sorted(
            layers[NUMBERS_PER_DRAW].items()
        )
    )

    total = sum(
        count
        for _, count in result
    )

    if total != TOTAL_DRAW_COMBINATIONS:
        raise RuntimeError(
            "Conteggio incompleto delle cinquine: "
            f"{total} invece di "
            f"{TOTAL_DRAW_COMBINATIONS}."
        )

    return result


def transition_count_distribution(
    current_missing: Iterable[int],
) -> dict[DigitState, int]:
    """
    Distribuzione esatta, in conteggi interi, degli stati
    successivi.
    """

    current_mask = digits_to_mask(
        current_missing
    )

    counts: defaultdict[int, int] = (
        defaultdict(int)
    )

    for observed_mask, draw_count in (
        draw_digit_mask_counts()
    ):
        next_mask = (
            current_mask
            & ~observed_mask
            & ALL_DIGITS_MASK
        )

        counts[next_mask] += draw_count

    total = sum(counts.values())

    if total != TOTAL_DRAW_COMBINATIONS:
        raise RuntimeError(
            "Distribuzione di transizione incompleta: "
            f"{total} invece di "
            f"{TOTAL_DRAW_COMBINATIONS}."
        )

    return {
        mask_to_state(mask): count
        for mask, count in sorted(
            counts.items()
        )
    }


def transition_probability_distribution(
    current_missing: Iterable[int],
) -> dict[DigitState, float]:
    return {
        next_state: (
            count
            / TOTAL_DRAW_COMBINATIONS
        )
        for next_state, count
        in transition_count_distribution(
            current_missing
        ).items()
    }
