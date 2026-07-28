#!/usr/bin/env python3

"""Stabilità temporale e per ruota delle classi candidate."""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from analyze_historical_symmetry_classes import (
    ClassObservation,
    DEFAULT_DATABASES,
    build_all_observations,
    build_empirical_rows,
    csv_value,
    load_merged_draws,
)


CANDIDATE_CLASS_IDS = (
    "nine-no-zero:1",
    "nine-no-zero:3",
)

DEFAULT_YEAR_CSV_OUTPUT = Path(
    "_work/symmetry-candidates-by-year.csv"
)

DEFAULT_WHEEL_CSV_OUTPUT = Path(
    "_work/symmetry-candidates-by-wheel.csv"
)

DEFAULT_JSON_OUTPUT = Path(
    "_work/symmetry-candidate-stability.json"
)


@dataclass(frozen=True)
class CandidateBreakdownRow:
    class_id: str
    dimension: str
    segment: str
    segment_order: int
    observations: int
    distinct_target_dates: int
    observed_completions: int
    expected_completions: float
    theoretical_probability: float
    observed_frequency: float | None
    difference_probability: float | None
    difference_percentage_points: float | None
    naive_standardized_residual: float | None
    direction: str


@dataclass(frozen=True)
class CandidateStabilityRow:
    class_id: str
    observations: int
    observed_completions: int
    expected_completions: float
    theoretical_probability: float
    observed_frequency: float
    difference_percentage_points: float
    observed_years: int
    positive_years: tuple[str, ...]
    negative_years: tuple[str, ...]
    neutral_years: tuple[str, ...]
    yearly_direction_consistent: bool
    observed_wheels: int
    positive_wheels: tuple[str, ...]
    negative_wheels: tuple[str, ...]
    neutral_wheels: tuple[str, ...]
    largest_wheel: str
    largest_wheel_observations: int
    largest_wheel_observation_share: float


def candidate_probabilities() -> dict[str, float]:
    probabilities = {
        row.class_id: row.theoretical_probability
        for row in build_empirical_rows(())
        if row.class_id in CANDIDATE_CLASS_IDS
    }

    if set(probabilities) != set(
        CANDIDATE_CLASS_IDS
    ):
        raise RuntimeError(
            "Definizione incompleta delle classi candidate."
        )

    return probabilities


def observation_segment(
    observation: ClassObservation,
    dimension: str,
) -> tuple[str, int]:
    if dimension == "year":
        if (
            len(observation.target_date) < 4
            or not observation.target_date[:4].isdigit()
        ):
            raise ValueError(
                "Data target non valida: "
                f"{observation.target_date}."
            )

        year = observation.target_date[:4]

        return year, int(year)

    if dimension == "wheel":
        return (
            observation.wheel,
            observation.wheel_order,
        )

    raise ValueError(
        "La dimensione deve essere 'year' o 'wheel'."
    )


def direction_from_difference(
    difference: float | None,
    *,
    tolerance: float = 1e-15,
) -> str:
    if difference is None:
        return "no-data"

    if difference > tolerance:
        return "positive"

    if difference < -tolerance:
        return "negative"

    return "neutral"


def build_breakdown_rows(
    observations: Sequence[ClassObservation],
    *,
    dimension: str,
) -> tuple[CandidateBreakdownRow, ...]:
    probabilities = candidate_probabilities()

    segments: dict[str, int] = {}

    for observation in observations:
        segment, order = observation_segment(
            observation,
            dimension,
        )

        previous = segments.get(segment)

        if (
            previous is not None
            and previous != order
        ):
            raise ValueError(
                f"Ordine incoerente per {segment}."
            )

        segments[segment] = order

    grouped: dict[
        tuple[str, str],
        list[ClassObservation],
    ] = defaultdict(list)

    for observation in observations:
        if (
            observation.class_id
            not in CANDIDATE_CLASS_IDS
        ):
            continue

        segment, _ = observation_segment(
            observation,
            dimension,
        )

        expected_probability = probabilities[
            observation.class_id
        ]

        if not math.isclose(
            observation.theoretical_probability,
            expected_probability,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise RuntimeError(
                "Probabilità teorica incoerente per "
                f"{observation.class_id}."
            )

        grouped[
            observation.class_id,
            segment,
        ].append(observation)

    rows: list[CandidateBreakdownRow] = []

    ordered_segments = sorted(
        segments.items(),
        key=lambda item: (
            item[1],
            item[0],
        ),
    )

    for class_id in CANDIDATE_CLASS_IDS:
        probability = probabilities[class_id]

        for segment, segment_order in (
            ordered_segments
        ):
            selected = grouped.get(
                (
                    class_id,
                    segment,
                ),
                [],
            )

            observation_count = len(selected)

            completions = sum(
                observation.completed_next
                for observation in selected
            )

            expected_completions = (
                observation_count
                * probability
            )

            if observation_count:
                observed_frequency = (
                    completions
                    / observation_count
                )

                difference = (
                    observed_frequency
                    - probability
                )

                variance = (
                    observation_count
                    * probability
                    * (1.0 - probability)
                )

                standardized_residual = (
                    (
                        completions
                        - expected_completions
                    )
                    / math.sqrt(variance)
                    if variance > 0.0
                    else None
                )
            else:
                observed_frequency = None
                difference = None
                standardized_residual = None

            rows.append(
                CandidateBreakdownRow(
                    class_id=class_id,
                    dimension=dimension,
                    segment=segment,
                    segment_order=segment_order,
                    observations=observation_count,
                    distinct_target_dates=len(
                        {
                            observation.target_date
                            for observation in selected
                        }
                    ),
                    observed_completions=(
                        completions
                    ),
                    expected_completions=(
                        expected_completions
                    ),
                    theoretical_probability=(
                        probability
                    ),
                    observed_frequency=(
                        observed_frequency
                    ),
                    difference_probability=(
                        difference
                    ),
                    difference_percentage_points=(
                        None
                        if difference is None
                        else 100.0 * difference
                    ),
                    naive_standardized_residual=(
                        standardized_residual
                    ),
                    direction=(
                        direction_from_difference(
                            difference
                        )
                    ),
                )
            )

    return tuple(rows)


def validate_breakdown_rows(
    rows: Sequence[CandidateBreakdownRow],
    observations: Sequence[ClassObservation],
    *,
    dimension: str,
) -> None:
    candidate_observations = [
        observation
        for observation in observations
        if observation.class_id
        in CANDIDATE_CLASS_IDS
    ]

    keys = {
        (
            row.class_id,
            row.dimension,
            row.segment,
        )
        for row in rows
    }

    if len(keys) != len(rows):
        raise RuntimeError(
            "Righe duplicate nel breakdown."
        )

    for row in rows:
        if row.dimension != dimension:
            raise RuntimeError(
                "Dimensione incoerente nel breakdown."
            )

        if row.observations == 0:
            if (
                row.observed_frequency
                is not None
                or row.difference_probability
                is not None
                or row.naive_standardized_residual
                is not None
                or row.direction != "no-data"
            ):
                raise RuntimeError(
                    "Riga senza dati valorizzata."
                )

            continue

        expected_frequency = (
            row.observed_completions
            / row.observations
        )

        if not math.isclose(
            row.observed_frequency or 0.0,
            expected_frequency,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise RuntimeError(
                "Frequenza osservata incoerente."
            )

    for class_id in CANDIDATE_CLASS_IDS:
        expected_total = sum(
            observation.class_id == class_id
            for observation
            in candidate_observations
        )

        actual_total = sum(
            row.observations
            for row in rows
            if row.class_id == class_id
        )

        if actual_total != expected_total:
            raise RuntimeError(
                "Totale non conservato per "
                f"{class_id}: "
                f"{actual_total} invece di "
                f"{expected_total}."
            )


def build_stability_rows(
    year_rows: Sequence[CandidateBreakdownRow],
    wheel_rows: Sequence[CandidateBreakdownRow],
) -> tuple[CandidateStabilityRow, ...]:
    results: list[CandidateStabilityRow] = []

    for class_id in CANDIDATE_CLASS_IDS:
        years = [
            row
            for row in year_rows
            if (
                row.class_id == class_id
                and row.observations > 0
            )
        ]

        wheels = [
            row
            for row in wheel_rows
            if (
                row.class_id == class_id
                and row.observations > 0
            )
        ]

        observations = sum(
            row.observations
            for row in years
        )

        completions = sum(
            row.observed_completions
            for row in years
        )

        if observations == 0:
            raise RuntimeError(
                "Classe candidata priva di dati: "
                f"{class_id}."
            )

        probability = years[
            0
        ].theoretical_probability

        observed_frequency = (
            completions / observations
        )

        positive_years = tuple(
            row.segment
            for row in years
            if row.direction == "positive"
        )

        negative_years = tuple(
            row.segment
            for row in years
            if row.direction == "negative"
        )

        neutral_years = tuple(
            row.segment
            for row in years
            if row.direction == "neutral"
        )

        year_directions = {
            row.direction
            for row in years
            if row.direction != "neutral"
        }

        positive_wheels = tuple(
            row.segment
            for row in wheels
            if row.direction == "positive"
        )

        negative_wheels = tuple(
            row.segment
            for row in wheels
            if row.direction == "negative"
        )

        neutral_wheels = tuple(
            row.segment
            for row in wheels
            if row.direction == "neutral"
        )

        largest_wheel = max(
            wheels,
            key=lambda row: (
                row.observations,
                -row.segment_order,
            ),
        )

        results.append(
            CandidateStabilityRow(
                class_id=class_id,
                observations=observations,
                observed_completions=(
                    completions
                ),
                expected_completions=(
                    observations * probability
                ),
                theoretical_probability=(
                    probability
                ),
                observed_frequency=(
                    observed_frequency
                ),
                difference_percentage_points=(
                    100.0
                    * (
                        observed_frequency
                        - probability
                    )
                ),
                observed_years=len(years),
                positive_years=positive_years,
                negative_years=negative_years,
                neutral_years=neutral_years,
                yearly_direction_consistent=(
                    len(year_directions) == 1
                    and not neutral_years
                ),
                observed_wheels=len(wheels),
                positive_wheels=positive_wheels,
                negative_wheels=negative_wheels,
                neutral_wheels=neutral_wheels,
                largest_wheel=(
                    largest_wheel.segment
                ),
                largest_wheel_observations=(
                    largest_wheel.observations
                ),
                largest_wheel_observation_share=(
                    largest_wheel.observations
                    / observations
                ),
            )
        )

    return tuple(results)


def write_csv(
    rows: Sequence[CandidateBreakdownRow],
    output: Path,
) -> None:
    if not rows:
        raise ValueError(
            "Servono righe da scrivere."
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    documents = [
        asdict(row)
        for row in rows
    ]

    with output.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(
                documents[0].keys()
            ),
            lineterminator="\n",
        )

        writer.writeheader()

        for document in documents:
            writer.writerow(
                {
                    key: csv_value(value)
                    for key, value
                    in document.items()
                }
            )


def write_json(
    year_rows: Sequence[CandidateBreakdownRow],
    wheel_rows: Sequence[CandidateBreakdownRow],
    stability_rows: Sequence[CandidateStabilityRow],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = {
        "report_format_version": 1,
        "report_type": (
            "symmetry-candidate-stability"
        ),
        "segment": "2023-2025",
        "candidate_class_ids": list(
            CANDIDATE_CLASS_IDS
        ),
        "caution": (
            "Descriptive breakdown. Wheels share "
            "the draw calendar; standardized "
            "residuals use a naive binomial scale "
            "and are not inferential p-values."
        ),
        "by_year": [
            asdict(row)
            for row in year_rows
        ],
        "by_wheel": [
            asdict(row)
            for row in wheel_rows
        ],
        "stability": [
            asdict(row)
            for row in stability_rows
        ],
    }

    output.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def format_percentage(
    value: float | None,
) -> str:
    if value is None:
        return "—"

    return f"{value:.3%}"


def format_decimal(
    value: float | None,
    *,
    signed: bool = False,
) -> str:
    if value is None:
        return "—"

    if signed:
        return f"{value:+.3f}"

    return f"{value:.3f}"


def render_rows(
    rows: Sequence[CandidateBreakdownRow],
    *,
    class_id: str,
) -> str:
    selected = [
        row
        for row in rows
        if row.class_id == class_id
    ]

    lines = [
        (
            "Segmento       N  Date  Hit   Attesi  "
            "Teoria  Osservata  Diff.pp      z"
        ),
        (
            "------------ ---- ----- ---- -------- "
            "------- ---------- -------- ------"
        ),
    ]

    for row in selected:
        lines.append(
            f"{row.segment:<12} "
            f"{row.observations:>4} "
            f"{row.distinct_target_dates:>5} "
            f"{row.observed_completions:>4} "
            f"{row.expected_completions:>8.2f} "
            f"{row.theoretical_probability:>7.3%} "
            f"{format_percentage(row.observed_frequency):>10} "
            f"{format_decimal(row.difference_percentage_points, signed=True):>8} "
            f"{format_decimal(row.naive_standardized_residual, signed=True):>6}"
        )

    return "\n".join(lines)


def render_stability(
    row: CandidateStabilityRow,
) -> str:
    return "\n".join(
        (
            f"Classe: {row.class_id}",
            (
                "  Totale: "
                f"{row.observations} osservazioni, "
                f"{row.observed_completions} hit, "
                f"{row.difference_percentage_points:+.3f} pp"
            ),
            (
                "  Anni positivi: "
                + (
                    ", ".join(row.positive_years)
                    or "nessuno"
                )
            ),
            (
                "  Anni negativi: "
                + (
                    ", ".join(row.negative_years)
                    or "nessuno"
                )
            ),
            (
                "  Segno annuale coerente: "
                + (
                    "sì"
                    if row.yearly_direction_consistent
                    else "no"
                )
            ),
            (
                "  Ruote positive: "
                f"{len(row.positive_wheels)} / "
                f"{row.observed_wheels}"
            ),
            (
                "  Ruote negative: "
                f"{len(row.negative_wheels)} / "
                f"{row.observed_wheels}"
            ),
            (
                "  Ruota con più casi: "
                f"{row.largest_wheel} "
                f"({row.largest_wheel_observations}, "
                f"{row.largest_wheel_observation_share:.1%})"
            ),
        )
    )


def main() -> int:
    try:
        draws_by_wheel = load_merged_draws(
            DEFAULT_DATABASES
        )

        observations = build_all_observations(
            draws_by_wheel
        )

        year_rows = build_breakdown_rows(
            observations,
            dimension="year",
        )

        wheel_rows = build_breakdown_rows(
            observations,
            dimension="wheel",
        )

        validate_breakdown_rows(
            year_rows,
            observations,
            dimension="year",
        )

        validate_breakdown_rows(
            wheel_rows,
            observations,
            dimension="wheel",
        )

        stability_rows = build_stability_rows(
            year_rows,
            wheel_rows,
        )

        write_csv(
            year_rows,
            DEFAULT_YEAR_CSV_OUTPUT,
        )

        write_csv(
            wheel_rows,
            DEFAULT_WHEEL_CSV_OUTPUT,
        )

        write_json(
            year_rows,
            wheel_rows,
            stability_rows,
            DEFAULT_JSON_OUTPUT,
        )

        for class_id in CANDIDATE_CLASS_IDS:
            print(
                f"===== {class_id} — PER ANNO ====="
            )
            print(
                render_rows(
                    year_rows,
                    class_id=class_id,
                )
            )
            print()

            print(
                f"===== {class_id} — PER RUOTA ====="
            )
            print(
                render_rows(
                    wheel_rows,
                    class_id=class_id,
                )
            )
            print()

        print(
            "===== RIEPILOGO STABILITÀ ====="
        )

        for row in stability_rows:
            print(render_stability(row))
            print()

        print(
            f"CSV anni:  {DEFAULT_YEAR_CSV_OUTPUT}"
        )

        print(
            f"CSV ruote: {DEFAULT_WHEEL_CSV_OUTPUT}"
        )

        print(
            f"JSON:      {DEFAULT_JSON_OUTPUT}"
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
