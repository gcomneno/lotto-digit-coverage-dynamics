"""Analisi one-step dei numeri gemelli 11–88."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from statistics import NormalDist
from typing import Mapping, Sequence

from strategies.coverage_completion import ALL_DIGITS, digits_in_draw
from strategies.lotto_repository import DrawSnapshot, split_digits


TWIN_DIGITS = tuple(range(1, 9))
TWIN_NUMBERS = {digit: 11 * digit for digit in TWIN_DIGITS}
NULL_TWIN_PROBABILITY = 1.0 / 18.0
MIN_CANDIDATE_CASES = 200
CONDITION_ORDER = {
    "baseline": 0,
    "missing": 1,
    "top": 2,
    "last-missing": 3,
    "missing-age>=3": 4,
    "return-gap:1-4": 5,
    "return-gap:5-9": 6,
    "return-gap:10-19": 7,
    "return-gap:20+": 8,
}


@dataclass(frozen=True)
class TwinObservation:
    wheel: str
    wheel_order: int
    target_draw: int
    target_date: str
    digit: int
    twin_number: int
    conditions: tuple[str, ...]
    hit: bool


@dataclass(frozen=True)
class TwinStatisticsRow:
    condition: str
    digit: int
    twin_number: int
    cases: int
    hits: int
    expected_hits: float
    null_probability: float
    observed_probability: float
    lift_probability: float
    wilson_low: float
    wilson_high: float
    p_value: float
    q_value: float
    candidate: bool


def _ordered_single_wheel_draws(
    draws: Sequence[DrawSnapshot],
) -> tuple[DrawSnapshot, ...]:
    if not draws:
        return ()

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    if any(
        draw.wheel != wheel
        or draw.wheel_order != wheel_order
        or len(draw.numbers) != 5
        for draw in draws
    ):
        raise ValueError(
            "Le estrazioni devono essere complete e appartenere "
            "alla stessa ruota."
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
    identities = tuple(
        (draw.draw_date, draw.draw_number)
        for draw in ordered
    )

    if len(identities) != len(set(identities)):
        raise ValueError("La cronologia contiene estrazioni duplicate.")

    return ordered


def _top_digits(counts: Sequence[int]) -> frozenset[int]:
    maximum = max(counts, default=0)

    if maximum <= 0:
        return frozenset()

    return frozenset(
        digit
        for digit, count in enumerate(counts)
        if count == maximum
    )


def _return_gap_condition(gap: int) -> str:
    if gap <= 4:
        return "return-gap:1-4"
    if gap <= 9:
        return "return-gap:5-9"
    if gap <= 19:
        return "return-gap:10-19"
    return "return-gap:20+"


def build_twin_observations(
    draws: Sequence[DrawSnapshot],
) -> tuple[TwinObservation, ...]:
    """
    Fotografa lo stato prima di ogni estrazione target.

    Il tratto iniziale viene escluso fino alla prima copertura
    completa osservata. Gli stati MISSING/TOP iniziano soltanto
    quando il nuovo ciclo contiene almeno un'estrazione: lo stato
    vuoto di ripartenza, in cui tutte le cifre sono mancanti, non è
    considerato un segnale informativo.
    """

    ordered = _ordered_single_wheel_draws(draws)

    if not ordered:
        return ()

    covered: set[int] = set()
    counts = [0] * 10
    draws_in_cycle = 0
    synchronized = False
    last_twin_index: dict[int, int] = {}
    observations: list[TwinObservation] = []

    for draw_index, draw in enumerate(ordered):
        observed_digits = digits_in_draw(draw)

        if synchronized:
            missing = ALL_DIGITS.difference(covered)
            top = _top_digits(counts)

            for digit in TWIN_DIGITS:
                conditions = ["baseline"]

                if draws_in_cycle > 0:
                    if digit in missing:
                        conditions.append("missing")

                        if draws_in_cycle >= 3:
                            conditions.append("missing-age>=3")

                    if digit in top:
                        conditions.append("top")

                    if missing == frozenset({digit}):
                        conditions.append("last-missing")

                previous_index = last_twin_index.get(digit)

                if previous_index is not None:
                    conditions.append(
                        _return_gap_condition(
                            draw_index - previous_index
                        )
                    )

                twin_number = TWIN_NUMBERS[digit]

                observations.append(
                    TwinObservation(
                        wheel=draw.wheel,
                        wheel_order=draw.wheel_order,
                        target_draw=draw.draw_number,
                        target_date=draw.draw_date,
                        digit=digit,
                        twin_number=twin_number,
                        conditions=tuple(conditions),
                        hit=twin_number in draw.numbers,
                    )
                )

        for digit, twin_number in TWIN_NUMBERS.items():
            if twin_number in draw.numbers:
                last_twin_index[digit] = draw_index

        covered.update(observed_digits)

        for number in draw.numbers:
            for digit in split_digits(number):
                counts[digit] += 1

        draws_in_cycle += 1

        if covered == ALL_DIGITS:
            synchronized = True
            covered.clear()
            counts = [0] * 10
            draws_in_cycle = 0

    return tuple(observations)


def build_all_twin_observations(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
) -> tuple[TwinObservation, ...]:
    result = [
        observation
        for draws in draws_by_wheel.values()
        for observation in build_twin_observations(draws)
    ]

    return tuple(
        sorted(
            result,
            key=lambda observation: (
                observation.target_date,
                observation.target_draw,
                observation.wheel_order,
                observation.digit,
            ),
        )
    )


def wilson_interval(
    hits: int,
    cases: int,
    *,
    confidence: float = 0.95,
) -> tuple[float, float]:
    if cases <= 0:
        raise ValueError("cases deve essere positivo")
    if hits < 0 or hits > cases:
        raise ValueError("hits deve appartenere a 0..cases")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence deve appartenere a (0, 1)")

    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    proportion = hits / cases
    z2 = z * z
    denominator = 1.0 + z2 / cases
    center = (proportion + z2 / (2.0 * cases)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / cases
            + z2 / (4.0 * cases * cases)
        )
        / denominator
    )

    return max(0.0, center - margin), min(1.0, center + margin)


def binomial_two_sided_p_value(
    hits: int,
    cases: int,
    probability: float = NULL_TWIN_PROBABILITY,
) -> float:
    """Test binomiale esatto two-sided con ordinamento per PMF."""

    if cases <= 0:
        raise ValueError("cases deve essere positivo")
    if hits < 0 or hits > cases:
        raise ValueError("hits deve appartenere a 0..cases")
    if not 0.0 < probability < 1.0:
        raise ValueError("probability deve appartenere a (0, 1)")

    log_p = math.log(probability)
    log_q = math.log1p(-probability)

    def log_pmf(value: int) -> float:
        return (
            math.lgamma(cases + 1)
            - math.lgamma(value + 1)
            - math.lgamma(cases - value + 1)
            + value * log_p
            + (cases - value) * log_q
        )

    observed = log_pmf(hits)
    threshold = observed + 1e-12
    total = 0.0

    for value in range(cases + 1):
        candidate = log_pmf(value)

        if candidate <= threshold:
            total += math.exp(candidate)

    return min(1.0, total)


def benjamini_hochberg(
    p_values: Sequence[float],
) -> tuple[float, ...]:
    if any(not 0.0 <= value <= 1.0 for value in p_values):
        raise ValueError("I p-value devono appartenere a [0, 1]")

    count = len(p_values)

    if count == 0:
        return ()

    ordered = sorted(
        enumerate(p_values),
        key=lambda item: item[1],
    )
    adjusted = [1.0] * count
    running = 1.0

    for rank_index in range(count - 1, -1, -1):
        original_index, p_value = ordered[rank_index]
        rank = rank_index + 1
        candidate = min(1.0, p_value * count / rank)
        running = min(running, candidate)
        adjusted[original_index] = running

    return tuple(adjusted)


def build_twin_statistics(
    observations: Sequence[TwinObservation],
) -> tuple[TwinStatisticsRow, ...]:
    grouped: dict[tuple[str, int], list[bool]] = defaultdict(list)

    for observation in observations:
        for condition in observation.conditions:
            grouped[(condition, observation.digit)].append(
                observation.hit
            )

    provisional: list[TwinStatisticsRow] = []

    for (condition, digit), outcomes in grouped.items():
        cases = len(outcomes)
        hits = sum(outcomes)
        observed = hits / cases
        wilson_low, wilson_high = wilson_interval(hits, cases)
        p_value = binomial_two_sided_p_value(hits, cases)

        provisional.append(
            TwinStatisticsRow(
                condition=condition,
                digit=digit,
                twin_number=TWIN_NUMBERS[digit],
                cases=cases,
                hits=hits,
                expected_hits=cases * NULL_TWIN_PROBABILITY,
                null_probability=NULL_TWIN_PROBABILITY,
                observed_probability=observed,
                lift_probability=observed - NULL_TWIN_PROBABILITY,
                wilson_low=wilson_low,
                wilson_high=wilson_high,
                p_value=p_value,
                q_value=1.0,
                candidate=False,
            )
        )

    provisional.sort(
        key=lambda row: (
            CONDITION_ORDER.get(row.condition, 999),
            row.digit,
        )
    )

    screened_indexes = [
        index
        for index, row in enumerate(provisional)
        if row.condition != "baseline"
    ]
    q_values = benjamini_hochberg(
        [
            provisional[index].p_value
            for index in screened_indexes
        ]
    )

    for index, q_value in zip(screened_indexes, q_values):
        row = provisional[index]
        excludes_null = (
            row.wilson_high < row.null_probability
            or row.wilson_low > row.null_probability
        )
        provisional[index] = replace(
            row,
            q_value=q_value,
            candidate=(
                row.cases >= MIN_CANDIDATE_CASES
                and q_value < 0.05
                and excludes_null
            ),
        )

    return tuple(provisional)
