"""Backtest walk-forward delle cifre mancanti intercettate."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence

from strategies.coverage_completion import (
    current_coverage_state,
    digits_in_draw,
)
from strategies.coverage_markov import (
    maturity_metrics,
    transition_distribution,
)
from strategies.lotto_repository import DrawSnapshot


def required_hit_count(missing_count: int) -> int:
    """Restituisce la soglia N-1, con minimo pari a uno."""

    if (
        not isinstance(missing_count, int)
        or isinstance(missing_count, bool)
        or missing_count <= 0
    ):
        raise ValueError(
            "missing_count deve essere un intero positivo."
        )

    return max(1, missing_count - 1)


def theoretical_threshold_probability(
    missing_digits: frozenset[int],
) -> float:
    """
    Probabilità esatta di intercettare la soglia richiesta.

    Somma la massa delle transizioni nelle quali il numero
    di cifre mancanti eliminate è almeno max(1, N-1).
    """

    if not missing_digits:
        raise ValueError(
            "missing_digits non può essere vuoto."
        )

    threshold = required_hit_count(
        len(missing_digits)
    )

    return sum(
        probability
        for next_missing, probability
        in transition_distribution(
            missing_digits
        ).items()
        if (
            len(missing_digits)
            - len(next_missing)
        ) >= threshold
    )


@dataclass(frozen=True)
class CoverageHitObservation:
    """Esito di uno stato storico verificato sul target successivo."""

    wheel: str
    wheel_order: int
    history_draw: int
    history_date: str
    target_draw: int
    target_date: str
    draws_in_cycle: int
    most_present_digits: frozenset[int]
    missing_digits: frozenset[int]
    target_digits: frozenset[int]
    hit_digits: frozenset[int]
    completion_within_one: float
    threshold_probability: float

    @property
    def required_hit_count(self) -> int:
        """
        Numero minimo di cifre mancanti da intercettare.

        Richiede N-1 cifre quando N > 1; con una sola
        cifra mancante richiede necessariamente quella cifra.
        """

        return required_hit_count(
            self.missing_count
        )

    @property
    def obtained(self) -> bool:
        """Il target raggiunge la soglia di quasi-chiusura."""

        return len(self.hit_digits) >= self.required_hit_count

    @property
    def most_present_count(self) -> int:
        return len(self.most_present_digits)

    @property
    def missing_count(self) -> int:
        return len(self.missing_digits)


@dataclass(frozen=True)
class CoverageHitSummary:
    """Aggregato per quantità TOP, mancanti e fascia Markov."""

    most_present_count: int
    missing_count: int
    mean_completion_within_one: float
    mean_threshold_probability: float
    attempts: int
    obtained: int
    missed: int
    hit_digit_count: int

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0

        return self.obtained / self.attempts

    @property
    def mean_hit_digits(self) -> float:
        if self.attempts == 0:
            return 0.0

        return self.hit_digit_count / self.attempts

    @property
    def success_excess(self) -> float:
        """Scarto fra successo osservato e probabilità attesa."""

        return (
            self.success_rate
            - self.mean_threshold_probability
        )


def _ordered_single_wheel(
    draws: Sequence[DrawSnapshot],
) -> tuple[DrawSnapshot, ...]:
    if not draws:
        return ()

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    if any(
        draw.wheel != wheel
        or draw.wheel_order != wheel_order
        for draw in draws
    ):
        raise ValueError(
            "Le osservazioni non possono mescolare ruote."
        )

    return tuple(
        sorted(
            draws,
            key=lambda draw: (
                draw.draw_date,
                draw.draw_number,
            ),
        )
    )


def build_coverage_hit_observations(
    draws: Sequence[DrawSnapshot],
) -> tuple[CoverageHitObservation, ...]:
    """
    Costruisce le osservazioni walk-forward di una ruota.

    Lo stato associato a ciascun target usa esclusivamente
    le estrazioni precedenti al target stesso.
    """

    ordered = _ordered_single_wheel(draws)

    if len(ordered) < 2:
        return ()

    observations: list[CoverageHitObservation] = []

    for target_index in range(1, len(ordered)):
        history = ordered[:target_index]
        target = ordered[target_index]
        state = current_coverage_state(history)

        if (
            not state.synchronized
            or state.draws_in_cycle == 0
        ):
            continue

        target_digits = digits_in_draw(target)
        hit_digits = (
            state.missing_digits
            & target_digits
        )
        metrics = maturity_metrics(
            state.missing_digits,
            horizons=(1,),
        )
        completion = metrics["completion_within"]

        observations.append(
            CoverageHitObservation(
                wheel=target.wheel,
                wheel_order=target.wheel_order,
                history_draw=state.latest_draw,
                history_date=state.latest_date,
                target_draw=target.draw_number,
                target_date=target.draw_date,
                draws_in_cycle=state.draws_in_cycle,
                most_present_digits=(
                    state.most_present_digits
                ),
                missing_digits=state.missing_digits,
                target_digits=target_digits,
                hit_digits=hit_digits,
                completion_within_one=float(
                    completion[1]
                ),
                threshold_probability=(
                    theoretical_threshold_probability(
                        state.missing_digits
                    )
                ),
            )
        )

    return tuple(observations)


def build_coverage_hit_experiment(
    draws_by_wheel: Mapping[
        str,
        Sequence[DrawSnapshot],
    ],
) -> tuple[CoverageHitObservation, ...]:
    observations: list[CoverageHitObservation] = []

    for draws in draws_by_wheel.values():
        observations.extend(
            build_coverage_hit_observations(draws)
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


def select_latest_targets(
    observations: Sequence[CoverageHitObservation],
    *,
    target_count: int,
) -> tuple[CoverageHitObservation, ...]:
    if (
        not isinstance(target_count, int)
        or isinstance(target_count, bool)
        or target_count <= 0
    ):
        raise ValueError(
            "target_count deve essere un intero positivo."
        )

    target_keys = sorted(
        {
            (
                observation.target_date,
                observation.target_draw,
            )
            for observation in observations
        }
    )
    selected_keys = frozenset(
        target_keys[-target_count:]
    )

    return tuple(
        observation
        for observation in observations
        if (
            observation.target_date,
            observation.target_draw,
        ) in selected_keys
    )


def summarize_coverage_hits(
    observations: Sequence[CoverageHitObservation],
) -> tuple[CoverageHitSummary, ...]:
    grouped: dict[
        tuple[int, int],
        list[CoverageHitObservation],
    ] = defaultdict(list)

    for observation in observations:
        key = (
            observation.most_present_count,
            observation.missing_count,
        )
        grouped[key].append(observation)

    summaries = []

    for (
        most_present_count,
        missing_count,
    ), items in grouped.items():
        obtained = sum(
            observation.obtained
            for observation in items
        )
        attempts = len(items)

        summaries.append(
            CoverageHitSummary(
                most_present_count=most_present_count,
                missing_count=missing_count,
                mean_completion_within_one=(
                    sum(
                        observation.completion_within_one
                        for observation in items
                    )
                    / attempts
                ),
                mean_threshold_probability=(
                    sum(
                        observation.threshold_probability
                        for observation in items
                    )
                    / attempts
                ),
                attempts=attempts,
                obtained=obtained,
                missed=attempts - obtained,
                hit_digit_count=sum(
                    len(observation.hit_digits)
                    for observation in items
                ),
            )
        )

    return tuple(
        sorted(
            summaries,
            key=lambda summary: (
                summary.missing_count,
                summary.most_present_count,
            ),
        )
    )
