"""Stable JSON-compatible contracts for migrated application reports."""

from __future__ import annotations

import json
from typing import Any

from lotto_digit_coverage.application.current import CurrentCoverageReport
from lotto_digit_coverage.application.occurrence_groups import OccurrenceGroupReport


SCHEMA_VERSION = 1
NUMBER_REPRESENTATION = {
    "type": "integer",
    "minimum": 1,
    "maximum": 90,
    "display_width": 2,
}


def _digits(values) -> list[int]:
    return sorted(int(value) for value in values)


def _draw(draw) -> dict[str, Any]:
    return {
        "draw_number": draw.draw_number,
        "draw_date": draw.draw_date,
        "wheel": draw.wheel,
        "wheel_order": draw.wheel_order,
        "numbers": list(draw.numbers),
    }


def _state(state) -> dict[str, Any]:
    return {
        "wheel": state.wheel,
        "wheel_order": state.wheel_order,
        "latest_draw": state.latest_draw,
        "latest_date": state.latest_date,
        "completed_cycles": state.completed_cycles,
        "draws_in_cycle": state.draws_in_cycle,
        "covered_digits": _digits(state.covered_digits),
        "missing_digits": _digits(state.missing_digits),
        "most_present_digits": _digits(state.most_present_digits),
        "synchronized": state.synchronized,
    }


def _signal(signal) -> dict[str, Any]:
    historical = signal.historical
    return {
        "wheel": signal.wheel,
        "wheel_order": signal.wheel_order,
        "draws_in_cycle": signal.draws_in_cycle,
        "class": {
            "most_present_count": len(signal.most_present_digits),
            "missing_count": len(signal.missing_digits),
        },
        "most_present_digits": _digits(signal.most_present_digits),
        "missing_digits": _digits(signal.missing_digits),
        "historical": {
            "threshold": historical.threshold,
            "cases": historical.cases,
            "obtained": historical.obtained,
            "success_rate": historical.success_rate,
            "expected_probability": historical.expected_probability,
            "evidence_level": historical.evidence_level,
        },
        "current_event_probability": signal.current_event_probability,
        "completion_within_one": signal.completion_within_one,
        "lower_success_bound": signal.lower_success_bound,
        "conservative_excess": signal.conservative_excess,
        "conservative_probability": signal.conservative_probability,
    }


def _consensus(row) -> dict[str, Any]:
    return {
        "digit": row.digit,
        "missing_count": row.missing_count,
        "top_count": row.top_count,
        "missing_wheels": list(row.missing_wheels),
        "top_wheels": list(row.top_wheels),
        "involved_wheels": list(row.involved_wheels),
    }


def _anomaly(event) -> dict[str, Any]:
    return {
        "category": event.category,
        "signature": event.signature,
        "recurrence_key": event.recurrence_key,
        "wheel": event.wheel,
        "wheel_order": event.wheel_order,
        "cycle_number": event.cycle_number,
        "event_index": event.event_index,
        "target_draw": event.target_draw,
        "target_date": event.target_date,
        "source_state": event.source_state,
        "target_state": event.target_state,
        "horizon": event.horizon,
        "conditional_probability": event.conditional_probability,
        "atom_probability": event.atom_probability,
        "previous_conditional_probability": event.previous_conditional_probability,
        "pair_probability": event.pair_probability,
        "surprisal": event.surprisal,
        "severity": event.severity,
        "right_censored": event.right_censored,
        "previous_target_draw": event.previous_target_draw,
        "previous_target_date": event.previous_target_date,
        "recurrence_gap": event.recurrence_gap,
    }


def current_report_to_dict(report: CurrentCoverageReport) -> dict[str, Any]:
    """Serialize current status through an explicit versioned contract."""

    return {
        "schema": "lotto.current",
        "schema_version": SCHEMA_VERSION,
        "number_representation": dict(NUMBER_REPRESENTATION),
        "target": {
            "draw_number": report.latest_draw,
            "draw_date": report.latest_date,
        },
        "states": [_state(state) for state in report.states],
        "markov_ranking": [
            {
                "position": position,
                "wheel": row.state.wheel,
                "wheel_order": row.state.wheel_order,
                "expected_remaining_draws": row.expected_remaining_draws,
                "completion_within": {
                    str(horizon): probability
                    for horizon, probability in row.completion_within
                },
            }
            for position, row in enumerate(report.markov_ranking, start=1)
        ],
        "coverage_hit_ranking": [
            {
                "position": position,
                **_signal(signal),
            }
            for position, signal in enumerate(
                report.coverage_hit_ranking,
                start=1,
            )
        ],
        "consensus": [_consensus(row) for row in report.consensus],
        "anomalies": {
            "transition_count": report.transition_count,
            "history": [_anomaly(event) for event in report.anomaly_history],
            "active": [_anomaly(event) for event in report.active_anomalies],
        },
        "next_draw_validation": [_draw(draw) for draw in report.next_draws],
    }


def occurrence_group_report_to_dict(
    report: OccurrenceGroupReport,
) -> dict[str, Any]:
    """Serialize occurrence groups through an explicit versioned contract."""

    return {
        "schema": "lotto.occurrence-groups",
        "schema_version": SCHEMA_VERSION,
        "number_representation": dict(NUMBER_REPRESENTATION),
        "reference": {
            "draw_number": report.reference_draw_number,
            "draw_date": report.reference_draw_date,
            "kind": report.reference_kind,
        },
        "group_size": report.group_size,
        "groups": [
            {
                "reference": {
                    "draw_number": group.reference_draw_number,
                    "draw_date": group.reference_draw_date,
                },
                "range": {
                    "newest": {
                        "draw_number": group.newest_draw_number,
                        "draw_date": group.newest_draw_date,
                    },
                    "oldest": {
                        "draw_number": group.oldest_draw_number,
                        "draw_date": group.oldest_draw_date,
                    },
                },
                "actual_size": group.size,
                "draws": [
                    {
                        "draw_number": draw.draw_number,
                        "draw_date": draw.draw_date,
                        "wheels": [
                            {
                                "wheel": wheel,
                                "numbers": list(numbers),
                            }
                            for wheel, numbers in draw.wheel_numbers
                        ],
                    }
                    for draw in group.draws
                ],
                "wheels": [
                    {
                        "wheel": wheel.wheel,
                        "reference_numbers": list(wheel.reference_numbers),
                        "occurrence_counts": list(wheel.occurrence_counts),
                    }
                    for wheel in group.wheels
                ],
            }
            for group in report.groups
        ],
    }


def dumps_report(payload: dict[str, Any]) -> str:
    """Return deterministic UTF-8-friendly JSON with a trailing newline."""

    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def dumps_current_report(report: CurrentCoverageReport) -> str:
    return dumps_report(current_report_to_dict(report))


def dumps_occurrence_group_report(report: OccurrenceGroupReport) -> str:
    return dumps_report(occurrence_group_report_to_dict(report))
