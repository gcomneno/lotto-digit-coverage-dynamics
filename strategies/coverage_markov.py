"""Catena di Markov esatta per la copertura delle cifre 0–9."""

from __future__ import annotations

import math
from functools import lru_cache
from itertools import combinations
from typing import Iterable

from strategies.coverage_completion import (
    digits_in_number,
    exact_completion_probability,
    normalize_digits,
)


DigitState = frozenset[int]
COMPLETE_STATE: DigitState = frozenset()
TOTAL_DRAW_COMBINATIONS = math.comb(90, 5)


def normalize_state(digits: Iterable[int]) -> DigitState:
    return frozenset(normalize_digits(digits))


@lru_cache(maxsize=None)
def probability_avoiding_digits(
    forbidden_digits: tuple[int, ...],
) -> float:
    """
    Probabilità che nessuno dei cinque numeri estratti
    contenga una delle cifre vietate.
    """

    forbidden = normalize_state(forbidden_digits)

    allowed_numbers = sum(
        digits_in_number(number).isdisjoint(forbidden)
        for number in range(1, 91)
    )

    if allowed_numbers < 5:
        return 0.0

    return (
        math.comb(allowed_numbers, 5)
        / TOTAL_DRAW_COMBINATIONS
    )


@lru_cache(maxsize=None)
def _transition_probability(
    current_tuple: tuple[int, ...],
    next_tuple: tuple[int, ...],
) -> float:
    current = normalize_state(current_tuple)
    next_state = normalize_state(next_tuple)

    if not next_state.issubset(current):
        raise ValueError(
            "Lo stato successivo deve essere un sottoinsieme "
            "dello stato corrente."
        )

    if not current:
        return 1.0

    required_present = tuple(
        sorted(current.difference(next_state))
    )

    probability = 0.0

    # Le cifre rimaste in next_state devono essere assenti.
    # Tutte quelle in required_present devono invece comparire.
    # L'inclusione-esclusione impone la presenza di queste ultime.
    for subset_size in range(len(required_present) + 1):
        for subset in combinations(
            required_present,
            subset_size,
        ):
            forbidden = tuple(
                sorted(
                    next_state.union(subset)
                )
            )

            term = probability_avoiding_digits(forbidden)

            probability += (
                term
                if subset_size % 2 == 0
                else -term
            )

    if abs(probability) < 1e-15:
        return 0.0

    if probability < 0.0 and probability > -1e-12:
        return 0.0

    if probability > 1.0 and probability < 1.0 + 1e-12:
        return 1.0

    return probability


def transition_probability(
    current_missing: Iterable[int],
    next_missing: Iterable[int],
) -> float:
    current = tuple(sorted(normalize_state(current_missing)))
    next_state = tuple(sorted(normalize_state(next_missing)))

    return _transition_probability(
        current,
        next_state,
    )


@lru_cache(maxsize=None)
def _transition_distribution(
    current_tuple: tuple[int, ...],
) -> tuple[tuple[DigitState, float], ...]:
    current = normalize_state(current_tuple)

    if not current:
        return ((COMPLETE_STATE, 1.0),)

    ordered = tuple(sorted(current))
    transitions: list[tuple[DigitState, float]] = []

    for size in range(len(ordered) + 1):
        for subset in combinations(ordered, size):
            next_state = frozenset(subset)
            probability = transition_probability(
                current,
                next_state,
            )

            if probability > 1e-15:
                transitions.append(
                    (next_state, probability)
                )

    total = sum(
        probability
        for _, probability in transitions
    )

    if not math.isclose(
        total,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise RuntimeError(
            "Distribuzione di transizione non normalizzata: "
            f"{total:.15f} per lo stato {sorted(current)}."
        )

    return tuple(transitions)


def transition_distribution(
    current_missing: Iterable[int],
) -> dict[DigitState, float]:
    current = tuple(sorted(normalize_state(current_missing)))

    return dict(
        _transition_distribution(current)
    )


@lru_cache(maxsize=None)
def _completion_probability_within(
    state_tuple: tuple[int, ...],
    draws: int,
) -> float:
    state = normalize_state(state_tuple)

    if draws < 0:
        raise ValueError(
            "Il numero di estrazioni non può essere negativo."
        )

    if not state:
        return 1.0

    if draws == 0:
        return 0.0

    return sum(
        probability
        * _completion_probability_within(
            tuple(sorted(next_state)),
            draws - 1,
        )
        for next_state, probability
        in _transition_distribution(tuple(sorted(state)))
    )


def completion_probability_within(
    missing_digits: Iterable[int],
    draws: int,
) -> float:
    state = tuple(sorted(normalize_state(missing_digits)))

    return _completion_probability_within(
        state,
        draws,
    )


@lru_cache(maxsize=None)
def _expected_remaining_draws(
    state_tuple: tuple[int, ...],
) -> float:
    state = normalize_state(state_tuple)

    if not state:
        return 0.0

    distribution = _transition_distribution(
        tuple(sorted(state))
    )

    self_probability = dict(distribution).get(
        state,
        0.0,
    )

    if self_probability >= 1.0:
        raise RuntimeError(
            f"Stato non assorbibile: {sorted(state)}."
        )

    expected_after_progress = sum(
        probability
        * _expected_remaining_draws(
            tuple(sorted(next_state))
        )
        for next_state, probability in distribution
        if next_state != state
    )

    return (
        1.0 + expected_after_progress
    ) / (
        1.0 - self_probability
    )


def expected_remaining_draws(
    missing_digits: Iterable[int],
) -> float:
    state = tuple(sorted(normalize_state(missing_digits)))

    return _expected_remaining_draws(state)


@lru_cache(maxsize=None)
def _second_moment_remaining_draws(
    state_tuple: tuple[int, ...],
) -> float:
    state = normalize_state(state_tuple)

    if not state:
        return 0.0

    distribution = _transition_distribution(
        tuple(sorted(state))
    )

    self_probability = dict(distribution).get(
        state,
        0.0,
    )

    if self_probability >= 1.0:
        raise RuntimeError(
            f"Stato non assorbibile: {sorted(state)}."
        )

    expected_after_next = sum(
        probability
        * _expected_remaining_draws(
            tuple(sorted(next_state))
        )
        for next_state, probability in distribution
    )

    second_moment_after_progress = sum(
        probability
        * _second_moment_remaining_draws(
            tuple(sorted(next_state))
        )
        for next_state, probability in distribution
        if next_state != state
    )

    return (
        1.0
        + 2.0 * expected_after_next
        + second_moment_after_progress
    ) / (
        1.0 - self_probability
    )


def second_moment_remaining_draws(
    missing_digits: Iterable[int],
) -> float:
    state = tuple(sorted(normalize_state(missing_digits)))

    return _second_moment_remaining_draws(state)


def variance_remaining_draws(
    missing_digits: Iterable[int],
) -> float:
    state = normalize_state(missing_digits)
    mean = expected_remaining_draws(state)
    second_moment = second_moment_remaining_draws(
        state
    )

    variance = second_moment - mean**2

    if abs(variance) < 1e-12:
        return 0.0

    if variance < 0.0:
        raise RuntimeError(
            "Varianza negativa oltre la tolleranza "
            f"per lo stato {sorted(state)}: "
            f"{variance:.15e}."
        )

    return variance


def absorption_probability_mass(
    missing_digits: Iterable[int],
    max_draws: int,
) -> dict[int, float]:
    state = normalize_state(missing_digits)

    if max_draws < 0:
        raise ValueError(
            "L'orizzonte massimo non può essere negativo."
        )

    if not state:
        return {0: 1.0}

    previous_cumulative = 0.0
    mass: dict[int, float] = {}

    for draw in range(1, max_draws + 1):
        cumulative = completion_probability_within(
            state,
            draw,
        )

        probability = (
            cumulative
            - previous_cumulative
        )

        if probability < 0.0:
            if probability > -1e-12:
                probability = 0.0
            else:
                raise RuntimeError(
                    "Massa di probabilità negativa "
                    f"allo step {draw} per lo stato "
                    f"{sorted(state)}."
                )

        mass[draw] = probability
        previous_cumulative = cumulative

    return mass


def absorption_quantiles(
    missing_digits: Iterable[int],
    probabilities: Iterable[float] = (
        0.50,
        0.90,
        0.95,
        0.99,
    ),
    *,
    max_draws: int = 1000,
) -> dict[float, int]:
    state = normalize_state(missing_digits)

    normalized_probabilities = tuple(
        sorted(
            {
                float(probability)
                for probability in probabilities
            }
        )
    )

    if any(
        probability <= 0.0
        or probability >= 1.0
        for probability in normalized_probabilities
    ):
        raise ValueError(
            "I quantili devono essere compresi "
            "strettamente tra zero e uno."
        )

    if max_draws <= 0:
        raise ValueError(
            "L'orizzonte massimo deve essere positivo."
        )

    if not state:
        return {
            probability: 0
            for probability
            in normalized_probabilities
        }

    result: dict[float, int] = {}

    for draw in range(1, max_draws + 1):
        cumulative = completion_probability_within(
            state,
            draw,
        )

        for probability in normalized_probabilities:
            if (
                probability not in result
                and cumulative >= probability
            ):
                result[probability] = draw

        if len(result) == len(
            normalized_probabilities
        ):
            return result

    missing = [
        probability
        for probability in normalized_probabilities
        if probability not in result
    ]

    raise RuntimeError(
        "Quantili non raggiunti entro "
        f"{max_draws} estrazioni per lo stato "
        f"{sorted(state)}: {missing}."
    )


def maturity_metrics(
    missing_digits: Iterable[int],
    horizons: Iterable[int] = (1, 2, 3, 5),
    quantiles: Iterable[float] = (
        0.50,
        0.90,
        0.95,
        0.99,
    ),
) -> dict[str, object]:
    state = normalize_state(missing_digits)
    normalized_horizons = tuple(sorted(set(horizons)))

    if any(horizon <= 0 for horizon in normalized_horizons):
        raise ValueError(
            "Gli orizzonti devono essere interi positivi."
        )

    return {
        "missing_digits": state,
        "one_step_probability": (
            exact_completion_probability(state)
        ),
        "completion_within": {
            horizon: completion_probability_within(
                state,
                horizon,
            )
            for horizon in normalized_horizons
        },
        "expected_remaining_draws": (
            expected_remaining_draws(state)
        ),
        "second_moment_remaining_draws": (
            second_moment_remaining_draws(state)
        ),
        "variance_remaining_draws": (
            variance_remaining_draws(state)
        ),
        "absorption_quantiles": (
            absorption_quantiles(
                state,
                quantiles,
            )
        ),
    }
