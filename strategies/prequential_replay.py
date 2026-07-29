"""Replay prequentiale walk-forward su estrazioni storiche."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from strategies.coverage_completion import (
    current_coverage_state,
    digits_in_draw,
)
from strategies.coverage_markov import maturity_metrics
from strategies.prequential_validation import (
    DEFAULT_HORIZONS,
    normalize_horizons,
)
from strategies.lotto_repository import DrawSnapshot


@dataclass(frozen=True)
class PrequentialReplayObservation:
    target_draw: int
    target_date: str
    wheel: str
    wheel_order: int
    source_latest_draw: int
    source_latest_date: str
    cycle_age: int
    missing_digits: frozenset[int]
    completion_probability_within: tuple[
        tuple[int, float],
        ...
    ]
    expected_remaining_draws: float
    target_numbers: tuple[int, ...]
    target_digits: frozenset[int]
    completed: bool
    remaining_before_reset: frozenset[int]

    def probability(self, horizon: int) -> float:
        probabilities = dict(
            self.completion_probability_within
        )

        try:
            return probabilities[horizon]
        except KeyError as error:
            raise KeyError(
                f"Orizzonte non disponibile: {horizon}."
            ) from error


def _ordered_draws(
    draws: Sequence[DrawSnapshot],
) -> tuple[DrawSnapshot, ...]:
    return tuple(
        sorted(
            draws,
            key=lambda draw: (
                draw.draw_date,
                draw.draw_number,
            ),
        )
    )


def _validate_alignment(
    draws_by_wheel: Mapping[
        str,
        Sequence[DrawSnapshot],
    ],
) -> tuple[int, ...]:
    if not draws_by_wheel:
        raise ValueError(
            "Serve almeno una ruota."
        )

    reference_draws: tuple[int, ...] | None = None

    for wheel, draws in draws_by_wheel.items():
        if not draws:
            raise ValueError(
                f"Nessuna estrazione per la ruota {wheel}."
            )

        draw_numbers = tuple(
            draw.draw_number
            for draw in _ordered_draws(draws)
        )

        if len(draw_numbers) != len(set(draw_numbers)):
            raise ValueError(
                f"Concorsi duplicati per la ruota {wheel}."
            )

        if reference_draws is None:
            reference_draws = draw_numbers
        elif draw_numbers != reference_draws:
            raise ValueError(
                "Le ruote non sono allineate sugli stessi concorsi."
            )

    if reference_draws is None:
        raise RuntimeError(
            "Impossibile determinare i concorsi disponibili."
        )

    return reference_draws


def build_prequential_replay(
    draws_by_wheel: Mapping[
        str,
        Sequence[DrawSnapshot],
    ],
    *,
    start_target: int,
    end_target: int | None = None,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> tuple[PrequentialReplayObservation, ...]:
    """
    Ricostruisce previsioni walk-forward senza utilizzare il target.

    Per ogni concorso T, lo stato viene calcolato esclusivamente sulle
    estrazioni precedenti a T. L'estrazione T viene letta soltanto dopo
    il congelamento logico delle metriche.
    """

    if start_target <= 0:
        raise ValueError(
            "Il concorso iniziale deve essere positivo."
        )

    normalized_horizons = normalize_horizons(horizons)
    available_draws = _validate_alignment(draws_by_wheel)

    maximum_draw = available_draws[-1]

    if end_target is None:
        end_target = maximum_draw

    if end_target < start_target:
        raise ValueError(
            "Il concorso finale precede quello iniziale."
        )

    targets = tuple(
        draw_number
        for draw_number in available_draws
        if start_target <= draw_number <= end_target
    )

    if not targets:
        raise ValueError(
            "Nessun concorso disponibile nell'intervallo richiesto."
        )

    observations: list[PrequentialReplayObservation] = []

    for wheel, draws in draws_by_wheel.items():
        ordered = _ordered_draws(draws)

        index_by_draw = {
            draw.draw_number: index
            for index, draw in enumerate(ordered)
        }

        for target_draw in targets:
            target_index = index_by_draw[target_draw]

            if target_index == 0:
                raise ValueError(
                    f"Nessuno storico precedente al concorso "
                    f"{target_draw} per {wheel}."
                )

            source_draws = ordered[:target_index]
            target = ordered[target_index]
            source_latest = source_draws[-1]

            state = current_coverage_state(source_draws)

            if not state.synchronized:
                raise ValueError(
                    f"Ciclo non sincronizzato per {wheel} "
                    f"prima del concorso {target_draw}."
                )

            if state.latest_draw != source_latest.draw_number:
                raise RuntimeError(
                    "Lo stato include un concorso inatteso."
                )

            if state.latest_draw >= target_draw:
                raise RuntimeError(
                    "Rilevata contaminazione dal futuro."
                )

            metrics = maturity_metrics(
                state.missing_digits,
                horizons=normalized_horizons,
            )

            completion = metrics[
                "completion_within"
            ]

            target_digit_set = digits_in_draw(target)
            completed = state.missing_digits.issubset(
                target_digit_set
            )

            remaining = state.missing_digits.difference(
                target_digit_set
            )

            observations.append(
                PrequentialReplayObservation(
                    target_draw=target.draw_number,
                    target_date=target.draw_date,
                    wheel=wheel,
                    wheel_order=state.wheel_order,
                    source_latest_draw=state.latest_draw,
                    source_latest_date=state.latest_date,
                    cycle_age=state.draws_in_cycle,
                    missing_digits=state.missing_digits,
                    completion_probability_within=tuple(
                        (
                            horizon,
                            completion[horizon],
                        )
                        for horizon in normalized_horizons
                    ),
                    expected_remaining_draws=metrics[
                        "expected_remaining_draws"
                    ],
                    target_numbers=tuple(target.numbers),
                    target_digits=target_digit_set,
                    completed=completed,
                    remaining_before_reset=remaining,
                )
            )

    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.target_draw,
                observation.wheel_order,
            ),
        )
    )
