"""Osservazioni empiriche per validare il modello Markov di copertura."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from strategies.coverage_completion import (
    ALL_DIGITS,
    digits_in_draw,
)
from strategies.coverage_markov import (
    completion_probability_within,
)
from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
)


@dataclass(frozen=True)
class MarkovCalibrationObservation:
    wheel: str
    wheel_order: int
    current_draw: int
    current_date: str
    draws_in_cycle: int
    missing_digits: frozenset[int]
    horizon: int
    predicted_probability: float
    completed_within: bool


def normalize_horizons(
    horizons: Iterable[int],
) -> tuple[int, ...]:
    normalized = tuple(
        sorted(set(horizons))
    )

    if not normalized:
        raise ValueError(
            "Serve almeno un orizzonte."
        )

    if any(horizon <= 0 for horizon in normalized):
        raise ValueError(
            "Gli orizzonti devono essere interi positivi."
        )

    return normalized


def build_calibration_observations(
    draws: Sequence[DrawSnapshot],
    horizons: Iterable[int] = (1, 2, 3, 5),
) -> tuple[MarkovCalibrationObservation, ...]:
    """
    Costruisce osservazioni con gestione della censura a destra.

    Dopo la prima copertura completa osservata, ogni stato è affidabile.
    Se il ciclo si completa entro l'orizzonte, l'esito è noto anche
    quando restano meno di `horizon` estrazioni nell'archivio.
    Un mancato completamento è invece registrato soltanto quando sono
    disponibili tutte le estrazioni richieste dall'orizzonte.
    """

    normalized_horizons = normalize_horizons(horizons)

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
    synchronized = False
    observations: list[MarkovCalibrationObservation] = []

    for index, current in enumerate(ordered):
        covered.update(digits_in_draw(current))
        draws_in_cycle += 1

        if covered == ALL_DIGITS:
            synchronized = True
            covered.clear()
            draws_in_cycle = 0

        if not synchronized:
            continue

        missing = ALL_DIGITS.difference(covered)

        for horizon in normalized_horizons:
            future = ordered[
                index + 1:
                index + 1 + horizon
            ]

            if not future:
                continue

            future_covered = set(covered)
            completed = False

            for future_draw in future:
                future_covered.update(
                    digits_in_draw(future_draw)
                )

                if future_covered == ALL_DIGITS:
                    completed = True
                    break

            fully_observed = len(future) == horizon

            if not completed and not fully_observed:
                continue

            observations.append(
                MarkovCalibrationObservation(
                    wheel=wheel,
                    wheel_order=wheel_order,
                    current_draw=current.draw_number,
                    current_date=current.draw_date,
                    draws_in_cycle=draws_in_cycle,
                    missing_digits=missing,
                    horizon=horizon,
                    predicted_probability=(
                        completion_probability_within(
                            missing,
                            horizon,
                        )
                    ),
                    completed_within=completed,
                )
            )

    return tuple(observations)


def collect_calibration_observations(
    repository: LottoRepository,
    horizons: Iterable[int] = (1, 2, 3, 5),
) -> tuple[MarkovCalibrationObservation, ...]:
    observations: list[MarkovCalibrationObservation] = []

    for draws in load_draws_by_wheel(repository).values():
        observations.extend(
            build_calibration_observations(
                draws,
                horizons=horizons,
            )
        )

    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.horizon,
                observation.current_date,
                observation.current_draw,
                observation.wheel_order,
            ),
        )
    )
