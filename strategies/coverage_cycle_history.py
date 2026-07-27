"""Ricostruzione dei cicli storici completi di copertura."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from strategies.coverage_completion import (
    ALL_DIGITS,
    digits_in_draw,
)
from strategies.twin_digits import DrawSnapshot


@dataclass(frozen=True)
class CompletedCoverageCycle:
    """Ciclo naturale interamente osservato."""

    wheel: str
    wheel_order: int
    cycle_number: int
    start_draw: int
    start_date: str
    end_draw: int
    end_date: str
    draws_in_cycle: int


@dataclass(frozen=True)
class WheelCoverageHistory:
    """Cicli ricostruiti per una singola ruota."""

    wheel: str
    wheel_order: int
    first_draw: int
    first_date: str
    last_draw: int
    last_date: str
    synchronized: bool
    initial_left_censored_draws: int
    completed_cycles: tuple[
        CompletedCoverageCycle,
        ...,
    ]
    right_censored_draws: int
    right_censored_missing_digits: frozenset[int]


def _ordered_single_wheel_draws(
    draws: Sequence[DrawSnapshot],
) -> tuple[DrawSnapshot, ...]:
    if not draws:
        raise ValueError(
            "Servono estrazioni per ricostruire "
            "la cronologia di una ruota."
        )

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    for draw in draws:
        if draw.wheel != wheel:
            raise ValueError(
                "Una cronologia non può mescolare ruote."
            )

        if draw.wheel_order != wheel_order:
            raise ValueError(
                "Ordine ruota incoerente nella cronologia."
            )

        if len(draw.numbers) != 5:
            raise ValueError(
                f"Estrazione {draw.draw_number}, "
                f"ruota {draw.wheel}: "
                f"attesi 5 numeri, trovati "
                f"{len(draw.numbers)}."
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

    seen: set[tuple[str, int]] = set()

    for draw in ordered:
        key = (
            draw.draw_date,
            draw.draw_number,
        )

        if key in seen:
            raise ValueError(
                "Estrazione duplicata per la ruota "
                f"{wheel}: data {draw.draw_date}, "
                f"numero {draw.draw_number}."
            )

        seen.add(key)

    return ordered


def build_wheel_cycle_history(
    draws: Sequence[DrawSnapshot],
) -> WheelCoverageHistory:
    """
    Ricostruisce soltanto i cicli interamente osservati.

    Il tratto iniziale viene escluso fino alla prima
    copertura completa, perché il ciclo potrebbe essere
    iniziato prima dell'archivio.

    Il ciclo finale incompleto viene registrato come
    censurato a destra, ma non incluso tra le durate
    complete.
    """

    ordered = _ordered_single_wheel_draws(draws)

    wheel = ordered[0].wheel
    wheel_order = ordered[0].wheel_order

    covered: set[int] = set()
    cycle_draws: list[DrawSnapshot] = []
    completed_cycles: list[
        CompletedCoverageCycle
    ] = []

    synchronized = False
    initial_left_censored_draws = 0

    for draw in ordered:
        cycle_draws.append(draw)
        covered.update(digits_in_draw(draw))

        if covered != ALL_DIGITS:
            continue

        if synchronized:
            first = cycle_draws[0]

            completed_cycles.append(
                CompletedCoverageCycle(
                    wheel=wheel,
                    wheel_order=wheel_order,
                    cycle_number=(
                        len(completed_cycles) + 1
                    ),
                    start_draw=first.draw_number,
                    start_date=first.draw_date,
                    end_draw=draw.draw_number,
                    end_date=draw.draw_date,
                    draws_in_cycle=len(cycle_draws),
                )
            )
        else:
            synchronized = True
            initial_left_censored_draws = len(
                cycle_draws
            )

        covered.clear()
        cycle_draws.clear()

    if synchronized:
        right_censored_draws = len(cycle_draws)
        right_censored_missing_digits = (
            ALL_DIGITS.difference(covered)
        )
    else:
        initial_left_censored_draws = len(ordered)
        right_censored_draws = 0
        right_censored_missing_digits = (
            frozenset()
        )

    first = ordered[0]
    last = ordered[-1]

    return WheelCoverageHistory(
        wheel=wheel,
        wheel_order=wheel_order,
        first_draw=first.draw_number,
        first_date=first.draw_date,
        last_draw=last.draw_number,
        last_date=last.draw_date,
        synchronized=synchronized,
        initial_left_censored_draws=(
            initial_left_censored_draws
        ),
        completed_cycles=tuple(completed_cycles),
        right_censored_draws=right_censored_draws,
        right_censored_missing_digits=(
            right_censored_missing_digits
        ),
    )


def merge_draws_by_wheel(
    collections: Sequence[
        Mapping[
            str,
            Sequence[DrawSnapshot],
        ]
    ],
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """
    Unisce archivi consecutivi preservando i confini annuali.

    Il numero progressivo dell'estrazione può ripartire da
    uno a gennaio; l'identità storica usa quindi la coppia
    data e numero.
    """

    merged: dict[str, list[DrawSnapshot]] = {}
    wheel_orders: dict[str, int] = {}

    for collection in collections:
        for wheel, draws in collection.items():
            for draw in draws:
                if draw.wheel != wheel:
                    raise ValueError(
                        "La chiave della raccolta non "
                        "corrisponde alla ruota "
                        f"dell'estrazione: {wheel} / "
                        f"{draw.wheel}."
                    )

                previous_order = wheel_orders.get(
                    wheel
                )

                if (
                    previous_order is not None
                    and previous_order
                    != draw.wheel_order
                ):
                    raise ValueError(
                        "Ordine ruota incoerente tra "
                        f"gli archivi per {wheel}."
                    )

                wheel_orders[wheel] = (
                    draw.wheel_order
                )

                merged.setdefault(
                    wheel,
                    [],
                ).append(draw)

    histories: dict[
        str,
        tuple[DrawSnapshot, ...],
    ] = {}

    for wheel, draws in merged.items():
        histories[wheel] = (
            _ordered_single_wheel_draws(draws)
        )

    return {
        wheel: histories[wheel]
        for wheel in sorted(
            histories,
            key=lambda name: wheel_orders[name],
        )
    }


def flatten_completed_cycles(
    histories: Sequence[WheelCoverageHistory],
) -> tuple[CompletedCoverageCycle, ...]:
    cycles = [
        cycle
        for history in histories
        for cycle in history.completed_cycles
    ]

    return tuple(
        sorted(
            cycles,
            key=lambda cycle: (
                cycle.end_date,
                cycle.end_draw,
                cycle.wheel_order,
                cycle.cycle_number,
            ),
        )
    )
