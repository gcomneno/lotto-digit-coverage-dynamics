"""Presentation-neutral historical symmetry-class analysis."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from lotto_digit_coverage.domain.draws import DrawSnapshot
from strategies.coverage_completion import (
    ALL_DIGITS,
    digits_in_draw,
    exact_completion_probability,
)
from strategies.coverage_structure import (
    StateSymmetryClass,
    group_nonempty_states_by_symmetry,
    state_symmetry_class,
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


@dataclass(frozen=True)
class HistoricalSymmetryReport:
    observations: tuple[ClassObservation, ...]
    rows: tuple[EmpiricalClassRow, ...]
    wheel_count: int


def class_identifier(symmetry_class: StateSymmetryClass) -> str:
    return f"{symmetry_class.family}:{symmetry_class.exchangeable_count}"


def format_state(digits: Sequence[int]) -> str:
    return "{" + ",".join(str(digit) for digit in digits) + "}"


def ordered_draws(draws: Sequence[DrawSnapshot]) -> tuple[DrawSnapshot, ...]:
    if not draws:
        return ()
    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order
    if any(
        draw.wheel != wheel or draw.wheel_order != wheel_order
        for draw in draws
    ):
        raise ValueError("Le estrazioni devono appartenere alla stessa ruota.")

    result = tuple(
        sorted(draws, key=lambda draw: (draw.draw_date, draw.draw_number))
    )
    identities = [(draw.draw_date, draw.draw_number) for draw in result]
    if len(identities) != len(set(identities)):
        raise ValueError("La cronologia contiene estrazioni duplicate.")
    return result


def build_class_observations(
    draws: Sequence[DrawSnapshot],
) -> tuple[ClassObservation, ...]:
    ordered = ordered_draws(draws)
    if not ordered:
        return ()

    covered: set[int] = set()
    synchronized = False
    observations: list[ClassObservation] = []

    for draw in ordered:
        observed_digits = digits_in_draw(draw)
        if not synchronized:
            covered.update(observed_digits)
            if covered == ALL_DIGITS:
                synchronized = True
                covered.clear()
            continue

        missing = ALL_DIGITS.difference(covered)
        symmetry_class = state_symmetry_class(missing)
        observations.append(
            ClassObservation(
                wheel=draw.wheel,
                wheel_order=draw.wheel_order,
                target_draw=draw.draw_number,
                target_date=draw.draw_date,
                missing_digits=tuple(sorted(missing)),
                class_id=class_identifier(symmetry_class),
                theoretical_probability=exact_completion_probability(missing),
                completed_next=missing.issubset(observed_digits),
            )
        )
        covered.update(observed_digits)
        if covered == ALL_DIGITS:
            covered.clear()

    return tuple(observations)


def build_all_observations(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
) -> tuple[ClassObservation, ...]:
    observations = [
        observation
        for draws in draws_by_wheel.values()
        for observation in build_class_observations(draws)
    ]
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                item.target_date,
                item.target_draw,
                item.wheel_order,
            ),
        )
    )


def build_empirical_rows(
    observations: Sequence[ClassObservation],
) -> tuple[EmpiricalClassRow, ...]:
    grouped: dict[str, list[ClassObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.class_id].append(observation)

    rows: list[EmpiricalClassRow] = []
    for symmetry_class, states in group_nonempty_states_by_symmetry().items():
        class_id = class_identifier(symmetry_class)
        canonical = tuple(sorted(symmetry_class.canonical_state))
        theoretical = exact_completion_probability(canonical)
        items = grouped.get(class_id, [])
        count = len(items)
        completions = sum(item.completed_next for item in items)
        observed = completions / count if count else None
        difference = None if observed is None else observed - theoretical
        rows.append(
            EmpiricalClassRow(
                class_id=class_id,
                family=symmetry_class.family,
                exchangeable_count=symmetry_class.exchangeable_count,
                missing_count=symmetry_class.missing_count,
                canonical_state=format_state(canonical),
                state_multiplicity=len(states),
                observations=count,
                observed_completions=completions,
                expected_completions=count * theoretical,
                theoretical_probability=theoretical,
                observed_frequency=observed,
                difference_probability=difference,
                difference_percentage_points=(
                    None if difference is None else 100.0 * difference
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
    observations: Sequence[ClassObservation],
) -> None:
    if len(rows) != 27:
        raise RuntimeError(f"Attese 27 classi, trovate {len(rows)}.")
    if len({row.class_id for row in rows}) != 27:
        raise RuntimeError("Identificatori di classe duplicati.")
    if sum(row.observations for row in rows) != len(observations):
        raise RuntimeError("Il totale delle osservazioni non coincide.")
    for row in rows:
        if not 0.0 <= row.theoretical_probability <= 1.0:
            raise RuntimeError(
                f"Probabilità teorica non valida per {row.class_id}."
            )
        if row.observations == 0:
            if row.observed_frequency is not None or row.difference_probability is not None:
                raise RuntimeError(
                    "Classe priva di osservazioni con frequenza valorizzata."
                )
        elif row.observed_frequency is None or not 0.0 <= row.observed_frequency <= 1.0:
            raise RuntimeError(f"Frequenza osservata non valida per {row.class_id}.")


def build_historical_symmetry_report(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
) -> HistoricalSymmetryReport:
    observations = build_all_observations(draws_by_wheel)
    rows = build_empirical_rows(observations)
    validate_rows(rows, observations)
    return HistoricalSymmetryReport(
        observations=observations,
        rows=rows,
        wheel_count=len(draws_by_wheel),
    )
