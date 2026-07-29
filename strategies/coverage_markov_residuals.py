"""Validazione empirica dell'attesa residua del modello Markov."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from strategies.coverage_completion import (
    ALL_DIGITS,
    digits_in_draw,
)
from strategies.coverage_markov import expected_remaining_draws
from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
)


@dataclass(frozen=True)
class MarkovResidualObservation:
    wheel: str
    wheel_order: int
    current_draw: int
    current_date: str
    cycle_number: int
    draws_in_cycle: int
    missing_digits: frozenset[int]
    predicted_remaining: float
    actual_remaining: int


@dataclass(frozen=True)
class _CoverageSnapshot:
    index: int
    draw: DrawSnapshot
    cycle_number: int
    draws_in_cycle: int
    missing_digits: frozenset[int]


def build_residual_observations(
    draws: Sequence[DrawSnapshot],
) -> tuple[MarkovResidualObservation, ...]:
    """
    Confronta l'attesa Markov con la durata residua realmente osservata.

    Il primo ciclo viene usato soltanto per sincronizzare l'analisi.
    Uno stato è incluso solo se una successiva chiusura del ciclo è
    osservabile entro l'archivio.
    """

    if not draws:
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
    completed_cycles = 0
    synchronized = False

    completion_flags = [False] * len(ordered)
    snapshots: dict[int, _CoverageSnapshot] = {}

    for index, current in enumerate(ordered):
        covered.update(digits_in_draw(current))
        draws_in_cycle += 1

        completed = covered == ALL_DIGITS
        completion_flags[index] = completed

        if completed:
            completed_cycles += 1
            synchronized = True
            covered.clear()
            draws_in_cycle = 0

        if not synchronized:
            continue

        snapshots[index] = _CoverageSnapshot(
            index=index,
            draw=current,
            cycle_number=completed_cycles + 1,
            draws_in_cycle=draws_in_cycle,
            missing_digits=ALL_DIGITS.difference(covered),
        )

    next_completion_index: int | None = None
    reversed_observations: list[MarkovResidualObservation] = []

    for index in range(len(ordered) - 1, -1, -1):
        snapshot = snapshots.get(index)

        if (
            snapshot is not None
            and next_completion_index is not None
        ):
            actual_remaining = next_completion_index - index

            if actual_remaining <= 0:
                raise RuntimeError(
                    "Durata residua non positiva."
                )

            reversed_observations.append(
                MarkovResidualObservation(
                    wheel=wheel,
                    wheel_order=wheel_order,
                    current_draw=snapshot.draw.draw_number,
                    current_date=snapshot.draw.draw_date,
                    cycle_number=snapshot.cycle_number,
                    draws_in_cycle=snapshot.draws_in_cycle,
                    missing_digits=snapshot.missing_digits,
                    predicted_remaining=expected_remaining_draws(
                        snapshot.missing_digits
                    ),
                    actual_remaining=actual_remaining,
                )
            )

        # Lo stato registrato nel concorso di completamento appartiene
        # già al nuovo ciclo. Deve quindi puntare al completamento
        # successivo, non a quello appena avvenuto.
        if completion_flags[index]:
            next_completion_index = index

    return tuple(reversed(reversed_observations))


def collect_residual_observations(
    repository: LottoRepository,
) -> tuple[MarkovResidualObservation, ...]:
    observations: list[MarkovResidualObservation] = []

    for draws in load_draws_by_wheel(repository).values():
        observations.extend(
            build_residual_observations(draws)
        )

    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.current_date,
                observation.current_draw,
                observation.wheel_order,
            ),
        )
    )
