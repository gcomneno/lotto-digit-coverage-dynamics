"""Presentation-neutral historical coverage and Markov analysis use cases."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from collections.abc import Hashable, Sequence
from dataclasses import dataclass

from lotto_digit_coverage.application.repositories import DrawRepository
from strategies.coverage_completion import (
    CoverageCompletionObservation,
    collect_completion_observations,
    exact_completion_probability,
)
from strategies.coverage_markov_residuals import (
    MarkovResidualObservation,
    collect_residual_observations,
)
from strategies.coverage_markov_validation import (
    MarkovCalibrationObservation,
    collect_calibration_observations,
)


@dataclass(frozen=True)
class CompletionSummary:
    cases: int
    completions: int
    observed_probability: float
    theoretical_probability: float
    delta: float


@dataclass(frozen=True)
class CompletionGroup:
    key: int | str | frozenset[int]
    summary: CompletionSummary


@dataclass(frozen=True)
class CompletionResidualRow:
    missing_count: int
    states: int
    mean_remaining: float
    median_remaining: float
    minimum_remaining: int
    maximum_remaining: int


@dataclass(frozen=True)
class CoverageCompletionReport:
    observations: tuple[CoverageCompletionObservation, ...]
    by_missing_count: tuple[CompletionGroup, ...]
    by_cycle_age: tuple[CompletionGroup, ...]
    single_missing: tuple[CompletionGroup, ...]
    exact_states: tuple[CompletionGroup, ...]
    residual_rows: tuple[CompletionResidualRow, ...]
    right_censored_states: int
    minimum_state_cases: int


@dataclass(frozen=True)
class CalibrationSummary:
    cases: int
    completions: int
    observed_probability: float
    predicted_probability: float
    delta: float
    brier_score: float


@dataclass(frozen=True)
class CalibrationGroup:
    key: int | str | frozenset[int]
    summary: CalibrationSummary


@dataclass(frozen=True)
class CalibrationBandReport:
    horizon: int
    groups: tuple[CalibrationGroup, ...]
    weighted_absolute_error: float


@dataclass(frozen=True)
class MarkovValidationReport:
    observations: tuple[MarkovCalibrationObservation, ...]
    horizons: tuple[int, ...]
    overall: tuple[CalibrationGroup, ...]
    probability_bands: tuple[CalibrationBandReport, ...]
    exact_states_h1: tuple[CalibrationGroup, ...]
    exact_states_h3: tuple[CalibrationGroup, ...]
    minimum_state_cases: int


@dataclass(frozen=True)
class ResidualSummary:
    states: int
    actual_mean: float
    predicted_mean: float
    bias: float
    mean_absolute_error: float
    root_mean_square_error: float


@dataclass(frozen=True)
class ResidualGroup:
    key: int | str | frozenset[int]
    summary: ResidualSummary


@dataclass(frozen=True)
class MarkovResidualReport:
    observations: tuple[MarkovResidualObservation, ...]
    overall: ResidualSummary
    by_missing_count: tuple[ResidualGroup, ...]
    by_expectation_band: tuple[ResidualGroup, ...]
    exact_states: tuple[ResidualGroup, ...]
    minimum_state_cases: int


def summarize_completion(
    observations: Sequence[CoverageCompletionObservation],
) -> CompletionSummary:
    total = len(observations)
    hits = sum(observation.completed_next for observation in observations)
    observed = hits / total if total else 0.0
    expected = (
        statistics.mean(
            exact_completion_probability(observation.missing_digits)
            for observation in observations
        )
        if observations
        else 0.0
    )

    return CompletionSummary(
        cases=total,
        completions=hits,
        observed_probability=observed,
        theoretical_probability=expected,
        delta=observed - expected,
    )


def age_bucket(draws_in_cycle: int) -> str:
    if draws_in_cycle <= 4:
        return str(draws_in_cycle)
    return "5+"


def bucket_order(bucket: str) -> int:
    return int(bucket.rstrip("+"))


def completed_cycle_lengths(
    observations: Sequence[CoverageCompletionObservation],
) -> dict[tuple[str, int], int]:
    lengths: dict[tuple[str, int], int] = {}

    for observation in observations:
        if observation.completed_next:
            lengths[(observation.wheel, observation.cycle_number)] = (
                observation.draws_in_cycle + 1
            )

    return lengths


def _completion_groups(
    groups: dict[Hashable, list[CoverageCompletionObservation]],
    keys: Sequence[Hashable],
) -> tuple[CompletionGroup, ...]:
    return tuple(
        CompletionGroup(key=key, summary=summarize_completion(groups.get(key, [])))
        for key in keys
    )


def build_coverage_completion_report(
    repository: DrawRepository,
    *,
    minimum_state_cases: int = 10,
) -> CoverageCompletionReport:
    if minimum_state_cases <= 0:
        raise ValueError("Il numero minimo di casi deve essere positivo.")

    observations = tuple(collect_completion_observations(repository))
    if not observations:
        raise RuntimeError("Nessuna osservazione di copertura disponibile.")

    by_missing_count: dict[int, list[CoverageCompletionObservation]] = defaultdict(list)
    by_cycle_age: dict[str, list[CoverageCompletionObservation]] = defaultdict(list)
    single_missing: dict[int, list[CoverageCompletionObservation]] = defaultdict(list)
    exact_states: dict[frozenset[int], list[CoverageCompletionObservation]] = defaultdict(list)

    for observation in observations:
        by_missing_count[len(observation.missing_digits)].append(observation)
        by_cycle_age[age_bucket(observation.draws_in_cycle)].append(observation)
        exact_states[observation.missing_digits].append(observation)
        if len(observation.missing_digits) == 1:
            single_missing[next(iter(observation.missing_digits))].append(observation)

    eligible_states = [
        state
        for state, items in exact_states.items()
        if len(items) >= minimum_state_cases
    ]
    eligible_states.sort(
        key=lambda state: (
            len(state),
            -len(exact_states[state]),
            tuple(sorted(state)),
        )
    )

    lengths = completed_cycle_lengths(observations)
    residuals: dict[int, list[int]] = defaultdict(list)
    censored = 0

    for observation in observations:
        cycle_length = lengths.get((observation.wheel, observation.cycle_number))
        if cycle_length is None:
            censored += 1
            continue
        residuals[len(observation.missing_digits)].append(
            cycle_length - observation.draws_in_cycle
        )

    residual_rows = tuple(
        CompletionResidualRow(
            missing_count=missing_count,
            states=len(values),
            mean_remaining=statistics.mean(values),
            median_remaining=statistics.median(values),
            minimum_remaining=min(values),
            maximum_remaining=max(values),
        )
        for missing_count, values in sorted(residuals.items())
    )

    return CoverageCompletionReport(
        observations=observations,
        by_missing_count=_completion_groups(
            by_missing_count,
            sorted(by_missing_count),
        ),
        by_cycle_age=_completion_groups(
            by_cycle_age,
            sorted(by_cycle_age, key=bucket_order),
        ),
        single_missing=_completion_groups(single_missing, tuple(range(10))),
        exact_states=_completion_groups(exact_states, eligible_states),
        residual_rows=residual_rows,
        right_censored_states=censored,
        minimum_state_cases=minimum_state_cases,
    )


def probability_band(probability: float) -> str:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("La probabilità deve essere compresa tra 0 e 1.")
    if probability < 0.10:
        return "0–10%"
    if probability < 0.25:
        return "10–25%"
    if probability < 0.50:
        return "25–50%"
    if probability < 0.75:
        return "50–75%"
    if probability < 0.90:
        return "75–90%"
    return "90–100%"


def probability_band_sort_key(label: str) -> int:
    return {
        "0–10%": 0,
        "10–25%": 1,
        "25–50%": 2,
        "50–75%": 3,
        "75–90%": 4,
        "90–100%": 5,
    }[label]


def summarize_calibration(
    observations: Sequence[MarkovCalibrationObservation],
) -> CalibrationSummary:
    total = len(observations)
    hits = sum(observation.completed_within for observation in observations)
    observed = hits / total if total else 0.0
    predicted = (
        statistics.mean(
            observation.predicted_probability for observation in observations
        )
        if observations
        else 0.0
    )
    brier = (
        statistics.mean(
            (
                float(observation.completed_within)
                - observation.predicted_probability
            )
            ** 2
            for observation in observations
        )
        if observations
        else 0.0
    )

    return CalibrationSummary(
        cases=total,
        completions=hits,
        observed_probability=observed,
        predicted_probability=predicted,
        delta=observed - predicted,
        brier_score=brier,
    )


def grouped_calibration_error(
    groups: dict[Hashable, list[MarkovCalibrationObservation]],
) -> float:
    total = sum(len(items) for items in groups.values())
    if total == 0:
        return 0.0
    return sum(
        len(items) / total * abs(summarize_calibration(items).delta)
        for items in groups.values()
    )


def _calibration_groups(
    groups: dict[Hashable, list[MarkovCalibrationObservation]],
    keys: Sequence[Hashable],
) -> tuple[CalibrationGroup, ...]:
    return tuple(
        CalibrationGroup(key=key, summary=summarize_calibration(groups.get(key, [])))
        for key in keys
    )


def _exact_calibration_groups(
    observations: Sequence[MarkovCalibrationObservation],
    *,
    horizon: int,
    minimum_cases: int,
) -> tuple[CalibrationGroup, ...]:
    groups: dict[frozenset[int], list[MarkovCalibrationObservation]] = defaultdict(list)
    for observation in observations:
        if observation.horizon == horizon:
            groups[observation.missing_digits].append(observation)

    eligible = [state for state, items in groups.items() if len(items) >= minimum_cases]
    eligible.sort(
        key=lambda state: (
            len(state),
            -len(groups[state]),
            tuple(sorted(state)),
        )
    )
    return _calibration_groups(groups, eligible)


def build_markov_validation_report(
    repository: DrawRepository,
    *,
    horizons: Sequence[int] = (1, 2, 3, 5),
    minimum_state_cases: int = 20,
) -> MarkovValidationReport:
    normalized_horizons = tuple(sorted(set(horizons)))
    if not normalized_horizons or any(horizon <= 0 for horizon in normalized_horizons):
        raise ValueError("Gli orizzonti devono essere interi positivi.")
    if minimum_state_cases <= 0:
        raise ValueError("Il numero minimo di casi deve essere positivo.")

    observations = tuple(
        collect_calibration_observations(repository, horizons=normalized_horizons)
    )
    if not observations:
        raise RuntimeError("Nessuna osservazione di calibrazione disponibile.")

    by_horizon: dict[int, list[MarkovCalibrationObservation]] = defaultdict(list)
    for observation in observations:
        by_horizon[observation.horizon].append(observation)

    band_reports: list[CalibrationBandReport] = []
    for horizon in sorted(by_horizon):
        groups: dict[str, list[MarkovCalibrationObservation]] = defaultdict(list)
        for observation in by_horizon[horizon]:
            groups[probability_band(observation.predicted_probability)].append(observation)
        ordered = sorted(groups, key=probability_band_sort_key)
        band_reports.append(
            CalibrationBandReport(
                horizon=horizon,
                groups=_calibration_groups(groups, ordered),
                weighted_absolute_error=grouped_calibration_error(groups),
            )
        )

    return MarkovValidationReport(
        observations=observations,
        horizons=normalized_horizons,
        overall=_calibration_groups(by_horizon, sorted(by_horizon)),
        probability_bands=tuple(band_reports),
        exact_states_h1=_exact_calibration_groups(
            observations,
            horizon=1,
            minimum_cases=minimum_state_cases,
        ),
        exact_states_h3=_exact_calibration_groups(
            observations,
            horizon=3,
            minimum_cases=minimum_state_cases,
        ),
        minimum_state_cases=minimum_state_cases,
    )


def expectation_band(value: float) -> str:
    if value < 1.75:
        return "<1.75"
    if value < 2.25:
        return "1.75–2.25"
    if value < 2.75:
        return "2.25–2.75"
    if value < 3.25:
        return "2.75–3.25"
    return "3.25+"


def expectation_band_sort_key(label: str) -> int:
    return {
        "<1.75": 0,
        "1.75–2.25": 1,
        "2.25–2.75": 2,
        "2.75–3.25": 3,
        "3.25+": 4,
    }[label]


def summarize_residual(
    observations: Sequence[MarkovResidualObservation],
) -> ResidualSummary:
    total = len(observations)
    if not observations:
        return ResidualSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0)

    actual_mean = statistics.mean(
        observation.actual_remaining for observation in observations
    )
    predicted_mean = statistics.mean(
        observation.predicted_remaining for observation in observations
    )
    errors = tuple(
        observation.actual_remaining - observation.predicted_remaining
        for observation in observations
    )
    bias = statistics.mean(errors)
    mae = statistics.mean(abs(error) for error in errors)
    rmse = math.sqrt(statistics.mean(error * error for error in errors))

    return ResidualSummary(
        states=total,
        actual_mean=actual_mean,
        predicted_mean=predicted_mean,
        bias=bias,
        mean_absolute_error=mae,
        root_mean_square_error=rmse,
    )


def _residual_groups(
    groups: dict[Hashable, list[MarkovResidualObservation]],
    keys: Sequence[Hashable],
) -> tuple[ResidualGroup, ...]:
    return tuple(
        ResidualGroup(key=key, summary=summarize_residual(groups.get(key, [])))
        for key in keys
    )


def build_markov_residual_report(
    repository: DrawRepository,
    *,
    minimum_state_cases: int = 20,
) -> MarkovResidualReport:
    if minimum_state_cases <= 0:
        raise ValueError("Il numero minimo di casi deve essere positivo.")

    observations = tuple(collect_residual_observations(repository))
    if not observations:
        raise RuntimeError("Nessuna osservazione residua disponibile.")

    by_missing_count: dict[int, list[MarkovResidualObservation]] = defaultdict(list)
    by_expectation_band: dict[str, list[MarkovResidualObservation]] = defaultdict(list)
    exact_states: dict[frozenset[int], list[MarkovResidualObservation]] = defaultdict(list)

    for observation in observations:
        by_missing_count[len(observation.missing_digits)].append(observation)
        by_expectation_band[expectation_band(observation.predicted_remaining)].append(
            observation
        )
        exact_states[observation.missing_digits].append(observation)

    eligible = [
        state
        for state, items in exact_states.items()
        if len(items) >= minimum_state_cases
    ]
    eligible.sort(
        key=lambda state: (
            len(state),
            -len(exact_states[state]),
            tuple(sorted(state)),
        )
    )

    return MarkovResidualReport(
        observations=observations,
        overall=summarize_residual(observations),
        by_missing_count=_residual_groups(
            by_missing_count,
            sorted(by_missing_count),
        ),
        by_expectation_band=_residual_groups(
            by_expectation_band,
            sorted(by_expectation_band, key=expectation_band_sort_key),
        ),
        exact_states=_residual_groups(exact_states, eligible),
        minimum_state_cases=minimum_state_cases,
    )
