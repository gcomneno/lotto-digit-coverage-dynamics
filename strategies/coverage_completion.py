"""Stati e probabilità di completamento della copertura 0–9."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from typing import Iterable, Sequence

from strategies.digit_coverage import load_draws_by_wheel
from strategies.twin_digits import (
    DrawSnapshot,
    LottoRepository,
    split_digits,
)


ALL_DIGITS = frozenset(range(10))


@dataclass(frozen=True)
class CoverageCompletionObservation:
    wheel: str
    wheel_order: int
    cycle_number: int
    draws_in_cycle: int
    current_draw: int
    current_date: str
    target_draw: int
    target_date: str
    covered_digits: frozenset[int]
    missing_digits: frozenset[int]
    completed_next: bool


def digits_in_number(number: int) -> frozenset[int]:
    return frozenset(split_digits(number))


def digits_in_draw(draw: DrawSnapshot) -> frozenset[int]:
    digits: set[int] = set()

    for number in draw.numbers:
        digits.update(digits_in_number(number))

    return frozenset(digits)


def normalize_digits(digits: Iterable[int]) -> tuple[int, ...]:
    normalized = tuple(sorted(set(digits)))

    if any(digit not in range(10) for digit in normalized):
        raise ValueError("Le cifre devono appartenere all'intervallo 0–9.")

    return normalized


@lru_cache(maxsize=None)
def _completion_probability(
    missing_digits: tuple[int, ...],
) -> float:
    """
    Probabilità esatta che cinque numeri senza reinserimento
    contengano tutte le cifre richieste.

    Usa inclusione-esclusione sugli eventi:
    «la cifra richiesta non compare nella cinquina».
    """

    if not missing_digits:
        return 1.0

    total_combinations = math.comb(90, 5)
    probability = 0.0

    for subset_size in range(len(missing_digits) + 1):
        for subset in combinations(
            missing_digits,
            subset_size,
        ):
            forbidden = frozenset(subset)

            allowed_count = sum(
                digits_in_number(number).isdisjoint(forbidden)
                for number in range(1, 91)
            )

            combinations_without_subset = (
                math.comb(allowed_count, 5)
                if allowed_count >= 5
                else 0
            )

            term = (
                combinations_without_subset
                / total_combinations
            )

            probability += (
                term
                if subset_size % 2 == 0
                else -term
            )

    return probability


def exact_completion_probability(
    missing_digits: Iterable[int],
) -> float:
    return _completion_probability(
        normalize_digits(missing_digits)
    )


def build_completion_observations(
    draws: Sequence[DrawSnapshot],
    *,
    skip_initial_partial_cycle: bool = True,
) -> tuple[CoverageCompletionObservation, ...]:
    if len(draws) < 2:
        return ()

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    if any(draw.wheel != wheel for draw in draws):
        raise ValueError(
            "Le osservazioni non possono mescolare ruote."
        )

    ordered = tuple(
        sorted(
            draws,
            key=lambda draw: (
                draw.draw_date,
                draw.draw_number,
            ),
        )
    )

    covered: set[int] = set()
    draws_in_cycle = 0
    recording = not skip_initial_partial_cycle
    cycle_number = 1 if recording else 0
    observations: list[CoverageCompletionObservation] = []

    for index, current in enumerate(ordered[:-1]):
        covered.update(digits_in_draw(current))
        draws_in_cycle += 1

        if covered == ALL_DIGITS:
            covered.clear()
            draws_in_cycle = 0

            if recording:
                cycle_number += 1
            else:
                recording = True
                cycle_number = 1

            continue

        if not recording:
            continue

        target = ordered[index + 1]
        missing = ALL_DIGITS.difference(covered)
        target_digits = digits_in_draw(target)

        observations.append(
            CoverageCompletionObservation(
                wheel=wheel,
                wheel_order=wheel_order,
                cycle_number=cycle_number,
                draws_in_cycle=draws_in_cycle,
                current_draw=current.draw_number,
                current_date=current.draw_date,
                target_draw=target.draw_number,
                target_date=target.draw_date,
                covered_digits=frozenset(covered),
                missing_digits=missing,
                completed_next=missing.issubset(target_digits),
            )
        )

    return tuple(observations)


def collect_completion_observations(
    repository: LottoRepository,
) -> tuple[CoverageCompletionObservation, ...]:
    draws_by_wheel = load_draws_by_wheel(repository)
    observations: list[CoverageCompletionObservation] = []

    for draws in draws_by_wheel.values():
        observations.extend(
            build_completion_observations(draws)
        )

    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.target_date,
                observation.target_draw,
                observation.wheel_order,
            ),
        )
    )


@dataclass(frozen=True)
class CurrentCoverageState:
    """Stato del ciclo naturale dopo l'ultima estrazione disponibile."""

    wheel: str
    wheel_order: int
    latest_draw: int
    latest_date: str
    completed_cycles: int
    draws_in_cycle: int
    covered_digits: frozenset[int]
    missing_digits: frozenset[int]
    synchronized: bool
    most_present_digits: frozenset[int] = frozenset()


def current_coverage_state(
    draws: Sequence[DrawSnapshot],
) -> CurrentCoverageState:
    """
    Ricostruisce lo stato corrente del ciclo naturale.

    Lo stato diventa affidabile dopo la prima copertura completa
    osservata nell'archivio. Prima di quel momento il ciclo potrebbe
    essere iniziato fuori dal periodo disponibile.
    """

    if not draws:
        raise ValueError(
            "Servono almeno un'estrazione per ricostruire lo stato."
        )

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    if any(draw.wheel != wheel for draw in draws):
        raise ValueError(
            "Lo stato corrente non può mescolare ruote."
        )

    ordered = tuple(
        sorted(
            draws,
            key=lambda draw: (
                draw.draw_date,
                draw.draw_number,
            ),
        )
    )

    covered: set[int] = set()
    digit_occurrences = [0] * 10
    draws_in_cycle = 0
    completed_cycles = 0
    synchronized = False

    for draw in ordered:
        covered.update(digits_in_draw(draw))

        for number in draw.numbers:
            for digit in split_digits(number):
                digit_occurrences[digit] += 1

        draws_in_cycle += 1

        if covered == ALL_DIGITS:
            completed_cycles += 1
            synchronized = True
            covered.clear()
            digit_occurrences = [0] * 10
            draws_in_cycle = 0

    maximum_occurrences = max(
        digit_occurrences
    )
    most_present_digits = frozenset(
        digit
        for digit, occurrences
        in enumerate(digit_occurrences)
        if (
            occurrences == maximum_occurrences
            and occurrences > 0
        )
    )

    latest = ordered[-1]

    return CurrentCoverageState(
        wheel=wheel,
        wheel_order=wheel_order,
        latest_draw=latest.draw_number,
        latest_date=latest.draw_date,
        completed_cycles=completed_cycles,
        draws_in_cycle=draws_in_cycle,
        covered_digits=frozenset(covered),
        missing_digits=ALL_DIGITS.difference(covered),
        synchronized=synchronized,
        most_present_digits=most_present_digits,
    )
