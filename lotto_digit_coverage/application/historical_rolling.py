"""Presentation-neutral rolling-frequency experiment orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import comb

from lotto_digit_coverage.domain.draws import DrawSnapshot
from strategies.rolling_frequency import (
    WalkForwardObservation,
    build_walk_forward_experiment,
    simulate_equal_size_random_baseline,
    summarize_walk_forward_observations,
)


@dataclass(frozen=True)
class RollingFrequencyResultRow:
    window_size: int
    period: str
    start_date: str
    end_date: str
    repetitions: int
    seed: int
    observation_count: int
    candidate_number_count: int
    covered_ambo_count: int
    observed_hit_number_count: int
    theoretical_hit_number_count: float
    random_mean_hit_number_count: float
    observed_to_random_number_ratio: float
    empirical_p_value_hit_number: float
    observed_hit_ambo_count: int
    theoretical_hit_ambo_count: float
    random_mean_hit_ambo_count: float
    observed_to_random_ambo_ratio: float
    empirical_p_value_hit_ambo: float


@dataclass(frozen=True)
class RollingFrequencyReport:
    rows: tuple[RollingFrequencyResultRow, ...]
    window_sizes: tuple[int, ...]
    periods: tuple[tuple[str, str, str], ...]
    repetitions: int
    base_seed: int
    wheel_count: int


def safe_ratio(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0.0 else numerator / denominator


def build_result_rows(
    experiment: Mapping[int, Sequence[WalkForwardObservation]],
    *,
    window_sizes: Sequence[int],
    periods: Sequence[tuple[str, str, str]],
    repetitions: int,
    base_seed: int,
) -> tuple[RollingFrequencyResultRow, ...]:
    rows: list[RollingFrequencyResultRow] = []

    for window_size in window_sizes:
        if window_size not in experiment:
            raise ValueError(
                f"Esperimento mancante per la finestra {window_size}."
            )
        observations = experiment[window_size]

        for period_index, (period, start_date, end_date) in enumerate(periods):
            seed = base_seed + window_size * 100 + period_index
            summary = summarize_walk_forward_observations(
                observations,
                window_size=window_size,
                period=period,
                start_date=start_date,
                end_date=end_date,
            )
            baseline = simulate_equal_size_random_baseline(
                observations,
                window_size=window_size,
                period=period,
                start_date=start_date,
                end_date=end_date,
                repetitions=repetitions,
                seed=seed,
            )
            theoretical_numbers = summary.candidate_number_count * 5 / 90
            theoretical_ambi = (
                summary.covered_ambo_count * comb(5, 2) / comb(90, 2)
            )
            rows.append(
                RollingFrequencyResultRow(
                    window_size=window_size,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    repetitions=repetitions,
                    seed=seed,
                    observation_count=summary.observation_count,
                    candidate_number_count=summary.candidate_number_count,
                    covered_ambo_count=summary.covered_ambo_count,
                    observed_hit_number_count=summary.hit_number_count,
                    theoretical_hit_number_count=theoretical_numbers,
                    random_mean_hit_number_count=baseline.mean_hit_number_count,
                    observed_to_random_number_ratio=safe_ratio(
                        summary.hit_number_count,
                        baseline.mean_hit_number_count,
                    ),
                    empirical_p_value_hit_number=(
                        baseline.empirical_p_value_hit_number
                    ),
                    observed_hit_ambo_count=summary.hit_ambo_count,
                    theoretical_hit_ambo_count=theoretical_ambi,
                    random_mean_hit_ambo_count=baseline.mean_hit_ambo_count,
                    observed_to_random_ambo_ratio=safe_ratio(
                        summary.hit_ambo_count,
                        baseline.mean_hit_ambo_count,
                    ),
                    empirical_p_value_hit_ambo=baseline.empirical_p_value_hit_ambo,
                )
            )

    return tuple(rows)


def build_rolling_frequency_report(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    *,
    window_sizes: Sequence[int],
    periods: Sequence[tuple[str, str, str]],
    repetitions: int,
    base_seed: int,
) -> RollingFrequencyReport:
    normalized_windows = tuple(sorted(set(window_sizes)))
    if not normalized_windows or any(window <= 0 for window in normalized_windows):
        raise ValueError("Le finestre rolling devono essere interi positivi.")
    if repetitions <= 0:
        raise ValueError("Le repliche devono essere positive.")

    experiment = build_walk_forward_experiment(
        draws_by_wheel,
        window_sizes=normalized_windows,
    )
    rows = build_result_rows(
        experiment,
        window_sizes=normalized_windows,
        periods=periods,
        repetitions=repetitions,
        base_seed=base_seed,
    )
    return RollingFrequencyReport(
        rows=rows,
        window_sizes=normalized_windows,
        periods=tuple(periods),
        repetitions=repetitions,
        base_seed=base_seed,
        wheel_count=len(draws_by_wheel),
    )
