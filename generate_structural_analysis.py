#!/usr/bin/env python3

"""Genera l'atlante delle classi strutturali di copertura."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from strategies.coverage_markov import (
    maturity_metrics,
    transition_distribution,
)
from strategies.coverage_structure import (
    StateSymmetryClass,
    allowed_number_count_closed_form,
    group_nonempty_states_by_symmetry,
    state_symmetry_class,
    verify_structural_symmetry,
)


HORIZONS = (1, 2, 3, 5, 10)
QUANTILES = (0.50, 0.90, 0.95, 0.99)

DEFAULT_CLASSES_CSV = Path(
    "generated/coverage-symmetry-classes.csv"
)

DEFAULT_CARDINALITY_CSV = Path(
    "generated/coverage-cardinality-loss.csv"
)

DEFAULT_JSON_OUTPUT = Path(
    "generated/coverage-structural-analysis.json"
)

DEFAULT_SUMMARY_OUTPUT = Path(
    "docs/structural-symmetry-analysis.md"
)

FAMILY_ORDER = {
    "no-nine": 0,
    "nine-no-zero": 1,
    "zero-nine": 2,
}


@dataclass(frozen=True)
class SymmetryClassRow:
    class_id: str
    family: str
    exchangeable_count: int
    missing_count: int
    state_multiplicity: int
    canonical_state: str
    contains_zero: bool
    contains_nine: bool
    allowed_numbers_avoiding_state: int
    self_transition_probability: float
    completion_probability_within_1: float
    completion_probability_within_2: float
    completion_probability_within_3: float
    completion_probability_within_5: float
    completion_probability_within_10: float
    expected_remaining_draws: float
    variance_remaining_draws: float
    standard_deviation_remaining_draws: float
    quantile_50_draws: int
    quantile_90_draws: int
    quantile_95_draws: int
    quantile_99_draws: int


@dataclass(frozen=True)
class CardinalityLossRow:
    missing_count: int
    state_count: int
    structural_class_count: int
    count_only_expected_mean: float
    minimum_expected_remaining_draws: float
    maximum_expected_remaining_draws: float
    expected_range: float
    expected_weighted_rmse: float
    expected_maximum_absolute_error: float
    count_only_completion_probability_1: float
    minimum_completion_probability_1: float
    maximum_completion_probability_1: float
    completion_probability_1_range: float
    completion_probability_1_weighted_rmse: float
    completion_probability_1_maximum_absolute_error: float
    easiest_class_id: str
    hardest_class_id: str


def format_state(
    digits: Sequence[int],
) -> str:
    return (
        "{"
        + ",".join(
            str(digit)
            for digit in digits
        )
        + "}"
    )


def class_identifier(
    symmetry_class: StateSymmetryClass,
) -> str:
    return (
        f"{symmetry_class.family}:"
        f"{symmetry_class.exchangeable_count}"
    )


def class_sort_key(
    row: SymmetryClassRow,
) -> tuple[int, int, int]:
    return (
        row.missing_count,
        FAMILY_ORDER[row.family],
        row.exchangeable_count,
    )


def build_symmetry_class_rows() -> tuple[
    SymmetryClassRow,
    ...,
]:
    groups = (
        group_nonempty_states_by_symmetry()
    )

    rows: list[SymmetryClassRow] = []

    for symmetry_class, states in groups.items():
        canonical = (
            symmetry_class.canonical_state
        )

        metrics = maturity_metrics(
            canonical,
            horizons=HORIZONS,
            quantiles=QUANTILES,
        )

        completion = metrics[
            "completion_within"
        ]

        quantiles = metrics[
            "absorption_quantiles"
        ]

        variance = float(
            metrics["variance_remaining_draws"]
        )

        self_probability = (
            transition_distribution(
                canonical
            ).get(canonical, 0.0)
        )

        rows.append(
            SymmetryClassRow(
                class_id=class_identifier(
                    symmetry_class
                ),
                family=(
                    symmetry_class.family
                ),
                exchangeable_count=(
                    symmetry_class
                    .exchangeable_count
                ),
                missing_count=(
                    symmetry_class.missing_count
                ),
                state_multiplicity=len(states),
                canonical_state=format_state(
                    tuple(sorted(canonical))
                ),
                contains_zero=0 in canonical,
                contains_nine=9 in canonical,
                allowed_numbers_avoiding_state=(
                    allowed_number_count_closed_form(
                        canonical
                    )
                ),
                self_transition_probability=(
                    self_probability
                ),
                completion_probability_within_1=(
                    float(completion[1])
                ),
                completion_probability_within_2=(
                    float(completion[2])
                ),
                completion_probability_within_3=(
                    float(completion[3])
                ),
                completion_probability_within_5=(
                    float(completion[5])
                ),
                completion_probability_within_10=(
                    float(completion[10])
                ),
                expected_remaining_draws=float(
                    metrics[
                        "expected_remaining_draws"
                    ]
                ),
                variance_remaining_draws=(
                    variance
                ),
                standard_deviation_remaining_draws=(
                    math.sqrt(variance)
                ),
                quantile_50_draws=int(
                    quantiles[0.50]
                ),
                quantile_90_draws=int(
                    quantiles[0.90]
                ),
                quantile_95_draws=int(
                    quantiles[0.95]
                ),
                quantile_99_draws=int(
                    quantiles[0.99]
                ),
            )
        )

    return tuple(
        sorted(
            rows,
            key=class_sort_key,
        )
    )


def weighted_mean(
    values: Sequence[tuple[float, int]],
) -> float:
    total_weight = sum(
        weight
        for _, weight in values
    )

    if total_weight <= 0:
        raise ValueError(
            "Il peso complessivo deve essere positivo."
        )

    return (
        sum(
            value * weight
            for value, weight in values
        )
        / total_weight
    )


def weighted_rmse(
    values: Sequence[tuple[float, int]],
    reference: float,
) -> float:
    total_weight = sum(
        weight
        for _, weight in values
    )

    return math.sqrt(
        sum(
            weight * (value - reference) ** 2
            for value, weight in values
        )
        / total_weight
    )


def build_cardinality_loss_rows(
    class_rows: Sequence[SymmetryClassRow],
) -> tuple[CardinalityLossRow, ...]:
    groups: dict[
        int,
        list[SymmetryClassRow],
    ] = defaultdict(list)

    for row in class_rows:
        groups[row.missing_count].append(
            row
        )

    result: list[CardinalityLossRow] = []

    for missing_count in range(1, 11):
        rows = groups[missing_count]

        expected_values = [
            (
                row.expected_remaining_draws,
                row.state_multiplicity,
            )
            for row in rows
        ]

        probability_values = [
            (
                row
                .completion_probability_within_1,
                row.state_multiplicity,
            )
            for row in rows
        ]

        expected_mean = weighted_mean(
            expected_values
        )

        probability_mean = weighted_mean(
            probability_values
        )

        expected_minimum = min(
            row.expected_remaining_draws
            for row in rows
        )

        expected_maximum = max(
            row.expected_remaining_draws
            for row in rows
        )

        probability_minimum = min(
            row
            .completion_probability_within_1
            for row in rows
        )

        probability_maximum = max(
            row
            .completion_probability_within_1
            for row in rows
        )

        easiest = min(
            rows,
            key=lambda row: (
                row.expected_remaining_draws,
                row.class_id,
            ),
        )

        hardest = max(
            rows,
            key=lambda row: (
                row.expected_remaining_draws,
                row.class_id,
            ),
        )

        result.append(
            CardinalityLossRow(
                missing_count=missing_count,
                state_count=sum(
                    row.state_multiplicity
                    for row in rows
                ),
                structural_class_count=len(rows),
                count_only_expected_mean=(
                    expected_mean
                ),
                minimum_expected_remaining_draws=(
                    expected_minimum
                ),
                maximum_expected_remaining_draws=(
                    expected_maximum
                ),
                expected_range=(
                    expected_maximum
                    - expected_minimum
                ),
                expected_weighted_rmse=(
                    weighted_rmse(
                        expected_values,
                        expected_mean,
                    )
                ),
                expected_maximum_absolute_error=max(
                    abs(
                        row
                        .expected_remaining_draws
                        - expected_mean
                    )
                    for row in rows
                ),
                count_only_completion_probability_1=(
                    probability_mean
                ),
                minimum_completion_probability_1=(
                    probability_minimum
                ),
                maximum_completion_probability_1=(
                    probability_maximum
                ),
                completion_probability_1_range=(
                    probability_maximum
                    - probability_minimum
                ),
                completion_probability_1_weighted_rmse=(
                    weighted_rmse(
                        probability_values,
                        probability_mean,
                    )
                ),
                completion_probability_1_maximum_absolute_error=max(
                    abs(
                        row
                        .completion_probability_within_1
                        - probability_mean
                    )
                    for row in rows
                ),
                easiest_class_id=(
                    easiest.class_id
                ),
                hardest_class_id=(
                    hardest.class_id
                ),
            )
        )

    return tuple(result)


def validate_analysis(
    class_rows: Sequence[SymmetryClassRow],
    cardinality_rows: Sequence[
        CardinalityLossRow
    ],
    *,
    tolerance: float = 1e-12,
) -> None:
    if len(class_rows) != 27:
        raise RuntimeError(
            "L'analisi deve contenere "
            f"27 classi, non {len(class_rows)}."
        )

    if len(
        {
            row.class_id
            for row in class_rows
        }
    ) != 27:
        raise RuntimeError(
            "Gli identificatori delle classi "
            "non sono univoci."
        )

    if sum(
        row.state_multiplicity
        for row in class_rows
    ) != 1023:
        raise RuntimeError(
            "Le molteplicità non ricostruiscono "
            "i 1.023 stati non vuoti."
        )

    for row in class_rows:
        canonical = tuple(
            int(digit)
            for digit in row.canonical_state
            if digit.isdigit()
        )

        if (
            class_identifier(
                state_symmetry_class(
                    canonical
                )
            )
            != row.class_id
        ):
            raise RuntimeError(
                "Rappresentante canonico incoerente "
                f"per {row.class_id}."
            )

        if row.state_multiplicity <= 0:
            raise RuntimeError(
                "Molteplicità non positiva "
                f"per {row.class_id}."
            )

        if not (
            0.0
            <= row
            .completion_probability_within_1
            <= 1.0
        ):
            raise RuntimeError(
                "Probabilità fuori intervallo "
                f"per {row.class_id}."
            )

    if len(cardinality_rows) != 10:
        raise RuntimeError(
            "Servono dieci righe cardinali."
        )

    expected_class_counts = (
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        1,
    )

    for row, expected_classes in zip(
        cardinality_rows,
        expected_class_counts,
    ):
        if (
            row.structural_class_count
            != expected_classes
        ):
            raise RuntimeError(
                "Numero di classi errato per "
                f"cardinalità {row.missing_count}."
            )

        if row.state_count != math.comb(
            10,
            row.missing_count,
        ):
            raise RuntimeError(
                "Numero di stati errato per "
                f"cardinalità {row.missing_count}."
            )

        if row.expected_range < -tolerance:
            raise RuntimeError(
                "Intervallo atteso negativo."
            )

        if (
            row
            .completion_probability_1_range
            < -tolerance
        ):
            raise RuntimeError(
                "Intervallo probabilistico negativo."
            )

    if any(
        row.expected_range <= tolerance
        for row in cardinality_rows[:-1]
    ):
        raise RuntimeError(
            "La sola cardinalità dovrebbe perdere "
            "informazione per cardinalità 1–9."
        )

    if (
        cardinality_rows[-1].expected_range
        > tolerance
    ):
        raise RuntimeError(
            "La cardinalità 10 contiene un solo stato."
        )


def csv_value(value: object) -> object:
    if isinstance(value, float):
        return format(value, ".17g")

    if isinstance(value, bool):
        return "yes" if value else "no"

    return value


def write_csv(
    rows: Sequence[object],
    output: Path,
) -> None:
    if not rows:
        raise ValueError(
            "Non ci sono righe da scrivere."
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


def build_json_document(
    class_rows: Sequence[SymmetryClassRow],
    cardinality_rows: Sequence[
        CardinalityLossRow
    ],
) -> dict[str, object]:
    verification = (
        verify_structural_symmetry()
    )

    return {
        "report_format_version": 1,
        "report_type": (
            "decimal-digit-coverage-"
            "structural-analysis"
        ),
        "purpose": (
            "Exact symmetry and count-only "
            "information-loss analysis; "
            "not a predictive model."
        ),
        "state_space": {
            "total_states": 1024,
            "absorbing_states": 1,
            "non_empty_states": 1023,
            "non_empty_symmetry_classes": 27,
        },
        "cardinality_aggregation": {
            "weighting": (
                "uniform over exact states within each "
                "missing_count; symmetry-class metrics "
                "are weighted by state_multiplicity"
            ),
            "interpretation": (
                "structural information-loss benchmark; "
                "not empirical state-frequency weighting"
            ),
        },
        "verification": asdict(
            verification
        ),
        "symmetry_classes": [
            asdict(row)
            for row in class_rows
        ],
        "cardinality_loss": [
            asdict(row)
            for row in cardinality_rows
        ],
    }


def family_label(family: str) -> str:
    labels = {
        "no-nine": "senza 9",
        "nine-no-zero": "con 9, senza 0",
        "zero-nine": "con 0 e 9",
    }

    return labels[family]


def build_summary(
    class_rows: Sequence[SymmetryClassRow],
    cardinality_rows: Sequence[
        CardinalityLossRow
    ],
) -> str:
    widest_expected = max(
        cardinality_rows,
        key=lambda row: (
            row.expected_range,
            -row.missing_count,
        ),
    )

    widest_probability = max(
        cardinality_rows,
        key=lambda row: (
            row
            .completion_probability_1_range,
            -row.missing_count,
        ),
    )

    lines = [
        "# Structural symmetry analysis",
        "",
        "## Purpose",
        "",
        (
            "This document identifies the exact symmetry "
            "classes of the decimal digit-coverage process "
            "and quantifies the information lost when a "
            "state is represented only by its number of "
            "missing digits."
        ),
        "",
        (
            "The analysis is mathematical and descriptive. "
            "It is not a prediction or wagering rule."
        ),
        "",
        "## Allowed-number counting theorem",
        "",
        (
            "Let `A` be a set of forbidden decimal digits "
            "and let:"
        ),
        "",
        r"\[",
        r"c = 10 - |A|.",
        r"\]",
        "",
        (
            "Begin with the `c²` ordered pairs made from "
            "allowed digits. Two corrections are needed:"
        ),
        "",
        (
            "1. remove `00` when zero is allowed, because "
            "the Lotto range starts at `01`;"
        ),
        (
            "2. when nine is allowed as the tens digit, "
            "remove every allowed `91–99`; `90` remains "
            "valid."
        ),
        "",
        "Therefore:",
        "",
        r"\[",
        (
            r"N(A)=c^2-\mathbf 1_{0\notin A}"
            r"-\mathbf 1_{9\notin A}"
            r"\left(c-\mathbf 1_{0\notin A}\right)."
        ),
        r"\]",
        "",
        (
            "This formula was checked against direct "
            "enumeration of `01–90` for all 1,024 possible "
            "forbidden-digit sets."
        ),
        "",
        "## Exact symmetry classes",
        "",
        (
            "The transition kernel uses allowed-number "
            "counts for subsets of the current missing "
            "state. The counting theorem implies three "
            "families:"
        ),
        "",
        (
            "- `no-nine`: if 9 is not missing, all missing "
            "digits among 0–8 are exchangeable;"
        ),
        (
            "- `nine-no-zero`: if 9 is missing but 0 is "
            "not, digits 1–8 are exchangeable;"
        ),
        (
            "- `zero-nine`: if both 0 and 9 are missing, "
            "digits 1–8 are exchangeable."
        ),
        "",
        (
            "Their class counts are `9 + 9 + 9 = 27`. "
            "Their state multiplicities sum to 1,023."
        ),
        "",
        (
            "Kernel equivariance was verified over all "
            "1,024 states and all 58,848 stored transition "
            "entries. The maximum discrepancy after "
            "canonical relabelling was exactly zero."
        ),
        "",
        "## Class atlas",
        "",
        (
            "| Class | Family | Missing | States | Canonical "
            "| P(complete in 1) | Expected draws | Q95 |"
        ),
        (
            "|:---|:---|---:|---:|:---|---:|---:|---:|"
        ),
    ]

    for row in class_rows:
        lines.append(
            f"| `{row.class_id}` "
            f"| {family_label(row.family)} "
            f"| {row.missing_count} "
            f"| {row.state_multiplicity} "
            f"| `{row.canonical_state}` "
            f"| {row.completion_probability_within_1:.6%} "
            f"| {row.expected_remaining_draws:.9f} "
            f"| {row.quantile_95_draws} |"
        )

    lines.extend(
        [
            "",
            "## Information loss from cardinality only",
            "",
            (
                "A count-only model replaces all exact states "
                "with the same cardinality by one mean, giving "
                "each exact state equal weight. Because the rows "
                "represent symmetry classes, their metrics are "
                "weighted by `state_multiplicity`."
            ),
            "",
            (
                "This is a structural average over the state "
                "space, not an average weighted by historical "
                "state frequencies."
            ),
            "",
            (
                "| Missing | States | Classes | Mean expected "
                "| Expected range | Expected RMSE | "
                "P1 range |"
            ),
            (
                "|---:|---:|---:|---:|---:|---:|---:|"
            ),
        ]
    )

    for row in cardinality_rows:
        lines.append(
            f"| {row.missing_count} "
            f"| {row.state_count} "
            f"| {row.structural_class_count} "
            f"| {row.count_only_expected_mean:.9f} "
            f"| {row.expected_range:.9f} "
            f"| {row.expected_weighted_rmse:.9f} "
            f"| {row.completion_probability_1_range:.6%} |"
        )

    lines.extend(
        [
            "",
            "## Main structural findings",
            "",
            (
                "States with the same number of missing "
                "digits are not generally equivalent."
            ),
            "",
            (
                f"The largest expected-time range occurs "
                f"at cardinality "
                f"{widest_expected.missing_count}: "
                f"{widest_expected.expected_range:.9f} draws."
            ),
            "",
            (
                f"The largest one-draw completion-probability "
                f"range occurs at cardinality "
                f"{widest_probability.missing_count}: "
                f"{widest_probability.completion_probability_1_range:.6%}."
            ),
            "",
            "Representative equality and inequality:",
            "",
            "```text",
            "E[{0,1}] = E[{2,3}]",
            "E[{1,9}] = E[{8,9}]",
            "E[{0,9}] ≠ E[{1,9}]",
            "```",
            "",
            (
                "The first two equalities follow from exact "
                "symmetry. The final inequality is caused by "
                "the special boundary interaction between "
                "`0`, `9`, `01` and `90` in the range "
                "`01–90`."
            ),
            "",
            (
                "Cardinality 10 is the only non-empty "
                "cardinality containing a single exact state. "
                "For cardinalities 1–9, count-only summaries "
                "discard measurable state-identity information."
            ),
            "",
            "## Reproduction",
            "",
            "```bash",
            "python3 generate_structural_analysis.py",
            "```",
            "",
            "Generated outputs:",
            "",
            "- `generated/coverage-symmetry-classes.csv`;",
            "- `generated/coverage-cardinality-loss.csv`;",
            "- `generated/coverage-structural-analysis.json`;",
            "- `docs/structural-symmetry-analysis.md`.",
            "",
            "## Scope",
            "",
            (
                "The symmetry theorem concerns the exact "
                "finite-state model over unordered five-number "
                "draws from `01–90`."
            ),
            "",
            (
                "It does not assert independence between "
                "historical wheels and does not create a "
                "predictive advantage."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def write_outputs(
    class_rows: Sequence[SymmetryClassRow],
    cardinality_rows: Sequence[
        CardinalityLossRow
    ],
    *,
    classes_csv: Path,
    cardinality_csv: Path,
    json_output: Path,
    summary_output: Path,
) -> None:
    write_csv(
        class_rows,
        classes_csv,
    )

    write_csv(
        cardinality_rows,
        cardinality_csv,
    )

    document = build_json_document(
        class_rows,
        cardinality_rows,
    )

    json_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_output.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    summary_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_output.write_text(
        build_summary(
            class_rows,
            cardinality_rows,
        ),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Genera l'analisi strutturale "
            "delle classi di copertura."
        )
    )

    parser.add_argument(
        "--classes-csv",
        type=Path,
        default=DEFAULT_CLASSES_CSV,
    )

    parser.add_argument(
        "--cardinality-csv",
        type=Path,
        default=DEFAULT_CARDINALITY_CSV,
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
    )

    parser.add_argument(
        "--summary-output",
        type=Path,
        default=DEFAULT_SUMMARY_OUTPUT,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        class_rows = (
            build_symmetry_class_rows()
        )

        cardinality_rows = (
            build_cardinality_loss_rows(
                class_rows
            )
        )

        validate_analysis(
            class_rows,
            cardinality_rows,
        )

        write_outputs(
            class_rows,
            cardinality_rows,
            classes_csv=args.classes_csv,
            cardinality_csv=(
                args.cardinality_csv
            ),
            json_output=args.json_output,
            summary_output=(
                args.summary_output
            ),
        )

        widest = max(
            cardinality_rows,
            key=lambda row: (
                row.expected_range,
                -row.missing_count,
            ),
        )

        print(
            f"Classi strutturali:       "
            f"{len(class_rows)}"
        )

        print(
            f"Stati rappresentati:      "
            f"{sum(row.state_multiplicity for row in class_rows)}"
        )

        print(
            f"Cardinalità analizzate:   "
            f"{len(cardinality_rows)}"
        )

        print(
            f"Massima perdita attesa:   "
            f"{widest.expected_range:.9f} "
            f"(cardinalità "
            f"{widest.missing_count})"
        )

        print(
            f"CSV classi:               "
            f"{args.classes_csv}"
        )

        print(
            f"CSV cardinalità:          "
            f"{args.cardinality_csv}"
        )

        print(
            f"JSON:                      "
            f"{args.json_output}"
        )

        print(
            f"Documento:                 "
            f"{args.summary_output}"
        )

    except (
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
