"""Presentation-neutral historical signal and coverage analysis use cases."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from lotto_digit_coverage.application.repositories import DrawRepository
from strategies.coverage_hit_statistics import (
    CoverageHitObservation,
    CoverageHitSummary,
    build_coverage_hit_experiment,
    select_latest_targets,
    summarize_coverage_hits,
)
from strategies.digit_coverage import (
    DigitCoverageWindow,
    analyze_digit_coverage,
    load_draws_by_wheel,
)
from strategies.digit_return_times import (
    DigitReturnObservation,
    POSITIONS,
    collect_return_observations,
    theoretical_hit_probability,
)


@dataclass(frozen=True)
class CoverageHitReport:
    observations: tuple[CoverageHitObservation, ...]
    summaries: tuple[CoverageHitSummary, ...]
    target_keys: tuple[tuple[str, int], ...]
    target_count: int


@dataclass(frozen=True)
class ReturnSummary:
    cases: int
    hits: int
    observed_rate: float
    expected_rate: float
    delta: float


@dataclass(frozen=True)
class ReturnGroup:
    key: int | str
    summary: ReturnSummary
    maximum_absence: int = 0


@dataclass(frozen=True)
class ReturnHazardTable:
    position: str
    groups: tuple[ReturnGroup, ...]


@dataclass(frozen=True)
class DigitReturnReport:
    observations: tuple[DigitReturnObservation, ...]
    hazard_tables: tuple[ReturnHazardTable, ...]
    any_position_by_digit: tuple[ReturnGroup, ...]
    long_absences_by_digit: tuple[ReturnGroup, ...]


@dataclass(frozen=True)
class GlobalCoverageRow:
    window_size: int
    windows: int
    complete: int
    one_missing: int
    two_missing: int
    three_or_more_missing: int
    average_missing: float
    median_missing: float


@dataclass(frozen=True)
class DigitAbsenceRow:
    window_size: int
    digit: int
    absent_windows: int
    total_windows: int


@dataclass(frozen=True)
class WheelCoverageRow:
    window_size: int
    wheel: str
    wheel_order: int
    windows: int
    complete_windows: int
    at_most_one_missing_windows: int
    average_missing: float


@dataclass(frozen=True)
class LatestCoverageRow:
    window_size: int
    wheel: str
    wheel_order: int
    window: DigitCoverageWindow


@dataclass(frozen=True)
class DigitCoverageReport:
    windows_by_size: tuple[tuple[int, tuple[DigitCoverageWindow, ...]], ...]
    global_summary: tuple[GlobalCoverageRow, ...]
    digit_absence: tuple[DigitAbsenceRow, ...]
    wheel_summary: tuple[WheelCoverageRow, ...]
    latest_windows: tuple[LatestCoverageRow, ...]


def build_coverage_hit_report(
    repository: DrawRepository,
    *,
    target_count: int = 10,
) -> CoverageHitReport:
    if target_count <= 0:
        raise ValueError("Il numero di estrazioni target deve essere positivo.")

    all_observations = build_coverage_hit_experiment(load_draws_by_wheel(repository))
    observations = tuple(
        select_latest_targets(
            all_observations,
            target_count=target_count,
        )
    )
    if not observations:
        raise RuntimeError("Nessuna osservazione walk-forward disponibile.")

    target_keys = tuple(
        sorted(
            {
                (observation.target_date, observation.target_draw)
                for observation in observations
            }
        )
    )

    return CoverageHitReport(
        observations=observations,
        summaries=tuple(summarize_coverage_hits(observations)),
        target_keys=target_keys,
        target_count=target_count,
    )


def streak_bucket(absence_streak: int, *, maximum_explicit: int = 8) -> str:
    if absence_streak <= 0:
        raise ValueError("La durata dell'assenza deve essere positiva.")
    if maximum_explicit <= 0:
        raise ValueError("Il limite esplicito deve essere positivo.")
    if absence_streak <= maximum_explicit:
        return str(absence_streak)
    return f"{maximum_explicit + 1}+"


def streak_bucket_sort_key(bucket: str) -> int:
    return int(bucket[:-1] if bucket.endswith("+") else bucket)


def summarize_return(
    observations: Sequence[DigitReturnObservation],
) -> ReturnSummary:
    total = len(observations)
    hits = sum(observation.hit for observation in observations)
    observed = hits / total if total else 0.0
    expected = (
        statistics.mean(
            theoretical_hit_probability(observation.digit, observation.position)
            for observation in observations
        )
        if observations
        else 0.0
    )
    return ReturnSummary(
        cases=total,
        hits=hits,
        observed_rate=observed,
        expected_rate=expected,
        delta=observed - expected,
    )


def build_digit_return_report(
    repository: DrawRepository,
    *,
    maximum_explicit_streak: int = 8,
) -> DigitReturnReport:
    observations = tuple(collect_return_observations(repository))
    if not observations:
        raise RuntimeError("Nessuna osservazione disponibile.")

    hazard_tables: list[ReturnHazardTable] = []
    for position in POSITIONS:
        grouped: dict[str, list[DigitReturnObservation]] = defaultdict(list)
        for observation in observations:
            if observation.position != position:
                continue
            grouped[
                streak_bucket(
                    observation.absence_streak,
                    maximum_explicit=maximum_explicit_streak,
                )
            ].append(observation)

        hazard_tables.append(
            ReturnHazardTable(
                position=position,
                groups=tuple(
                    ReturnGroup(key=bucket, summary=summarize_return(grouped[bucket]))
                    for bucket in sorted(grouped, key=streak_bucket_sort_key)
                ),
            )
        )

    any_observations = tuple(
        observation for observation in observations if observation.position == "any"
    )
    by_digit: list[ReturnGroup] = []
    long_by_digit: list[ReturnGroup] = []

    for digit in range(10):
        digit_observations = tuple(
            observation
            for observation in any_observations
            if observation.digit == digit
        )
        by_digit.append(
            ReturnGroup(
                key=digit,
                summary=summarize_return(digit_observations),
                maximum_absence=max(
                    (observation.absence_streak for observation in digit_observations),
                    default=0,
                ),
            )
        )

        long_observations = tuple(
            observation
            for observation in digit_observations
            if observation.absence_streak >= 5
        )
        if long_observations:
            long_by_digit.append(
                ReturnGroup(
                    key=digit,
                    summary=summarize_return(long_observations),
                    maximum_absence=max(
                        observation.absence_streak for observation in long_observations
                    ),
                )
            )

    return DigitReturnReport(
        observations=observations,
        hazard_tables=tuple(hazard_tables),
        any_position_by_digit=tuple(by_digit),
        long_absences_by_digit=tuple(long_by_digit),
    )


def build_digit_coverage_report(
    repository: DrawRepository,
    *,
    max_window_size: int = 3,
) -> DigitCoverageReport:
    if max_window_size <= 0:
        raise ValueError("max_window_size deve essere positivo")

    analysis = analyze_digit_coverage(
        repository,
        max_window_size=max_window_size,
    )

    global_rows: list[GlobalCoverageRow] = []
    absence_rows: list[DigitAbsenceRow] = []
    wheel_rows: list[WheelCoverageRow] = []
    latest_rows: list[LatestCoverageRow] = []

    for window_size, windows in analysis.items():
        total = len(windows)
        missing_distribution = Counter(window.missing_count for window in windows)
        missing_counts = [window.missing_count for window in windows]
        global_rows.append(
            GlobalCoverageRow(
                window_size=window_size,
                windows=total,
                complete=missing_distribution[0],
                one_missing=missing_distribution[1],
                two_missing=missing_distribution[2],
                three_or_more_missing=sum(
                    count
                    for missing_count, count in missing_distribution.items()
                    if missing_count >= 3
                ),
                average_missing=statistics.mean(missing_counts) if missing_counts else 0.0,
                median_missing=statistics.median(missing_counts) if missing_counts else 0.0,
            )
        )

        absence_counts = Counter(
            digit
            for window in windows
            for digit in window.missing_digits
        )
        ranking = sorted(
            range(10),
            key=lambda digit: (-absence_counts[digit], digit),
        )
        absence_rows.extend(
            DigitAbsenceRow(
                window_size=window_size,
                digit=digit,
                absent_windows=absence_counts[digit],
                total_windows=total,
            )
            for digit in ranking
        )

        grouped: dict[str, list[DigitCoverageWindow]] = defaultdict(list)
        wheel_order: dict[str, int] = {}
        latest_by_wheel: dict[str, DigitCoverageWindow] = {}
        for window in windows:
            grouped[window.wheel].append(window)
            wheel_order[window.wheel] = window.wheel_order
            current = latest_by_wheel.get(window.wheel)
            if current is None or (
                window.end_date,
                window.draw_numbers[-1],
            ) > (
                current.end_date,
                current.draw_numbers[-1],
            ):
                latest_by_wheel[window.wheel] = window

        for wheel in sorted(grouped, key=lambda name: wheel_order[name]):
            wheel_windows = grouped[wheel]
            wheel_rows.append(
                WheelCoverageRow(
                    window_size=window_size,
                    wheel=wheel,
                    wheel_order=wheel_order[wheel],
                    windows=len(wheel_windows),
                    complete_windows=sum(
                        window.missing_count == 0 for window in wheel_windows
                    ),
                    at_most_one_missing_windows=sum(
                        window.missing_count <= 1 for window in wheel_windows
                    ),
                    average_missing=statistics.mean(
                        window.missing_count for window in wheel_windows
                    ),
                )
            )
            latest_rows.append(
                LatestCoverageRow(
                    window_size=window_size,
                    wheel=wheel,
                    wheel_order=wheel_order[wheel],
                    window=latest_by_wheel[wheel],
                )
            )

    return DigitCoverageReport(
        windows_by_size=tuple(
            (window_size, tuple(windows))
            for window_size, windows in analysis.items()
        ),
        global_summary=tuple(global_rows),
        digit_absence=tuple(absence_rows),
        wheel_summary=tuple(wheel_rows),
        latest_windows=tuple(latest_rows),
    )
