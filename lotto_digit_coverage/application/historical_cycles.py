"""Presentation-neutral historical cycle-distribution analysis."""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from lotto_digit_coverage.domain.draws import DrawSnapshot
from strategies.coverage_completion import ALL_DIGITS
from strategies.coverage_cycle_history import (
    CompletedCoverageCycle,
    WheelCoverageHistory,
    build_wheel_cycle_history,
    flatten_completed_cycles,
)
from strategies.coverage_markov import (
    absorption_probability_mass,
    absorption_quantiles,
    expected_remaining_draws,
    variance_remaining_draws,
)


@dataclass(frozen=True)
class DurationComparisonRow:
    duration: int
    observed_count: int
    observed_probability: float
    observed_cdf: float
    theoretical_probability: float
    theoretical_cdf: float
    expected_count: float
    count_difference: float


@dataclass(frozen=True)
class CycleDistributionSummary:
    cycle_count: int
    minimum_duration: int
    maximum_duration: int
    observed_mean: float
    theoretical_mean: float
    mean_difference: float
    observed_variance: float
    theoretical_variance: float
    variance_difference: float
    observed_standard_deviation: float
    theoretical_standard_deviation: float
    observed_quantile_50: int
    theoretical_quantile_50: int
    observed_quantile_90: int
    theoretical_quantile_90: int
    observed_quantile_95: int
    theoretical_quantile_95: int
    observed_quantile_99: int
    theoretical_quantile_99: int
    cdf_mean_absolute_error: float
    cdf_maximum_absolute_error: float
    theoretical_tail_after_horizon: float
    comparison_horizon: int


@dataclass(frozen=True)
class SegmentAnalysis:
    label: str
    database_paths: tuple[str, ...]
    first_date: str
    last_date: str
    histories: tuple[WheelCoverageHistory, ...]
    cycles: tuple[CompletedCoverageCycle, ...]
    summary: CycleDistributionSummary
    duration_rows: tuple[DurationComparisonRow, ...]


def empirical_quantile(durations: Sequence[int], probability: float) -> int:
    if not durations:
        raise ValueError("Servono durate per calcolare un quantile.")
    if not 0.0 < probability < 1.0:
        raise ValueError(
            "La probabilità deve essere compresa strettamente tra zero e uno."
        )
    ordered = sorted(durations)
    rank = math.ceil(probability * len(ordered))
    return ordered[rank - 1]


def build_duration_comparison(
    durations: Sequence[int],
    *,
    comparison_horizon: int | None = None,
) -> tuple[DurationComparisonRow, ...]:
    if not durations:
        raise ValueError("Servono cicli completi per il confronto.")
    if any(duration <= 0 for duration in durations):
        raise ValueError("Le durate devono essere interi positivi.")

    q99 = absorption_quantiles(ALL_DIGITS, (0.99,))[0.99]
    horizon = comparison_horizon if comparison_horizon is not None else max(
        max(durations), q99
    )
    if horizon <= 0:
        raise ValueError("L'orizzonte deve essere positivo.")

    mass = absorption_probability_mass(ALL_DIGITS, horizon)
    total = len(durations)
    counts = {duration: durations.count(duration) for duration in set(durations)}
    rows: list[DurationComparisonRow] = []
    observed_cdf = 0.0
    theoretical_cdf = 0.0

    for duration in range(1, horizon + 1):
        observed_count = counts.get(duration, 0)
        observed_probability = observed_count / total
        theoretical_probability = mass[duration]
        observed_cdf += observed_probability
        theoretical_cdf += theoretical_probability
        expected_count = total * theoretical_probability
        rows.append(
            DurationComparisonRow(
                duration=duration,
                observed_count=observed_count,
                observed_probability=observed_probability,
                observed_cdf=observed_cdf,
                theoretical_probability=theoretical_probability,
                theoretical_cdf=theoretical_cdf,
                expected_count=expected_count,
                count_difference=observed_count - expected_count,
            )
        )
    return tuple(rows)


def summarize_durations(
    durations: Sequence[int],
    rows: Sequence[DurationComparisonRow],
) -> CycleDistributionSummary:
    if not durations:
        raise ValueError("Servono cicli completi per il riepilogo.")
    if not rows:
        raise ValueError("Servono righe di confronto.")

    theoretical_mean = expected_remaining_draws(ALL_DIGITS)
    theoretical_variance = variance_remaining_draws(ALL_DIGITS)
    quantiles = absorption_quantiles(ALL_DIGITS, (0.50, 0.90, 0.95, 0.99))
    observed_mean = statistics.fmean(durations)
    observed_variance = statistics.pvariance(durations)
    errors = [abs(row.observed_cdf - row.theoretical_cdf) for row in rows]

    return CycleDistributionSummary(
        cycle_count=len(durations),
        minimum_duration=min(durations),
        maximum_duration=max(durations),
        observed_mean=observed_mean,
        theoretical_mean=theoretical_mean,
        mean_difference=observed_mean - theoretical_mean,
        observed_variance=observed_variance,
        theoretical_variance=theoretical_variance,
        variance_difference=observed_variance - theoretical_variance,
        observed_standard_deviation=math.sqrt(observed_variance),
        theoretical_standard_deviation=math.sqrt(theoretical_variance),
        observed_quantile_50=empirical_quantile(durations, 0.50),
        theoretical_quantile_50=quantiles[0.50],
        observed_quantile_90=empirical_quantile(durations, 0.90),
        theoretical_quantile_90=quantiles[0.90],
        observed_quantile_95=empirical_quantile(durations, 0.95),
        theoretical_quantile_95=quantiles[0.95],
        observed_quantile_99=empirical_quantile(durations, 0.99),
        theoretical_quantile_99=quantiles[0.99],
        cdf_mean_absolute_error=statistics.fmean(errors),
        cdf_maximum_absolute_error=max(errors),
        theoretical_tail_after_horizon=max(0.0, 1.0 - rows[-1].theoretical_cdf),
        comparison_horizon=rows[-1].duration,
    )


def analyze_segment_from_draws(
    label: str,
    database_paths: Sequence[str],
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
) -> SegmentAnalysis:
    if not draws_by_wheel:
        raise ValueError("Serve almeno una ruota per segmento.")
    histories = tuple(
        build_wheel_cycle_history(draws)
        for draws in draws_by_wheel.values()
    )
    cycles = flatten_completed_cycles(histories)
    durations = [cycle.draws_in_cycle for cycle in cycles]
    rows = build_duration_comparison(durations)
    summary = summarize_durations(durations, rows)
    return SegmentAnalysis(
        label=label,
        database_paths=tuple(database_paths),
        first_date=min(history.first_date for history in histories),
        last_date=max(history.last_date for history in histories),
        histories=histories,
        cycles=cycles,
        summary=summary,
        duration_rows=rows,
    )
