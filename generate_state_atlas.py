#!/usr/bin/env python3

"""Genera l'atlante matematico dei 1.023 stati non vuoti."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Sequence

from strategies.coverage_markov import maturity_metrics


DIGIT_COUNT = 10
ALL_DIGITS_MASK = (1 << DIGIT_COUNT) - 1

HORIZONS = (1, 2, 3, 5, 10)
QUANTILES = (0.50, 0.90, 0.95, 0.99)

DEFAULT_CSV_OUTPUT = Path(
    "generated/coverage-state-atlas.csv"
)
DEFAULT_JSON_OUTPUT = Path(
    "generated/coverage-state-atlas.json"
)
DEFAULT_SUMMARY_OUTPUT = Path(
    "docs/state-atlas-summary.md"
)


@dataclass(frozen=True)
class StateAtlasRow:
    difficulty_rank: int
    rank_within_missing_count: int
    state_mask: int
    state: str
    missing_digits: tuple[int, ...]
    missing_count: int
    contains_digit_9: bool
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


def state_from_mask(
    mask: int,
) -> tuple[int, ...]:
    if not 1 <= mask <= ALL_DIGITS_MASK:
        raise ValueError(
            "La maschera deve rappresentare "
            "uno stato non vuoto."
        )

    return tuple(
        digit
        for digit in range(DIGIT_COUNT)
        if mask & (1 << digit)
    )


def format_state(
    digits: Sequence[int],
) -> str:
    return (
        "{"
        + ",".join(str(digit) for digit in digits)
        + "}"
    )


def build_unranked_rows() -> tuple[
    StateAtlasRow,
    ...,
]:
    rows: list[StateAtlasRow] = []

    for mask in range(
        1,
        ALL_DIGITS_MASK + 1,
    ):
        digits = state_from_mask(mask)

        metrics = maturity_metrics(
            digits,
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

        rows.append(
            StateAtlasRow(
                difficulty_rank=0,
                rank_within_missing_count=0,
                state_mask=mask,
                state=format_state(digits),
                missing_digits=digits,
                missing_count=len(digits),
                contains_digit_9=9 in digits,
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
                variance_remaining_draws=variance,
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

    return tuple(rows)


def difficulty_sort_key(
    row: StateAtlasRow,
) -> tuple[float, int, tuple[int, ...]]:
    return (
        row.expected_remaining_draws,
        row.missing_count,
        row.missing_digits,
    )


def assign_ranks(
    rows: Sequence[StateAtlasRow],
) -> tuple[StateAtlasRow, ...]:
    ordered = sorted(
        rows,
        key=difficulty_sort_key,
    )

    overall_rank = {
        row.state_mask: rank
        for rank, row in enumerate(
            ordered,
            start=1,
        )
    }

    groups: dict[
        int,
        list[StateAtlasRow],
    ] = defaultdict(list)

    for row in rows:
        groups[row.missing_count].append(row)

    within_count_rank: dict[int, int] = {}

    for group_rows in groups.values():
        for rank, row in enumerate(
            sorted(
                group_rows,
                key=difficulty_sort_key,
            ),
            start=1,
        ):
            within_count_rank[
                row.state_mask
            ] = rank

    return tuple(
        replace(
            row,
            difficulty_rank=overall_rank[
                row.state_mask
            ],
            rank_within_missing_count=(
                within_count_rank[
                    row.state_mask
                ]
            ),
        )
        for row in ordered
    )


def validate_atlas(
    rows: Sequence[StateAtlasRow],
    *,
    tolerance: float = 1e-12,
) -> None:
    if len(rows) != 1023:
        raise RuntimeError(
            "L'atlante deve contenere "
            f"1.023 stati, non {len(rows)}."
        )

    masks = {
        row.state_mask
        for row in rows
    }

    expected_masks = set(
        range(1, ALL_DIGITS_MASK + 1)
    )

    if masks != expected_masks:
        raise RuntimeError(
            "Lo spazio degli stati è incompleto "
            "o contiene duplicati."
        )

    ranks = [
        row.difficulty_rank
        for row in rows
    ]

    if ranks != list(range(1, 1024)):
        raise RuntimeError(
            "Il ranking complessivo non è "
            "contiguo e deterministico."
        )

    expected_values = [
        row.expected_remaining_draws
        for row in rows
    ]

    if any(
        current
        > following + tolerance
        for current, following in zip(
            expected_values,
            expected_values[1:],
        )
    ):
        raise RuntimeError(
            "Il ranking non è ordinato per "
            "tempo residuo atteso."
        )

    rows_by_mask = {
        row.state_mask: row
        for row in rows
    }

    for row in rows:
        probabilities = (
            row.completion_probability_within_1,
            row.completion_probability_within_2,
            row.completion_probability_within_3,
            row.completion_probability_within_5,
            row.completion_probability_within_10,
        )

        if any(
            probability < -tolerance
            or probability > 1.0 + tolerance
            for probability in probabilities
        ):
            raise RuntimeError(
                "Probabilità fuori intervallo "
                f"per lo stato {row.state}."
            )

        if any(
            current > following + tolerance
            for current, following in zip(
                probabilities,
                probabilities[1:],
            )
        ):
            raise RuntimeError(
                "Probabilità cumulative non monotone "
                f"per lo stato {row.state}."
            )

        if row.expected_remaining_draws <= 0.0:
            raise RuntimeError(
                "Tempo atteso non positivo "
                f"per lo stato {row.state}."
            )

        if row.variance_remaining_draws < 0.0:
            raise RuntimeError(
                "Varianza negativa "
                f"per lo stato {row.state}."
            )

        quantiles = (
            row.quantile_50_draws,
            row.quantile_90_draws,
            row.quantile_95_draws,
            row.quantile_99_draws,
        )

        if any(
            quantile <= 0
            for quantile in quantiles
        ):
            raise RuntimeError(
                "Quantile non positivo "
                f"per lo stato {row.state}."
            )

        if list(quantiles) != sorted(quantiles):
            raise RuntimeError(
                "Quantili non ordinati "
                f"per lo stato {row.state}."
            )

        for digit in range(DIGIT_COUNT):
            bit = 1 << digit

            if row.state_mask & bit:
                continue

            superset_mask = (
                row.state_mask | bit
            )

            superset = rows_by_mask[
                superset_mask
            ]

            if (
                row.expected_remaining_draws
                > superset.expected_remaining_draws
                + tolerance
            ):
                raise RuntimeError(
                    "Violazione della monotonia "
                    "per inclusione: "
                    f"{row.state} > {superset.state}."
                )

    for missing_count in range(1, 11):
        group = [
            row
            for row in rows
            if row.missing_count
            == missing_count
        ]

        group_ranks = sorted(
            row.rank_within_missing_count
            for row in group
        )

        if group_ranks != list(
            range(1, len(group) + 1)
        ):
            raise RuntimeError(
                "Ranking interno non contiguo "
                f"per cardinalità {missing_count}."
            )


def build_atlas() -> tuple[
    StateAtlasRow,
    ...,
]:
    rows = assign_ranks(
        build_unranked_rows()
    )

    validate_atlas(rows)

    return rows


def json_document(
    rows: Sequence[StateAtlasRow],
) -> dict[str, object]:
    return {
        "report_format_version": 1,
        "report_type": (
            "decimal-digit-coverage-state-atlas"
        ),
        "purpose": (
            "Exact descriptive absorption metrics; "
            "not a betting recommendation."
        ),
        "state_space": {
            "digit_count": DIGIT_COUNT,
            "total_states": 1024,
            "absorbing_states": 1,
            "non_empty_states": len(rows),
        },
        "horizons": list(HORIZONS),
        "quantile_probabilities": list(
            QUANTILES
        ),
        "ranking": {
            "primary_metric": (
                "expected_remaining_draws"
            ),
            "direction": (
                "ascending; rank 1 is easiest"
            ),
            "tie_breakers": (
                "missing_count, then "
                "lexicographic missing_digits"
            ),
        },
        "rows": [
            asdict(row)
            for row in rows
        ],
    }


def csv_value(
    value: object,
) -> object:
    if isinstance(value, float):
        return format(value, ".17g")

    if isinstance(value, tuple):
        return " ".join(
            str(item)
            for item in value
        )

    if isinstance(value, bool):
        return "yes" if value else "no"

    return value


def write_csv(
    rows: Sequence[StateAtlasRow],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = list(
        asdict(rows[0]).keys()
    )

    with output.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    key: csv_value(value)
                    for key, value
                    in asdict(row).items()
                }
            )


def write_json(
    rows: Sequence[StateAtlasRow],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            json_document(rows),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def format_summary_row(
    row: StateAtlasRow,
) -> str:
    return (
        f"| {row.difficulty_rank} "
        f"| `{row.state}` "
        f"| {row.missing_count} "
        f"| {row.expected_remaining_draws:.6f} "
        f"| {row.standard_deviation_remaining_draws:.6f} "
        f"| {row.completion_probability_within_1:.2%} "
        f"| {row.quantile_50_draws} "
        f"| {row.quantile_95_draws} "
        f"| {row.quantile_99_draws} |"
    )


def render_summary(
    rows: Sequence[StateAtlasRow],
) -> str:
    easiest = list(rows[:10])
    hardest = list(reversed(rows[-10:]))

    lines = [
        "# Coverage state atlas summary",
        "",
        "## Status",
        "",
        (
            "Generated from the exact 1,024-state "
            "finite-state model."
        ),
        "",
        (
            "The atlas is descriptive mathematical "
            "material, not a betting recommendation."
        ),
        "",
        "## Scope",
        "",
        "- total states: 1,024;",
        "- absorbing empty state: 1;",
        "- non-empty states in the atlas: 1,023;",
        "- difficulty metric: expected remaining draws;",
        "- rank 1: smallest expected remaining time;",
        (
            "- deterministic tie-breakers: missing-digit "
            "count and lexicographic state."
        ),
        "",
        "## Summary by missing-digit count",
        "",
        (
            "| Missing digits | States | Minimum mean "
            "| Average mean | Maximum mean |"
        ),
        (
            "|---:|---:|---:|---:|---:|"
        ),
    ]

    for missing_count in range(1, 11):
        group = [
            row
            for row in rows
            if row.missing_count
            == missing_count
        ]

        means = [
            row.expected_remaining_draws
            for row in group
        ]

        lines.append(
            f"| {missing_count} "
            f"| {len(group)} "
            f"| {min(means):.6f} "
            f"| {statistics.fmean(means):.6f} "
            f"| {max(means):.6f} |"
        )

    table_header = [
        "",
        "| Rank | State | Missing | Mean | Std. dev. "
        "| P(within 1) | Q50 | Q95 | Q99 |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    lines.extend(
        [
            "",
            "## Ten easiest states",
            *table_header,
        ]
    )

    lines.extend(
        format_summary_row(row)
        for row in easiest
    )

    lines.extend(
        [
            "",
            "## Ten hardest states",
            *table_header,
        ]
    )

    lines.extend(
        format_summary_row(row)
        for row in hardest
    )

    full_state = next(
        row
        for row in rows
        if row.state_mask
        == ALL_DIGITS_MASK
    )

    lines.extend(
        [
            "",
            "## Full initial state",
            "",
            (
                "For the state with all ten digits "
                "still missing:"
            ),
            "",
            (
                f"- expected remaining draws: "
                f"{full_state.expected_remaining_draws:.6f};"
            ),
            (
                f"- variance: "
                f"{full_state.variance_remaining_draws:.6f};"
            ),
            (
                f"- standard deviation: "
                f"{full_state.standard_deviation_remaining_draws:.6f};"
            ),
            (
                f"- completion within 3 draws: "
                f"{full_state.completion_probability_within_3:.2%};"
            ),
            (
                f"- completion within 5 draws: "
                f"{full_state.completion_probability_within_5:.2%};"
            ),
            (
                f"- median completion horizon: "
                f"{full_state.quantile_50_draws};"
            ),
            (
                f"- 95% completion horizon: "
                f"{full_state.quantile_95_draws};"
            ),
            (
                f"- 99% completion horizon: "
                f"{full_state.quantile_99_draws}."
            ),
            "",
            "## Machine-readable outputs",
            "",
            "- `generated/coverage-state-atlas.csv`",
            "- `generated/coverage-state-atlas.json`",
            "",
            "## Interpretation",
            "",
            (
                "States with the same number of missing "
                "digits may have different metrics because "
                "digit identities are not symmetric in "
                "the range `01–90`."
            ),
            "",
            (
                "The ranking describes mathematical "
                "absorption difficulty only. It does not "
                "identify favourable draws, wheels or "
                "wagering opportunities."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def write_summary(
    rows: Sequence[StateAtlasRow],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        render_summary(rows)
    )


def write_outputs(
    rows: Sequence[StateAtlasRow],
    *,
    csv_output: Path,
    json_output: Path,
    summary_output: Path,
) -> None:
    write_csv(rows, csv_output)
    write_json(rows, json_output)
    write_summary(rows, summary_output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Genera l'atlante matematico completo "
            "degli stati non vuoti."
        )
    )

    parser.add_argument(
        "--csv-output",
        type=Path,
        default=DEFAULT_CSV_OUTPUT,
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
        rows = build_atlas()

        write_outputs(
            rows,
            csv_output=args.csv_output,
            json_output=args.json_output,
            summary_output=args.summary_output,
        )

        easiest = rows[0]
        hardest = rows[-1]

        print("===== ATLANTE DEGLI STATI =====")
        print(f"Stati generati:       {len(rows)}")
        print(
            "Ranking:              "
            "tempo residuo atteso crescente"
        )
        print(
            "Stato più facile:     "
            f"{easiest.state} "
            f"({easiest.expected_remaining_draws:.6f})"
        )
        print(
            "Stato più difficile:  "
            f"{hardest.state} "
            f"({hardest.expected_remaining_draws:.6f})"
        )
        print(
            f"CSV:                  {args.csv_output}"
        )
        print(
            f"JSON:                 {args.json_output}"
        )
        print(
            f"Sintesi:              {args.summary_output}"
        )

    except (
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
    ) as error:
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
