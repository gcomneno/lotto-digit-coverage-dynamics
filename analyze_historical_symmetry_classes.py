#!/usr/bin/env python3

"""Confronto empirico one-step delle 27 classi strutturali."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from strategies.coverage_completion import (
    ALL_DIGITS,
    digits_in_draw,
    exact_completion_probability,
)
from strategies.coverage_cycle_history import (
    merge_draws_by_wheel,
)
from strategies.coverage_structure import (
    StateSymmetryClass,
    group_nonempty_states_by_symmetry,
    state_symmetry_class,
)
from strategies.digit_coverage import (
    load_draws_by_wheel,
)
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
)


DEFAULT_DATABASES = (
    Path("data/lotto-2023.sqlite3"),
    Path("data/lotto-2024.sqlite3"),
    Path("data/lotto-2025.sqlite3"),
    Path("data/lotto-2026.sqlite3"),
)

DEFAULT_CSV_OUTPUT = Path(
    "_work/historical-symmetry-classes.csv"
)

DEFAULT_JSON_OUTPUT = Path(
    "_work/historical-symmetry-classes.json"
)

FAMILY_ORDER = {
    "no-nine": 0,
    "nine-no-zero": 1,
    "zero-nine": 2,
}


@dataclass(frozen=True)
class ClassObservation:
    wheel: str
    wheel_order: int
    target_draw: int
    target_date: str
    missing_digits: tuple[int, ...]
    class_id: str
    theoretical_probability: float
    completed_next: bool


@dataclass(frozen=True)
class EmpiricalClassRow:
    class_id: str
    family: str
    exchangeable_count: int
    missing_count: int
    canonical_state: str
    state_multiplicity: int
    observations: int
    observed_completions: int
    expected_completions: float
    theoretical_probability: float
    observed_frequency: float | None
    difference_probability: float | None
    difference_percentage_points: float | None


def class_identifier(
    symmetry_class: StateSymmetryClass,
) -> str:
    return (
        f"{symmetry_class.family}:"
        f"{symmetry_class.exchangeable_count}"
    )


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


def ordered_draws(
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
            "Le estrazioni devono appartenere "
            "alla stessa ruota."
        )

    result = tuple(
        sorted(
            draws,
            key=lambda draw: (
                draw.draw_date,
                draw.draw_number,
            ),
        )
    )

    identities = [
        (
            draw.draw_date,
            draw.draw_number,
        )
        for draw in result
    ]

    if len(identities) != len(
        set(identities)
    ):
        raise ValueError(
            "La cronologia contiene "
            "estrazioni duplicate."
        )

    return result


def build_class_observations(
    draws: Sequence[DrawSnapshot],
) -> tuple[ClassObservation, ...]:
    """
    Costruisce osservazioni one-step dopo la sincronizzazione.

    Lo stato viene fotografato prima dell'estrazione target.
    L'esito indica se quella estrazione completa il ciclo.
    """

    ordered = ordered_draws(draws)

    if not ordered:
        return ()

    covered: set[int] = set()
    synchronized = False
    observations: list[
        ClassObservation
    ] = []

    for draw in ordered:
        observed_digits = digits_in_draw(
            draw
        )

        if not synchronized:
            covered.update(observed_digits)

            if covered == ALL_DIGITS:
                synchronized = True
                covered.clear()

            continue

        missing = ALL_DIGITS.difference(
            covered
        )

        symmetry_class = (
            state_symmetry_class(missing)
        )

        completed_next = missing.issubset(
            observed_digits
        )

        observations.append(
            ClassObservation(
                wheel=draw.wheel,
                wheel_order=draw.wheel_order,
                target_draw=draw.draw_number,
                target_date=draw.draw_date,
                missing_digits=tuple(
                    sorted(missing)
                ),
                class_id=class_identifier(
                    symmetry_class
                ),
                theoretical_probability=(
                    exact_completion_probability(
                        missing
                    )
                ),
                completed_next=completed_next,
            )
        )

        covered.update(observed_digits)

        if covered == ALL_DIGITS:
            covered.clear()

    return tuple(observations)


def build_all_observations(
    draws_by_wheel: Mapping[
        str,
        Sequence[DrawSnapshot],
    ],
) -> tuple[ClassObservation, ...]:
    observations = [
        observation
        for draws in draws_by_wheel.values()
        for observation in (
            build_class_observations(draws)
        )
    ]

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


def build_empirical_rows(
    observations: Sequence[
        ClassObservation
    ],
) -> tuple[EmpiricalClassRow, ...]:
    grouped: dict[
        str,
        list[ClassObservation],
    ] = defaultdict(list)

    for observation in observations:
        grouped[
            observation.class_id
        ].append(observation)

    rows: list[EmpiricalClassRow] = []

    classes = (
        group_nonempty_states_by_symmetry()
    )

    for symmetry_class, states in classes.items():
        class_id = class_identifier(
            symmetry_class
        )

        canonical = tuple(
            sorted(
                symmetry_class.canonical_state
            )
        )

        theoretical_probability = (
            exact_completion_probability(
                canonical
            )
        )

        class_observations = grouped.get(
            class_id,
            [],
        )

        observation_count = len(
            class_observations
        )

        completions = sum(
            observation.completed_next
            for observation
            in class_observations
        )

        if observation_count:
            observed_frequency = (
                completions
                / observation_count
            )

            difference = (
                observed_frequency
                - theoretical_probability
            )
        else:
            observed_frequency = None
            difference = None

        rows.append(
            EmpiricalClassRow(
                class_id=class_id,
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
                canonical_state=format_state(
                    canonical
                ),
                state_multiplicity=len(states),
                observations=observation_count,
                observed_completions=(
                    completions
                ),
                expected_completions=(
                    observation_count
                    * theoretical_probability
                ),
                theoretical_probability=(
                    theoretical_probability
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
            )
        )

    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.missing_count,
                FAMILY_ORDER[row.family],
                row.exchangeable_count,
            ),
        )
    )


def validate_rows(
    rows: Sequence[EmpiricalClassRow],
    observations: Sequence[
        ClassObservation
    ],
) -> None:
    if len(rows) != 27:
        raise RuntimeError(
            f"Attese 27 classi, trovate {len(rows)}."
        )

    if len(
        {
            row.class_id
            for row in rows
        }
    ) != 27:
        raise RuntimeError(
            "Identificatori di classe duplicati."
        )

    if sum(
        row.observations
        for row in rows
    ) != len(observations):
        raise RuntimeError(
            "Il totale delle osservazioni "
            "non coincide."
        )

    for row in rows:
        if not (
            0.0
            <= row.theoretical_probability
            <= 1.0
        ):
            raise RuntimeError(
                "Probabilità teorica non valida "
                f"per {row.class_id}."
            )

        if row.observations == 0:
            if (
                row.observed_frequency
                is not None
                or row.difference_probability
                is not None
            ):
                raise RuntimeError(
                    "Classe priva di osservazioni "
                    "con frequenza valorizzata."
                )

            continue

        if row.observed_frequency is None:
            raise RuntimeError(
                "Frequenza osservata mancante "
                f"per {row.class_id}."
            )

        if not (
            0.0
            <= row.observed_frequency
            <= 1.0
        ):
            raise RuntimeError(
                "Frequenza osservata non valida "
                f"per {row.class_id}."
            )


def load_database(
    path: Path,
) -> Mapping[
    str,
    Sequence[DrawSnapshot],
]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Database non trovato: {path}"
        )

    with LottoRepository(path) as repository:
        return load_draws_by_wheel(
            repository
        )


def load_merged_draws(
    database_paths: Sequence[Path],
) -> dict[
    str,
    tuple[DrawSnapshot, ...],
]:
    if not database_paths:
        raise ValueError(
            "Serve almeno un database."
        )

    collections = [
        load_database(path)
        for path in database_paths
    ]

    return merge_draws_by_wheel(
        collections
    )


def csv_value(
    value: object,
) -> object:
    if value is None:
        return ""

    if isinstance(value, float):
        return format(value, ".17g")

    return value


def write_csv(
    rows: Sequence[EmpiricalClassRow],
    output: Path,
) -> None:
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
    rows: Sequence[EmpiricalClassRow],
    observations: Sequence[
        ClassObservation
    ],
    database_paths: Sequence[Path],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    observed_dates = [
        observation.target_date
        for observation in observations
    ]

    document = {
        "report_format_version": 1,
        "report_type": (
            "historical-symmetry-class-"
            "one-step-comparison"
        ),
        "segment": (
            (
                f"{min(observed_dates)[:4]}-"
                f"{max(observed_dates)[:4]}"
            )
            if observed_dates
            else None
        ),
        "database_paths": [
            str(path)
            for path in database_paths
        ],
        "first_target_date": (
            min(observed_dates)
            if observed_dates
            else None
        ),
        "last_target_date": (
            max(observed_dates)
            if observed_dates
            else None
        ),
        "class_count": len(rows),
        "observation_count": len(
            observations
        ),
        "interpretation": (
            "Descriptive pooled comparison. "
            "Wheels share the draw calendar and "
            "are not assumed independent."
        ),
        "rows": [
            asdict(row)
            for row in rows
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


def render_table(
    rows: Sequence[EmpiricalClassRow],
) -> str:
    lines = [
        (
            "Classe             Stato       "
            "N      Hit    Teoria    Osservata   Diff. pp"
        ),
        (
            "------------------ --------- "
            "------ ------ --------- ----------- --------"
        ),
    ]

    for row in rows:
        observed = (
            "—"
            if row.observed_frequency is None
            else f"{row.observed_frequency:9.3%}"
        )

        difference = (
            "—"
            if row.difference_percentage_points
            is None
            else (
                f"{row.difference_percentage_points:+8.3f}"
            )
        )

        lines.append(
            f"{row.class_id:<18} "
            f"{row.canonical_state:<9} "
            f"{row.observations:>6} "
            f"{row.observed_completions:>6} "
            f"{row.theoretical_probability:>9.3%} "
            f"{observed:>11} "
            f"{difference:>8}"
        )

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta le frequenze storiche "
            "one-step delle 27 classi strutturali."
        )
    )

    parser.add_argument(
        "--database",
        action="append",
        type=Path,
        dest="databases",
        help=(
            "Database SQLite. Ripetere l'opzione "
            "per più archivi."
        ),
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

    return parser


def main() -> int:
    args = build_parser().parse_args()

    databases = tuple(
        args.databases
        if args.databases
        else DEFAULT_DATABASES
    )

    try:
        draws_by_wheel = (
            load_merged_draws(databases)
        )

        observations = (
            build_all_observations(
                draws_by_wheel
            )
        )

        rows = build_empirical_rows(
            observations
        )

        validate_rows(
            rows,
            observations,
        )

        write_csv(
            rows,
            args.csv_output,
        )

        write_json(
            rows,
            observations,
            databases,
            args.json_output,
        )

        print(
            f"Ruote:        "
            f"{len(draws_by_wheel)}"
        )

        print(
            f"Osservazioni: "
            f"{len(observations)}"
        )

        print(
            f"Classi:       "
            f"{len(rows)}"
        )

        print()
        print(render_table(rows))

        print()
        print(
            f"CSV:  {args.csv_output}"
        )

        print(
            f"JSON: {args.json_output}"
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
