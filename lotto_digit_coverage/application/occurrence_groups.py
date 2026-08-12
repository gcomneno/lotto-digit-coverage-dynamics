"""Presentation-neutral grouped same-wheel occurrence analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


DrawKey = tuple[int, str]
WheelNumbers = Mapping[str, Sequence[int]]


@dataclass(frozen=True)
class OccurrenceDrawRow:
    """One draw included in an occurrence group."""

    draw_number: int
    draw_date: str
    wheel_numbers: tuple[tuple[str, tuple[int, ...]], ...]

    def numbers_for(self, wheel: str) -> tuple[int, ...] | None:
        return dict(self.wheel_numbers).get(wheel)


@dataclass(frozen=True)
class OccurrenceWheelSummary:
    """Reference numbers and aligned same-wheel counts for one wheel."""

    wheel: str
    reference_numbers: tuple[int, ...]
    occurrence_counts: tuple[int, ...]


@dataclass(frozen=True)
class OccurrenceGroup:
    """One consecutive descending-chronology group."""

    reference_draw_number: int
    reference_draw_date: str
    newest_draw_number: int
    newest_draw_date: str
    oldest_draw_number: int
    oldest_draw_date: str
    draws: tuple[OccurrenceDrawRow, ...]
    wheels: tuple[OccurrenceWheelSummary, ...]

    @property
    def size(self) -> int:
        return len(self.draws)


@dataclass(frozen=True)
class OccurrenceGroupReport:
    """Structured result for grouped retrospective occurrences."""

    reference_draw_number: int
    reference_draw_date: str
    reference_kind: str
    group_size: int
    groups: tuple[OccurrenceGroup, ...]


def chronological_key(draw_key: DrawKey) -> tuple[str, int]:
    draw_number, draw_date = draw_key
    return draw_date, draw_number


def _normalized_numbers(numbers: Sequence[int]) -> tuple[int, ...]:
    return tuple(int(number) for number in numbers)


def _is_complete_reference(
    wheel_results: WheelNumbers,
    expected_wheels: Sequence[str],
) -> bool:
    return all(
        wheel in wheel_results
        and len(wheel_results[wheel]) == 5
        for wheel in expected_wheels
    )


def _validate_reference(
    draw_key: DrawKey,
    wheel_results: WheelNumbers,
    expected_wheels: Sequence[str],
) -> None:
    draw_number, draw_date = draw_key

    for wheel in expected_wheels:
        if wheel not in wheel_results:
            raise ValueError(
                "estrazione di riferimento "
                f"{draw_number} del {draw_date}: "
                f"ruota attesa mancante: {wheel}."
            )

        numbers = _normalized_numbers(wheel_results[wheel])
        if len(numbers) != 5:
            raise ValueError(
                "estrazione di riferimento "
                f"{draw_number} del {draw_date}: "
                f"la ruota {wheel} contiene "
                f"{len(numbers)} valori anziché 5."
            )

        for number in numbers:
            if not 1 <= number <= 90:
                raise ValueError(
                    "estrazione di riferimento "
                    f"{draw_number} del {draw_date}: "
                    "valore fuori dall'intervallo "
                    f"01–90 sulla ruota {wheel}: {number!r}."
                )


def resolve_reference(
    draws: Mapping[DrawKey, WheelNumbers],
    *,
    requested_draw_number: int | None,
    expected_wheels: Sequence[str],
) -> tuple[DrawKey, str]:
    """Resolve explicit or latest-complete reference without look-ahead."""

    if requested_draw_number is not None:
        candidates = tuple(
            key
            for key in draws
            if key[0] == requested_draw_number
        )

        if not candidates:
            raise ValueError(
                "estrazione di riferimento "
                f"{requested_draw_number} non trovata."
            )

        if len(candidates) > 1:
            raise ValueError(
                "numero di estrazione ambiguo: "
                f"{requested_draw_number}."
            )

        reference = candidates[0]
        _validate_reference(
            reference,
            draws[reference],
            expected_wheels,
        )
        return reference, "esplicito"

    complete = tuple(
        key
        for key, wheel_results in draws.items()
        if _is_complete_reference(wheel_results, expected_wheels)
    )

    if not complete:
        raise ValueError("nessuna estrazione completa disponibile.")

    reference = max(complete, key=chronological_key)
    _validate_reference(
        reference,
        draws[reference],
        expected_wheels,
    )
    return reference, "automatico"


def _draw_row(
    key: DrawKey,
    wheel_results: WheelNumbers,
    expected_wheels: Sequence[str],
) -> OccurrenceDrawRow:
    draw_number, draw_date = key
    available = tuple(
        (
            wheel,
            _normalized_numbers(wheel_results[wheel]),
        )
        for wheel in expected_wheels
        if wheel in wheel_results
    )
    return OccurrenceDrawRow(
        draw_number=draw_number,
        draw_date=draw_date,
        wheel_numbers=available,
    )


def _wheel_summary(
    *,
    wheel: str,
    reference_numbers: Sequence[int],
    group: Sequence[tuple[DrawKey, WheelNumbers]],
) -> OccurrenceWheelSummary:
    reference = _normalized_numbers(reference_numbers)
    counts: list[int] = []

    for number in reference:
        occurrences = 0
        for _key, wheel_results in group:
            observed = wheel_results.get(wheel)
            if observed is not None and number in observed:
                occurrences += 1
        counts.append(occurrences)

    return OccurrenceWheelSummary(
        wheel=wheel,
        reference_numbers=reference,
        occurrence_counts=tuple(counts),
    )


def build_occurrence_group_report(
    *,
    draws: Mapping[DrawKey, WheelNumbers],
    expected_wheels: Sequence[str],
    group_size: int,
    requested_draw_number: int | None = None,
) -> OccurrenceGroupReport:
    """Build consecutive grouped occurrences using each group's newest draw."""

    if (
        not isinstance(group_size, int)
        or isinstance(group_size, bool)
        or group_size <= 0
    ):
        raise ValueError("group_size deve essere un intero positivo.")

    if not draws:
        raise ValueError("nessuna estrazione disponibile.")

    reference_key, reference_kind = resolve_reference(
        draws,
        requested_draw_number=requested_draw_number,
        expected_wheels=expected_wheels,
    )

    rendered_draws = tuple(
        sorted(
            (
                (key, wheel_results)
                for key, wheel_results in draws.items()
                if chronological_key(key)
                <= chronological_key(reference_key)
            ),
            key=lambda item: chronological_key(item[0]),
            reverse=True,
        )
    )

    groups: list[OccurrenceGroup] = []

    for start in range(0, len(rendered_draws), group_size):
        group = rendered_draws[start:start + group_size]
        if not group:
            continue

        group_reference_key, group_reference_results = group[0]
        _validate_reference(
            group_reference_key,
            group_reference_results,
            expected_wheels,
        )
        newest_number, newest_date = group_reference_key
        oldest_number, oldest_date = group[-1][0]

        summaries = tuple(
            _wheel_summary(
                wheel=wheel,
                reference_numbers=group_reference_results[wheel],
                group=group,
            )
            for wheel in expected_wheels
        )

        groups.append(
            OccurrenceGroup(
                reference_draw_number=newest_number,
                reference_draw_date=newest_date,
                newest_draw_number=newest_number,
                newest_draw_date=newest_date,
                oldest_draw_number=oldest_number,
                oldest_draw_date=oldest_date,
                draws=tuple(
                    _draw_row(key, wheel_results, expected_wheels)
                    for key, wheel_results in group
                ),
                wheels=summaries,
            )
        )

    return OccurrenceGroupReport(
        reference_draw_number=reference_key[0],
        reference_draw_date=reference_key[1],
        reference_kind=reference_kind,
        group_size=group_size,
        groups=tuple(groups),
    )
