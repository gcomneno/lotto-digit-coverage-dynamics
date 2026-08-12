"""Presentation-neutral historical coverage-anomaly analysis."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from lotto_digit_coverage.application.historical_symmetry import ordered_draws
from lotto_digit_coverage.domain.draws import DrawSnapshot
from strategies.coverage_completion import ALL_DIGITS, digits_in_draw
from strategies.coverage_markov import (
    completion_probability_within,
    transition_distribution,
    transition_probability,
)


ALL_CATEGORIES = ("A1", "A2", "A3", "A4")
DEFAULT_THRESHOLD = 0.01
DEFAULT_RECURRENCE_WINDOW = 10
DEFAULT_RECURRENCE_THRESHOLD = 0.01


@dataclass(frozen=True)
class TransitionObservation:
    wheel: str
    wheel_order: int
    cycle_number: int
    event_index: int
    position_in_cycle: int
    target_draw: int
    target_date: str
    source_state: tuple[int, ...]
    target_state: tuple[int, ...]
    transition_probability: float


@dataclass(frozen=True)
class AnomalyEvent:
    category: str
    signature: str
    recurrence_key: str
    wheel: str
    wheel_order: int
    cycle_number: int
    event_index: int
    target_draw: int
    target_date: str
    source_state: str
    target_state: str
    horizon: int | None
    conditional_probability: float
    atom_probability: float | None
    previous_conditional_probability: float | None
    pair_probability: float | None
    surprisal: float
    severity: str
    right_censored: bool
    previous_target_draw: int | None
    previous_target_date: str | None
    recurrence_gap: int | None


@dataclass(frozen=True)
class CoverageAnomalyReport:
    transitions: tuple[TransitionObservation, ...]
    events: tuple[AnomalyEvent, ...]
    summary: dict[str, object]
    threshold: float
    recurrence_window: int
    recurrence_threshold: float


def format_state(digits: Sequence[int]) -> str:
    return "{" + ",".join(str(digit) for digit in digits) + "}"


def severity_for_probability(probability: float) -> str:
    if probability <= 0.001:
        return "extreme"
    if probability <= 0.01:
        return "rare"
    if probability <= 0.05:
        return "notable"
    return "ordinary"


def surprisal(probability: float) -> float:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("La probabilità deve appartenere a [0, 1].")
    return math.inf if probability == 0.0 else -math.log10(probability)


def build_transition_observations(
    draws: Sequence[DrawSnapshot],
) -> tuple[TransitionObservation, ...]:
    ordered = ordered_draws(draws)
    if not ordered:
        return ()
    covered: set[int] = set()
    synchronized = False
    cycle_number = 0
    position_in_cycle = 0
    event_index = 0
    observations: list[TransitionObservation] = []

    for draw in ordered:
        observed_digits = digits_in_draw(draw)
        if not synchronized:
            covered.update(observed_digits)
            if covered == ALL_DIGITS:
                synchronized = True
                cycle_number = 1
                covered.clear()
            continue

        source = ALL_DIGITS.difference(covered)
        target = source.difference(observed_digits)
        probability = transition_probability(source, target)
        if probability <= 0.0:
            raise RuntimeError("Transizione osservata con probabilità teorica nulla.")

        event_index += 1
        position_in_cycle += 1
        observations.append(
            TransitionObservation(
                wheel=draw.wheel,
                wheel_order=draw.wheel_order,
                cycle_number=cycle_number,
                event_index=event_index,
                position_in_cycle=position_in_cycle,
                target_draw=draw.draw_number,
                target_date=draw.draw_date,
                source_state=tuple(sorted(source)),
                target_state=tuple(sorted(target)),
                transition_probability=probability,
            )
        )
        if target:
            covered.update(observed_digits)
        else:
            covered.clear()
            cycle_number += 1
            position_in_cycle = 0

    return tuple(observations)


def build_all_transitions(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
) -> tuple[TransitionObservation, ...]:
    observations = [
        observation
        for draws in draws_by_wheel.values()
        for observation in build_transition_observations(draws)
    ]
    return tuple(
        sorted(
            observations,
            key=lambda item: (item.target_date, item.target_draw, item.wheel_order),
        )
    )


def make_primary_event(
    *,
    category: str,
    signature: str,
    recurrence_key: str,
    observation: TransitionObservation,
    source_state: tuple[int, ...],
    target_state: tuple[int, ...],
    horizon: int | None,
    probability: float,
    atom_probability: float | None = None,
    right_censored: bool = False,
) -> AnomalyEvent:
    return AnomalyEvent(
        category=category,
        signature=signature,
        recurrence_key=recurrence_key,
        wheel=observation.wheel,
        wheel_order=observation.wheel_order,
        cycle_number=observation.cycle_number,
        event_index=observation.event_index,
        target_draw=observation.target_draw,
        target_date=observation.target_date,
        source_state=format_state(source_state),
        target_state=format_state(target_state),
        horizon=horizon,
        conditional_probability=probability,
        atom_probability=atom_probability,
        previous_conditional_probability=None,
        pair_probability=None,
        surprisal=surprisal(probability),
        severity=severity_for_probability(probability),
        right_censored=right_censored,
        previous_target_draw=None,
        previous_target_date=None,
        recurrence_gap=None,
    )


def detect_persistence_anomalies(
    transitions: Sequence[TransitionObservation],
    *,
    threshold: float,
) -> tuple[AnomalyEvent, ...]:
    grouped: dict[tuple[str, int], list[TransitionObservation]] = defaultdict(list)
    for observation in transitions:
        grouped[(observation.wheel, observation.cycle_number)].append(observation)

    events: list[AnomalyEvent] = []
    for cycle in grouped.values():
        ordered = sorted(cycle, key=lambda item: item.event_index)
        closure_positions = [
            index for index, item in enumerate(ordered) if not item.target_state
        ]
        if len(closure_positions) > 1:
            raise RuntimeError("Più chiusure nello stesso ciclo.")
        if closure_positions and closure_positions[0] != len(ordered) - 1:
            raise RuntimeError("Transizioni presenti dopo la chiusura.")
        closure_index = closure_positions[0] if closure_positions else None
        right_censored = closure_index is None
        nonclosing_count = len(ordered) if closure_index is None else closure_index
        selected: tuple[
            float,
            int,
            TransitionObservation,
            TransitionObservation,
        ] | None = None

        for detection_index in range(nonclosing_count):
            candidates = []
            detection = ordered[detection_index]
            for start_index in range(detection_index + 1):
                start = ordered[start_index]
                horizon = detection_index - start_index + 1
                probability = max(
                    0.0,
                    1.0 - completion_probability_within(start.source_state, horizon),
                )
                if probability <= threshold:
                    candidates.append((probability, -horizon, start, detection))
            if candidates:
                selected = min(
                    candidates,
                    key=lambda item: (item[0], item[1], item[2].event_index),
                )
                break

        if selected is None:
            continue
        probability, negative_horizon, start, detection = selected
        horizon = -negative_horizon
        source_text = format_state(start.source_state)
        events.append(
            make_primary_event(
                category="A1",
                signature=f"A1:persistence:{source_text}:h={horizon}",
                recurrence_key=f"A1:persistence:{source_text}",
                observation=detection,
                source_state=start.source_state,
                target_state=detection.target_state,
                horizon=horizon,
                probability=probability,
                right_censored=right_censored,
            )
        )
    return tuple(events)


def transition_surprise_probability(
    source_state: Sequence[int],
    target_state: Sequence[int],
) -> float:
    source = frozenset(source_state)
    target = frozenset(target_state)
    if not target or target == source:
        raise ValueError(
            "A3 richiede una transizione di progresso non terminale."
        )
    observed_atom = transition_probability(source, target)
    tolerance = 1e-15
    tail = sum(
        probability
        for candidate, probability in transition_distribution(source).items()
        if candidate
        and candidate != source
        and probability <= observed_atom + tolerance
    )
    return min(1.0, max(0.0, tail))


def detect_transition_anomalies(
    transitions: Sequence[TransitionObservation],
    *,
    threshold: float,
) -> tuple[AnomalyEvent, ...]:
    events: list[AnomalyEvent] = []
    for observation in transitions:
        atom = observation.transition_probability
        source = observation.source_state
        target = observation.target_state
        source_text = format_state(source)
        target_text = format_state(target)
        if not target:
            if atom <= threshold:
                events.append(
                    make_primary_event(
                        category="A2",
                        signature=f"A2:closure:{source_text}->{{}}",
                        recurrence_key=f"A2:closure:{source_text}",
                        observation=observation,
                        source_state=source,
                        target_state=target,
                        horizon=1,
                        probability=atom,
                        atom_probability=atom,
                    )
                )
            continue
        if target == source:
            continue
        event_probability = transition_surprise_probability(source, target)
        if event_probability <= threshold:
            events.append(
                make_primary_event(
                    category="A3",
                    signature=f"A3:transition:{source_text}->{target_text}",
                    recurrence_key=f"A3:transition:{source_text}->{target_text}",
                    observation=observation,
                    source_state=source,
                    target_state=target,
                    horizon=1,
                    probability=event_probability,
                    atom_probability=atom,
                )
            )
    return tuple(events)


def detect_recurrence_anomalies(
    primary_events: Sequence[AnomalyEvent],
    *,
    max_gap: int,
    threshold: float,
) -> tuple[AnomalyEvent, ...]:
    if max_gap <= 0:
        raise ValueError("La finestra di ricorrenza deve essere positiva.")
    previous: dict[tuple[str, str], AnomalyEvent] = {}
    recurrences: list[AnomalyEvent] = []
    for event in sorted(
        primary_events,
        key=lambda item: (
            item.target_date,
            item.target_draw,
            item.wheel_order,
            item.category,
            item.signature,
        ),
    ):
        key = (event.wheel, event.recurrence_key)
        prior = previous.get(key)
        if prior is not None:
            gap = event.event_index - prior.event_index
            pair_probability = (
                prior.conditional_probability * event.conditional_probability
            )
            probability = min(1.0, max_gap * event.conditional_probability)
            if 0 < gap <= max_gap and probability <= threshold:
                recurrences.append(
                    AnomalyEvent(
                        category="A4",
                        signature=f"A4:recurrence:{event.recurrence_key}:gap={gap}",
                        recurrence_key=f"A4:recurrence:{event.recurrence_key}",
                        wheel=event.wheel,
                        wheel_order=event.wheel_order,
                        cycle_number=event.cycle_number,
                        event_index=event.event_index,
                        target_draw=event.target_draw,
                        target_date=event.target_date,
                        source_state=event.source_state,
                        target_state=event.target_state,
                        horizon=None,
                        conditional_probability=probability,
                        atom_probability=event.atom_probability,
                        previous_conditional_probability=prior.conditional_probability,
                        pair_probability=pair_probability,
                        surprisal=surprisal(probability),
                        severity=severity_for_probability(probability),
                        right_censored=False,
                        previous_target_draw=prior.target_draw,
                        previous_target_date=prior.target_date,
                        recurrence_gap=gap,
                    )
                )
        previous[key] = event
    return tuple(recurrences)


def anomaly_identity(event: AnomalyEvent) -> tuple[object, ...]:
    return (
        event.category,
        event.wheel,
        event.cycle_number,
        event.event_index,
        event.signature,
    )


def validate_anomalies(events: Sequence[AnomalyEvent]) -> None:
    identities = [anomaly_identity(event) for event in events]
    if len(identities) != len(set(identities)):
        raise RuntimeError("Eventi anomali duplicati.")
    if any(event.category not in ALL_CATEGORIES for event in events):
        raise RuntimeError("Categoria anomala sconosciuta.")
    persistence_cycles = [
        (event.wheel, event.cycle_number)
        for event in events
        if event.category == "A1"
    ]
    if len(persistence_cycles) != len(set(persistence_cycles)):
        raise RuntimeError("Più anomalie A1 nello stesso ciclo.")

    transition_categories: dict[tuple[str, int], set[str]] = defaultdict(set)
    for event in events:
        if event.category in {"A2", "A3"}:
            transition_categories[(event.wheel, event.event_index)].add(event.category)
        if not 0.0 <= event.conditional_probability <= 1.0:
            raise RuntimeError("Probabilità anomala non valida.")
        if event.category == "A4" and (
            event.previous_target_draw is None
            or event.previous_target_date is None
            or event.recurrence_gap is None
        ):
            raise RuntimeError("Ricorrenza senza predecessore.")
    if any(
        categories == {"A2", "A3"}
        for categories in transition_categories.values()
    ):
        raise RuntimeError("Una transizione è classificata sia A2 sia A3.")


def detect_anomalies(
    transitions: Sequence[TransitionObservation],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    recurrence_window: int = DEFAULT_RECURRENCE_WINDOW,
    recurrence_threshold: float = DEFAULT_RECURRENCE_THRESHOLD,
) -> tuple[AnomalyEvent, ...]:
    if not 0.0 < threshold <= 1.0:
        raise ValueError("La soglia primaria deve appartenere a (0, 1].")
    if not 0.0 < recurrence_threshold <= 1.0:
        raise ValueError("La soglia di ricorrenza deve appartenere a (0, 1].")
    primary = detect_persistence_anomalies(
        transitions,
        threshold=threshold,
    ) + detect_transition_anomalies(transitions, threshold=threshold)
    recurrences = detect_recurrence_anomalies(
        primary,
        max_gap=recurrence_window,
        threshold=recurrence_threshold,
    )
    events = tuple(
        sorted(
            primary + recurrences,
            key=lambda item: (
                item.target_date,
                item.target_draw,
                item.wheel_order,
                item.category,
                item.signature,
            ),
        )
    )
    validate_anomalies(events)
    return events


def summary_document(events: Sequence[AnomalyEvent]) -> dict[str, object]:
    category_counts = Counter(event.category for event in events)
    severity_counts = Counter(event.severity for event in events)
    return {
        "event_count": len(events),
        "category_counts": {
            category: category_counts.get(category, 0)
            for category in ALL_CATEGORIES
        },
        "severity_counts": dict(sorted(severity_counts.items())),
        "right_censored_a1_count": sum(
            event.category == "A1" and event.right_censored for event in events
        ),
        "unique_signatures": len({event.signature for event in events}),
        "duplicate_event_count": len(events)
        - len({anomaly_identity(event) for event in events}),
        "primary_transition_overlap_count": sum(
            count > 1
            for count in Counter(
                (event.wheel, event.event_index)
                for event in events
                if event.category in {"A1", "A2", "A3"}
            ).values()
        ),
    }


def build_coverage_anomaly_report(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    recurrence_window: int = DEFAULT_RECURRENCE_WINDOW,
    recurrence_threshold: float = DEFAULT_RECURRENCE_THRESHOLD,
) -> CoverageAnomalyReport:
    transitions = build_all_transitions(draws_by_wheel)
    events = detect_anomalies(
        transitions,
        threshold=threshold,
        recurrence_window=recurrence_window,
        recurrence_threshold=recurrence_threshold,
    )
    return CoverageAnomalyReport(
        transitions=transitions,
        events=events,
        summary=summary_document(events),
        threshold=threshold,
        recurrence_window=recurrence_window,
        recurrence_threshold=recurrence_threshold,
    )
