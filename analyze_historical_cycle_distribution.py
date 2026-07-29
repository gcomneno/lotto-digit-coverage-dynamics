#!/usr/bin/env python3

"""Confronto descrittivo tra cicli storici e modello esatto."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

from strategies.coverage_completion import ALL_DIGITS
from strategies.coverage_cycle_history import (
    CompletedCoverageCycle,
    WheelCoverageHistory,
    build_wheel_cycle_history,
    flatten_completed_cycles,
    merge_draws_by_wheel,
)
from strategies.coverage_markov import (
    absorption_probability_mass,
    absorption_quantiles,
    expected_remaining_draws,
    variance_remaining_draws,
)
from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
)


PRIMARY_DATABASES = (
    Path("data/lotto-2023.sqlite3"),
    Path("data/lotto-2024.sqlite3"),
    Path("data/lotto-2025.sqlite3"),
)

SECONDARY_DATABASES = (
    Path("data/lotto-2026.sqlite3"),
)

DEFAULT_TEXT_OUTPUT = Path(
    "_work/historical-cycle-comparison.txt"
)

DEFAULT_JSON_OUTPUT = Path(
    "_work/historical-cycle-comparison.json"
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


def empirical_quantile(
    durations: Sequence[int],
    probability: float,
) -> int:
    if not durations:
        raise ValueError(
            "Servono durate per calcolare un quantile."
        )

    if not 0.0 < probability < 1.0:
        raise ValueError(
            "La probabilità deve essere compresa "
            "strettamente tra zero e uno."
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
        raise ValueError(
            "Servono cicli completi per il confronto."
        )

    if any(duration <= 0 for duration in durations):
        raise ValueError(
            "Le durate devono essere interi positivi."
        )

    theoretical_quantiles = absorption_quantiles(
        ALL_DIGITS,
        (0.99,),
    )

    horizon = (
        comparison_horizon
        if comparison_horizon is not None
        else max(
            max(durations),
            theoretical_quantiles[0.99],
        )
    )

    if horizon <= 0:
        raise ValueError(
            "L'orizzonte deve essere positivo."
        )

    theoretical_mass = absorption_probability_mass(
        ALL_DIGITS,
        horizon,
    )

    total = len(durations)
    counts = {
        duration: durations.count(duration)
        for duration in set(durations)
    }

    rows: list[DurationComparisonRow] = []
    observed_cumulative = 0.0
    theoretical_cumulative = 0.0

    for duration in range(1, horizon + 1):
        observed_count = counts.get(duration, 0)
        observed_probability = observed_count / total
        theoretical_probability = theoretical_mass[
            duration
        ]

        observed_cumulative += observed_probability
        theoretical_cumulative += (
            theoretical_probability
        )

        expected_count = (
            total * theoretical_probability
        )

        rows.append(
            DurationComparisonRow(
                duration=duration,
                observed_count=observed_count,
                observed_probability=(
                    observed_probability
                ),
                observed_cdf=observed_cumulative,
                theoretical_probability=(
                    theoretical_probability
                ),
                theoretical_cdf=(
                    theoretical_cumulative
                ),
                expected_count=expected_count,
                count_difference=(
                    observed_count - expected_count
                ),
            )
        )

    return tuple(rows)


def summarize_durations(
    durations: Sequence[int],
    rows: Sequence[DurationComparisonRow],
) -> CycleDistributionSummary:
    if not durations:
        raise ValueError(
            "Servono cicli completi per il riepilogo."
        )

    if not rows:
        raise ValueError(
            "Servono righe di confronto."
        )

    theoretical_mean = expected_remaining_draws(
        ALL_DIGITS
    )

    theoretical_variance = (
        variance_remaining_draws(ALL_DIGITS)
    )

    theoretical_quantiles = absorption_quantiles(
        ALL_DIGITS,
        (0.50, 0.90, 0.95, 0.99),
    )

    observed_mean = statistics.fmean(durations)
    observed_variance = statistics.pvariance(
        durations
    )

    cdf_errors = [
        abs(
            row.observed_cdf
            - row.theoretical_cdf
        )
        for row in rows
    ]

    theoretical_tail = max(
        0.0,
        1.0 - rows[-1].theoretical_cdf,
    )

    return CycleDistributionSummary(
        cycle_count=len(durations),
        minimum_duration=min(durations),
        maximum_duration=max(durations),
        observed_mean=observed_mean,
        theoretical_mean=theoretical_mean,
        mean_difference=(
            observed_mean - theoretical_mean
        ),
        observed_variance=observed_variance,
        theoretical_variance=(
            theoretical_variance
        ),
        variance_difference=(
            observed_variance
            - theoretical_variance
        ),
        observed_standard_deviation=(
            math.sqrt(observed_variance)
        ),
        theoretical_standard_deviation=(
            math.sqrt(theoretical_variance)
        ),
        observed_quantile_50=empirical_quantile(
            durations,
            0.50,
        ),
        theoretical_quantile_50=(
            theoretical_quantiles[0.50]
        ),
        observed_quantile_90=empirical_quantile(
            durations,
            0.90,
        ),
        theoretical_quantile_90=(
            theoretical_quantiles[0.90]
        ),
        observed_quantile_95=empirical_quantile(
            durations,
            0.95,
        ),
        theoretical_quantile_95=(
            theoretical_quantiles[0.95]
        ),
        observed_quantile_99=empirical_quantile(
            durations,
            0.99,
        ),
        theoretical_quantile_99=(
            theoretical_quantiles[0.99]
        ),
        cdf_mean_absolute_error=(
            statistics.fmean(cdf_errors)
        ),
        cdf_maximum_absolute_error=max(
            cdf_errors
        ),
        theoretical_tail_after_horizon=(
            theoretical_tail
        ),
        comparison_horizon=rows[-1].duration,
    )


def load_database_collection(
    path: Path,
) -> Mapping[
    str,
    Sequence[DrawSnapshot],
]:
    with LottoRepository(path) as repository:
        return load_draws_by_wheel(repository)


def analyze_segment(
    label: str,
    database_paths: Sequence[Path],
) -> SegmentAnalysis:
    if not database_paths:
        raise ValueError(
            "Serve almeno un database per segmento."
        )

    collections = [
        load_database_collection(path)
        for path in database_paths
    ]

    merged = merge_draws_by_wheel(
        collections
    )

    histories = tuple(
        build_wheel_cycle_history(draws)
        for draws in merged.values()
    )

    cycles = flatten_completed_cycles(
        histories
    )

    durations = [
        cycle.draws_in_cycle
        for cycle in cycles
    ]

    rows = build_duration_comparison(
        durations
    )

    summary = summarize_durations(
        durations,
        rows,
    )

    first_date = min(
        history.first_date
        for history in histories
    )

    last_date = max(
        history.last_date
        for history in histories
    )

    return SegmentAnalysis(
        label=label,
        database_paths=tuple(
            str(path)
            for path in database_paths
        ),
        first_date=first_date,
        last_date=last_date,
        histories=histories,
        cycles=cycles,
        summary=summary,
        duration_rows=rows,
    )


def render_segment(
    segment: SegmentAnalysis,
) -> list[str]:
    summary = segment.summary

    lines = [
        f"===== {segment.label.upper()} =====",
        "",
        (
            f"Periodo:                 "
            f"{segment.first_date} → "
            f"{segment.last_date}"
        ),
        (
            "Database:                "
            + ", ".join(
                segment.database_paths
            )
        ),
        (
            f"Ruote:                  "
            f"{len(segment.histories)}"
        ),
        (
            f"Cicli completi:         "
            f"{summary.cycle_count}"
        ),
        (
            f"Durata minima/massima:  "
            f"{summary.minimum_duration} / "
            f"{summary.maximum_duration}"
        ),
        "",
        "Momenti:",
        (
            f"  media osservata:      "
            f"{summary.observed_mean:.6f}"
        ),
        (
            f"  media teorica:        "
            f"{summary.theoretical_mean:.6f}"
        ),
        (
            f"  differenza media:     "
            f"{summary.mean_difference:+.6f}"
        ),
        (
            f"  varianza osservata:   "
            f"{summary.observed_variance:.6f}"
        ),
        (
            f"  varianza teorica:     "
            f"{summary.theoretical_variance:.6f}"
        ),
        (
            f"  differenza varianza:  "
            f"{summary.variance_difference:+.6f}"
        ),
        "",
        "Quantili osservati / teorici:",
        (
            f"  Q50:                  "
            f"{summary.observed_quantile_50} / "
            f"{summary.theoretical_quantile_50}"
        ),
        (
            f"  Q90:                  "
            f"{summary.observed_quantile_90} / "
            f"{summary.theoretical_quantile_90}"
        ),
        (
            f"  Q95:                  "
            f"{summary.observed_quantile_95} / "
            f"{summary.theoretical_quantile_95}"
        ),
        (
            f"  Q99:                  "
            f"{summary.observed_quantile_99} / "
            f"{summary.theoretical_quantile_99}"
        ),
        "",
        "Errore descrittivo della CDF:",
        (
            f"  medio assoluto:       "
            f"{summary.cdf_mean_absolute_error:.4%}"
        ),
        (
            f"  massimo assoluto:     "
            f"{summary.cdf_maximum_absolute_error:.4%}"
        ),
        (
            f"  coda teorica oltre "
            f"{summary.comparison_horizon}: "
            f"{summary.theoretical_tail_after_horizon:.6%}"
        ),
        "",
        "Distribuzione delle durate:",
        "",
        (
            "Durata  Osservati  Attesi    "
            "P osservata  P teorica  "
            "CDF osservata  CDF teorica"
        ),
        (
            "------  ----------  --------  "
            "-----------  ---------  "
            "-------------  -----------"
        ),
    ]

    for row in segment.duration_rows:
        lines.append(
            f"{row.duration:<8}"
            f"{row.observed_count:<12}"
            f"{row.expected_count:<10.3f}"
            f"{row.observed_probability:>10.2%}  "
            f"{row.theoretical_probability:>8.2%}  "
            f"{row.observed_cdf:>12.2%}  "
            f"{row.theoretical_cdf:>10.2%}"
        )

    lines.extend(
        [
            "",
            "Riepilogo per ruota:",
            "",
            (
                "Ruota        Cicli  Media   "
                "Iniziale censurato  "
                "Finale censurato  Mancanti finali"
            ),
            (
                "------------  -----  ------  "
                "------------------  "
                "---------------  ---------------"
            ),
        ]
    )

    for history in segment.histories:
        durations = [
            cycle.draws_in_cycle
            for cycle
            in history.completed_cycles
        ]

        mean = (
            statistics.fmean(durations)
            if durations
            else 0.0
        )

        missing = (
            "{"
            + ",".join(
                str(digit)
                for digit in sorted(
                    history
                    .right_censored_missing_digits
                )
            )
            + "}"
        )

        lines.append(
            f"{history.wheel:<14}"
            f"{len(durations):<7}"
            f"{mean:<8.3f}"
            f"{history.initial_left_censored_draws:<20}"
            f"{history.right_censored_draws:<17}"
            f"{missing}"
        )

    lines.append("")

    return lines


def render_report(
    primary: SegmentAnalysis,
    secondary: SegmentAnalysis,
) -> str:
    lines = [
        "===== CONFRONTO STORICO DEI CICLI DI COPERTURA =====",
        "",
        (
            "Il rapporto confronta le durate dei cicli naturali "
            "completi con la distribuzione esatta del tempo di "
            "assorbimento dallo stato {0,1,2,3,4,5,6,7,8,9}."
        ),
        "",
        "Regole di osservazione:",
        (
            "- il primo ciclo di ogni ruota e segmento è "
            "escluso perché censurato a sinistra;"
        ),
        (
            "- l'ultimo ciclo incompleto è registrato ma "
            "escluso dalle durate complete;"
        ),
        (
            "- il segmento 2026 è separato dal 2023–2025 "
            "perché mancano le estrazioni 1–59 del 2026;"
        ),
        (
            "- le ruote condividono il calendario delle "
            "estrazioni e non sono trattate come osservazioni "
            "indipendenti;"
        ),
        (
            "- il confronto è descrittivo, non un test "
            "inferenziale e non una regola predittiva."
        ),
        "",
    ]

    lines.extend(render_segment(primary))
    lines.extend(render_segment(secondary))

    return "\n".join(lines)


def segment_to_json(
    segment: SegmentAnalysis,
) -> dict[str, object]:
    return {
        "label": segment.label,
        "database_paths": list(
            segment.database_paths
        ),
        "first_date": segment.first_date,
        "last_date": segment.last_date,
        "summary": asdict(segment.summary),
        "wheel_histories": [
            {
                **asdict(history),
                "right_censored_missing_digits": (
                    sorted(
                        history
                        .right_censored_missing_digits
                    )
                ),
                "completed_cycles": [
                    asdict(cycle)
                    for cycle
                    in history.completed_cycles
                ],
            }
            for history in segment.histories
        ],
        "duration_rows": [
            asdict(row)
            for row in segment.duration_rows
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta le durate storiche complete "
            "con la distribuzione teorica."
        )
    )

    parser.add_argument(
        "--primary-databases",
        nargs="+",
        type=Path,
        default=list(PRIMARY_DATABASES),
    )

    parser.add_argument(
        "--secondary-databases",
        nargs="+",
        type=Path,
        default=list(SECONDARY_DATABASES),
    )

    parser.add_argument(
        "--text-output",
        type=Path,
        default=DEFAULT_TEXT_OUTPUT,
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        primary = analyze_segment(
            "Segmento continuo 2023–2025",
            args.primary_databases,
        )

        secondary = analyze_segment(
            "Segmento parziale 2026",
            args.secondary_databases,
        )

        report = render_report(
            primary,
            secondary,
        )

        args.text_output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.json_output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.text_output.write_text(
            report + "\n"
        )

        document = {
            "report_format_version": 1,
            "report_type": (
                "historical-cycle-distribution-comparison"
            ),
            "interpretation": (
                "Descriptive mathematical comparison; "
                "not an inferential test or betting rule."
            ),
            "primary_segment": segment_to_json(
                primary
            ),
            "secondary_segment": segment_to_json(
                secondary
            ),
        }

        args.json_output.write_text(
            json.dumps(
                document,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        print(report)
        print(
            f"Rapporto testuale: {args.text_output}"
        )
        print(
            f"Rapporto JSON:     {args.json_output}"
        )

    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
