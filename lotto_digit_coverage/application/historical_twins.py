"""Presentation-neutral one-step twin-number research service."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from lotto_digit_coverage.domain.draws import DrawSnapshot
from strategies.twin_numbers import (
    TwinObservation,
    TwinStatisticsRow,
    build_all_twin_observations,
    build_twin_statistics,
)


@dataclass(frozen=True)
class TwinNumberReport:
    observations: tuple[TwinObservation, ...]
    rows: tuple[TwinStatisticsRow, ...]
    available_wheels: tuple[str, ...]
    requested_wheels: tuple[str, ...]
    from_date: str | None
    to_date: str | None
    first_target_date: str
    last_target_date: str
    candidate_count: int


def validate_wheels(requested: Sequence[str], available: Sequence[str]) -> None:
    known = {wheel.casefold(): wheel for wheel in available}
    unknown = [wheel for wheel in requested if wheel.casefold() not in known]
    if unknown:
        raise ValueError(
            "Ruote sconosciute: "
            + ", ".join(unknown)
            + ". Disponibili: "
            + ", ".join(available)
            + "."
        )


def filter_observations(
    observations: Sequence[TwinObservation],
    *,
    wheels: Sequence[str] = (),
    from_date: str | None = None,
    to_date: str | None = None,
) -> tuple[TwinObservation, ...]:
    selected_wheels = {wheel.casefold() for wheel in wheels}
    if from_date and to_date and from_date > to_date:
        raise ValueError("--from-date non può superare --to-date.")

    return tuple(
        observation
        for observation in observations
        if (
            not selected_wheels
            or observation.wheel.casefold() in selected_wheels
        )
        and (from_date is None or observation.target_date >= from_date)
        and (to_date is None or observation.target_date <= to_date)
    )


def build_twin_number_report(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    *,
    wheels: Sequence[str] = (),
    from_date: str | None = None,
    to_date: str | None = None,
) -> TwinNumberReport:
    available = tuple(draws_by_wheel)
    validate_wheels(wheels, available)
    observations = filter_observations(
        build_all_twin_observations(draws_by_wheel),
        wheels=wheels,
        from_date=from_date,
        to_date=to_date,
    )
    if not observations:
        raise RuntimeError(
            "Nessuna osservazione one-step disponibile con i filtri richiesti."
        )
    rows = tuple(build_twin_statistics(observations))
    dates = [observation.target_date for observation in observations]
    return TwinNumberReport(
        observations=observations,
        rows=rows,
        available_wheels=available,
        requested_wheels=tuple(wheels),
        from_date=from_date,
        to_date=to_date,
        first_target_date=min(dates),
        last_target_date=max(dates),
        candidate_count=sum(row.candidate for row in rows),
    )
