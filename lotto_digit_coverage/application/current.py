"""Presentation-neutral current coverage application use case."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from analyze_coverage_anomalies import (
    AnomalyEvent,
    build_all_transitions,
    detect_anomalies,
)
from strategies.coverage_checkpoint import (
    apply_draws as apply_checkpoint_draws,
    freeze_state as freeze_checkpoint_state,
    states_from_checkpoint,
)
from strategies.coverage_completion import (
    CurrentCoverageState,
    current_coverage_state,
)
from strategies.coverage_consensus import (
    DigitConsensus,
    build_digit_consensus,
)
from strategies.coverage_markov import maturity_metrics
from strategies.current_coverage_signal import (
    CurrentCoverageSignal,
    HistoricalCoverageClass,
    build_current_coverage_signals,
)

from lotto_digit_coverage.domain.draws import DrawSnapshot


HORIZONS = (1, 2, 3, 5)


@dataclass(frozen=True)
class MarkovWheelReport:
    """Structured Markov metrics for one current wheel state."""

    state: CurrentCoverageState
    completion_within: tuple[tuple[int, float], ...]
    expected_remaining_draws: float

    def probability_within(self, horizon: int) -> float:
        return dict(self.completion_within)[horizon]


@dataclass(frozen=True)
class CurrentCoverageReport:
    """Complete presentation-neutral result for the current use case."""

    latest_draw: int
    latest_date: str
    states: tuple[CurrentCoverageState, ...]
    markov_ranking: tuple[MarkovWheelReport, ...]
    coverage_hit_ranking: tuple[CurrentCoverageSignal, ...]
    consensus: tuple[DigitConsensus, ...]
    anomaly_history: tuple[AnomalyEvent, ...]
    active_anomalies: tuple[AnomalyEvent, ...]
    transition_count: int
    next_draws: tuple[DrawSnapshot, ...]


def limit_draws_to_date(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    cutoff: date | None,
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """Apply an inclusive ISO-date cutoff without mutating the archive."""

    if cutoff is None:
        return {
            wheel: tuple(draws)
            for wheel, draws in draws_by_wheel.items()
        }

    limited = {
        wheel: tuple(
            draw
            for draw in draws
            if date.fromisoformat(draw.draw_date) <= cutoff
        )
        for wheel, draws in draws_by_wheel.items()
    }
    empty_wheels = tuple(
        wheel for wheel, draws in limited.items() if not draws
    )

    if empty_wheels:
        raise RuntimeError(
            "Nessuna estrazione disponibile entro "
            f"il {cutoff.isoformat()} per: "
            + ", ".join(empty_wheels)
            + "."
        )

    return limited


def limit_draws_to_number(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    cutoff: int | None,
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """Apply the legacy inclusive draw-number cutoff semantics."""

    if cutoff is None:
        return {
            wheel: tuple(draws)
            for wheel, draws in draws_by_wheel.items()
        }

    limited = {
        wheel: tuple(
            draw for draw in draws if draw.draw_number <= cutoff
        )
        for wheel, draws in draws_by_wheel.items()
    }
    empty_wheels = tuple(
        wheel for wheel, draws in limited.items() if not draws
    )

    if empty_wheels:
        raise RuntimeError(
            "Nessuna estrazione disponibile entro "
            f"il numero {cutoff} per: "
            + ", ".join(empty_wheels)
            + "."
        )

    return limited


def latest_target(
    states: Sequence[CurrentCoverageState],
) -> tuple[int, str]:
    targets = {
        (state.latest_draw, state.latest_date)
        for state in states
    }

    if not targets:
        raise RuntimeError("Nessuno stato corrente disponibile.")

    if len(targets) != 1:
        details = ", ".join(
            f"{draw}/{draw_date}"
            for draw, draw_date in sorted(targets)
        )
        raise RuntimeError(
            "Le ruote non terminano sulla stessa "
            f"estrazione: {details}."
        )

    return next(iter(targets))


def next_draws_after_target(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    *,
    latest_draw: int,
    latest_date: str,
) -> tuple[DrawSnapshot, ...]:
    """Select exactly one aligned draw after the analyzed target, if present."""

    target_key = (date.fromisoformat(latest_date), latest_draw)
    selected: dict[str, DrawSnapshot] = {}

    for wheel, draws in draws_by_wheel.items():
        candidate = next(
            (
                draw
                for draw in draws
                if (
                    date.fromisoformat(draw.draw_date),
                    draw.draw_number,
                ) > target_key
            ),
            None,
        )
        if candidate is not None:
            selected[wheel] = candidate

    if not selected:
        return ()

    missing_wheels = tuple(
        wheel for wheel in draws_by_wheel if wheel not in selected
    )
    if missing_wheels:
        raise RuntimeError(
            "Estrazione successiva incompleta per: "
            + ", ".join(missing_wheels)
            + "."
        )

    targets = {
        (draw.draw_number, draw.draw_date)
        for draw in selected.values()
    }
    if len(targets) != 1:
        details = ", ".join(
            f"{wheel}={draw.draw_number}/{draw.draw_date}"
            for wheel, draw in selected.items()
        )
        raise RuntimeError(
            "Le ruote non condividono la stessa "
            f"estrazione successiva: {details}."
        )

    return tuple(
        sorted(selected.values(), key=lambda draw: draw.wheel_order)
    )


def active_anomalies(
    events: Sequence[AnomalyEvent],
    *,
    latest_draw: int,
    latest_date: str,
) -> tuple[AnomalyEvent, ...]:
    """Return anomalies that are still active at the analyzed target."""

    selected = [
        event
        for event in events
        if (
            event.category == "A1" and event.right_censored
        )
        or (
            event.category in {"A2", "A3", "A4"}
            and event.target_draw == latest_draw
            and event.target_date == latest_date
        )
    ]

    return tuple(
        sorted(
            selected,
            key=lambda event: (
                event.category,
                event.wheel_order,
                event.target_date,
                event.target_draw,
            ),
        )
    )


def states_from_draws(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    *,
    checkpoint_payload: Mapping[str, Any] | None = None,
) -> tuple[CurrentCoverageState, ...]:
    """Reconstruct synchronized current states from draws and optional checkpoint."""

    if checkpoint_payload is None:
        states = tuple(
            current_coverage_state(draws)
            for draws in draws_by_wheel.values()
        )
    else:
        mutable_states = states_from_checkpoint(dict(checkpoint_payload))
        checkpoint_date = str(checkpoint_payload["checkpoint_date"])
        current_draws = tuple(
            draw
            for draws in draws_by_wheel.values()
            for draw in draws
            if draw.draw_date > checkpoint_date
        )

        if not current_draws:
            raise RuntimeError(
                "Nessuna estrazione successiva al checkpoint "
                f"del {checkpoint_date}."
            )

        checkpoint_wheels = set(mutable_states)
        current_wheels = set(draws_by_wheel)
        if checkpoint_wheels != current_wheels:
            missing = sorted(checkpoint_wheels - current_wheels)
            unexpected = sorted(current_wheels - checkpoint_wheels)
            raise RuntimeError(
                "Ruote non allineate tra checkpoint e "
                f"database corrente; mancanti={missing}, "
                f"inattese={unexpected}."
            )

        apply_checkpoint_draws(mutable_states, current_draws)
        converted: list[CurrentCoverageState] = []

        for state in mutable_states.values():
            frozen = freeze_checkpoint_state(state)
            converted.append(
                CurrentCoverageState(
                    wheel=frozen.wheel,
                    wheel_order=frozen.wheel_order,
                    latest_draw=frozen.latest_draw,
                    latest_date=frozen.latest_date,
                    completed_cycles=frozen.completed_cycles,
                    draws_in_cycle=frozen.draws_in_cycle,
                    covered_digits=frozenset(frozen.covered_digits),
                    missing_digits=frozenset(frozen.missing_digits),
                    synchronized=frozen.synchronized,
                    most_present_digits=frozenset(
                        frozen.most_present_digits
                    ),
                )
            )

        states = tuple(
            sorted(
                converted,
                key=lambda state: (state.wheel_order, state.wheel),
            )
        )

    unsynchronized = tuple(
        state for state in states if not state.synchronized
    )
    if unsynchronized:
        raise RuntimeError(
            "Ciclo corrente non sincronizzato per: "
            + ", ".join(state.wheel for state in unsynchronized)
            + "."
        )

    return states


def _markov_report(
    states: Sequence[CurrentCoverageState],
) -> tuple[MarkovWheelReport, ...]:
    rows: list[MarkovWheelReport] = []

    for state in states:
        metrics = maturity_metrics(state.missing_digits, horizons=HORIZONS)
        completion = metrics["completion_within"]
        rows.append(
            MarkovWheelReport(
                state=state,
                completion_within=tuple(
                    (horizon, float(completion[horizon]))
                    for horizon in HORIZONS
                ),
                expected_remaining_draws=float(
                    metrics["expected_remaining_draws"]
                ),
            )
        )

    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.expected_remaining_draws,
                -row.probability_within(1),
                row.state.wheel_order,
            ),
        )
    )


def build_current_coverage_report(
    *,
    all_draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    historical_classes: Mapping[
        tuple[int, int], HistoricalCoverageClass
    ],
    cutoff_date: date | None = None,
    cutoff_draw_number: int | None = None,
    checkpoint_payload: Mapping[str, Any] | None = None,
) -> CurrentCoverageReport:
    """Build the complete current report without rendering terminal output."""

    if cutoff_date is not None and cutoff_draw_number is not None:
        raise ValueError("I cutoff per data e numero sono mutuamente esclusivi.")

    if cutoff_draw_number is not None:
        draws_by_wheel = limit_draws_to_number(
            all_draws_by_wheel, cutoff_draw_number
        )
    else:
        draws_by_wheel = limit_draws_to_date(
            all_draws_by_wheel, cutoff_date
        )

    states = states_from_draws(
        draws_by_wheel,
        checkpoint_payload=checkpoint_payload,
    )
    latest_draw, latest_date = latest_target(states)
    transitions = build_all_transitions(draws_by_wheel)
    anomaly_history = detect_anomalies(transitions)

    return CurrentCoverageReport(
        latest_draw=latest_draw,
        latest_date=latest_date,
        states=states,
        markov_ranking=_markov_report(states),
        coverage_hit_ranking=build_current_coverage_signals(
            states, historical_classes
        ),
        consensus=build_digit_consensus(states),
        anomaly_history=anomaly_history,
        active_anomalies=active_anomalies(
            anomaly_history,
            latest_draw=latest_draw,
            latest_date=latest_date,
        ),
        transition_count=len(transitions),
        next_draws=next_draws_after_target(
            all_draws_by_wheel,
            latest_draw=latest_draw,
            latest_date=latest_date,
        ),
    )
