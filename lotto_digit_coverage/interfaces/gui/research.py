"""GUI-specific view models over presentation-neutral historical services."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lotto_digit_coverage.application.historical_markov import (
    build_coverage_completion_report,
    build_markov_residual_report,
    build_markov_validation_report,
)
from lotto_digit_coverage.application.historical_twins import build_twin_number_report
from lotto_digit_coverage.infrastructure.historical_archives import load_draw_collection
from lotto_digit_coverage.infrastructure.sqlite_lotto_repository import SQLiteLottoRepository


HISTORICAL_DATABASE = Path("data/lotto-2025.sqlite3")
TWIN_DATABASE = Path("data/lotto-1871-2025.sqlite3")

RESEARCH_CATALOG: tuple[dict[str, str], ...] = (
    {
        "id": "completion",
        "title": "Cycle completion",
        "summary": "One-step probability and residual distance by coverage state.",
        "interpretation": "descriptive",
    },
    {
        "id": "validation",
        "title": "Markov calibration",
        "summary": "Comparison between theoretical probabilities and observed completions.",
        "interpretation": "descriptive-calibration",
    },
    {
        "id": "residuals",
        "title": "Markov residual duration",
        "summary": "Comparison between theoretical and observed residual duration.",
        "interpretation": "descriptive-validation",
    },
    {
        "id": "twins",
        "title": "Twin numbers 11–88",
        "summary": "One-step screen against the exact 1/18 null with multiple gates.",
        "interpretation": "exploratory-screen",
    },
)


def research_catalog() -> list[dict[str, str]]:
    return [dict(item) for item in RESEARCH_CATALOG]


def _column(key: str, label: str, value_format: str = "text") -> dict[str, str]:
    return {"key": key, "label": label, "format": value_format}


def _metric(label: str, value: Any, value_format: str = "text") -> dict[str, Any]:
    return {"label": label, "value": value, "format": value_format}


def _completion_payload(root: Path) -> dict[str, Any]:
    database = root / HISTORICAL_DATABASE
    with SQLiteLottoRepository(database) as repository:
        report = build_coverage_completion_report(repository)

    rows = [
        {
            "missing": group.key,
            "cases": group.summary.cases,
            "completions": group.summary.completions,
            "observed": group.summary.observed_probability,
            "theoretical": group.summary.theoretical_probability,
            "delta": group.summary.delta,
        }
        for group in report.by_missing_count
    ]
    return {
        "id": "completion",
        "title": "Cycle completion",
        "interpretation": (
            "Descriptive comparison between observed one-step frequencies and exact "
            "state probabilities. The first cycle of each wheel remains excluded because "
            "it is left-censored."
        ),
        "source": str(HISTORICAL_DATABASE),
        "metrics": [
            _metric("Incomplete states", len(report.observations), "integer"),
            _metric("Right-censored states", report.right_censored_states, "integer"),
            _metric("Exact-state threshold", report.minimum_state_cases, "integer"),
        ],
        "tables": [
            {
                "title": "By number of missing digits",
                "columns": [
                    _column("missing", "Missing", "integer"),
                    _column("cases", "Cases", "integer"),
                    _column("completions", "Completions", "integer"),
                    _column("observed", "Observed", "percentage"),
                    _column("theoretical", "Theoretical", "percentage"),
                    _column("delta", "Delta", "percentage-signed"),
                ],
                "rows": rows,
            }
        ],
        "notes": [
            "Historical frequencies do not change the theoretical probability of the next event."
        ],
    }


def _validation_payload(root: Path) -> dict[str, Any]:
    database = root / HISTORICAL_DATABASE
    with SQLiteLottoRepository(database) as repository:
        report = build_markov_validation_report(repository)

    rows = [
        {
            "horizon": group.key,
            "cases": group.summary.cases,
            "completions": group.summary.completions,
            "observed": group.summary.observed_probability,
            "predicted": group.summary.predicted_probability,
            "delta": group.summary.delta,
            "brier": group.summary.brier_score,
        }
        for group in report.overall
    ]
    return {
        "id": "validation",
        "title": "Markov calibration",
        "interpretation": (
            "Descriptive calibration validation. Observations overlap and are dependent; "
            "the report is not an inferential test."
        ),
        "source": str(HISTORICAL_DATABASE),
        "metrics": [
            _metric("Observations", len(report.observations), "integer"),
            _metric("Horizons", ", ".join(str(value) for value in report.horizons)),
            _metric("Exact-state threshold", report.minimum_state_cases, "integer"),
        ],
        "tables": [
            {
                "title": "Overall calibration",
                "columns": [
                    _column("horizon", "Within", "integer"),
                    _column("cases", "Cases", "integer"),
                    _column("completions", "Completions", "integer"),
                    _column("observed", "Observed", "percentage"),
                    _column("predicted", "Predicted", "percentage"),
                    _column("delta", "Delta", "percentage-signed"),
                    _column("brier", "Brier", "decimal-4"),
                ],
                "rows": rows,
            }
        ],
        "notes": [
            "Good calibration describes the model; it does not constitute a predictive gambling advantage."
        ],
    }


def _residual_payload(root: Path) -> dict[str, Any]:
    database = root / HISTORICAL_DATABASE
    with SQLiteLottoRepository(database) as repository:
        report = build_markov_residual_report(repository)

    rows = [
        {
            "missing": group.key,
            "states": group.summary.states,
            "actual": group.summary.actual_mean,
            "predicted": group.summary.predicted_mean,
            "bias": group.summary.bias,
            "mae": group.summary.mean_absolute_error,
            "rmse": group.summary.root_mean_square_error,
        }
        for group in report.by_missing_count
    ]
    overall = report.overall
    return {
        "id": "residuals",
        "title": "Markov residual duration",
        "interpretation": (
            "Descriptive comparison between observed residual time and Markov expectation. "
            "Only states whose subsequent completion is observable are included."
        ),
        "source": str(HISTORICAL_DATABASE),
        "metrics": [
            _metric("States", overall.states, "integer"),
            _metric("Actual residual", overall.actual_mean, "decimal-3"),
            _metric("Predicted residual", overall.predicted_mean, "decimal-3"),
            _metric("Bias", overall.bias, "decimal-signed-3"),
            _metric("MAE", overall.mean_absolute_error, "decimal-3"),
            _metric("RMSE", overall.root_mean_square_error, "decimal-3"),
        ],
        "tables": [
            {
                "title": "By number of missing digits",
                "columns": [
                    _column("missing", "Missing", "integer"),
                    _column("states", "States", "integer"),
                    _column("actual", "Actual", "decimal-3"),
                    _column("predicted", "Predicted", "decimal-3"),
                    _column("bias", "Bias", "decimal-signed-3"),
                    _column("mae", "MAE", "decimal-3"),
                    _column("rmse", "RMSE", "decimal-3"),
                ],
                "rows": rows,
            }
        ],
        "notes": ["Subsequent observations from the same cycle are not independent."],
    }


def _twins_payload(root: Path) -> dict[str, Any]:
    database = root / TWIN_DATABASE
    report = build_twin_number_report(load_draw_collection(database))

    rows = [
        {
            "condition": row.condition,
            "twin": row.twin_number,
            "cases": row.cases,
            "hits": row.hits,
            "expected": row.expected_hits,
            "observed": row.observed_probability,
            "lift": row.lift_probability,
            "wilson_low": row.wilson_low,
            "wilson_high": row.wilson_high,
            "q": row.q_value,
            "candidate": row.candidate,
        }
        for row in report.rows
    ]
    return {
        "id": "twins",
        "title": "Twin numbers 11–88",
        "interpretation": (
            "Exploratory one-step screen against the exact 1/18 null. Any candidate state "
            "still requires chronological out-of-sample or forward validation before any "
            "predictive interpretation."
        ),
        "source": str(TWIN_DATABASE),
        "metrics": [
            _metric("Observations", len(report.observations), "integer"),
            _metric("First target", report.first_target_date),
            _metric("Last target", report.last_target_date),
            _metric("Exploratory candidates", report.candidate_count, "integer"),
        ],
        "tables": [
            {
                "title": "Screen by condition and twin",
                "columns": [
                    _column("condition", "Condition"),
                    _column("twin", "Twin", "lotto-number"),
                    _column("cases", "Cases", "integer"),
                    _column("hits", "Hits", "integer"),
                    _column("expected", "Expected", "decimal-2"),
                    _column("observed", "Observed", "percentage"),
                    _column("lift", "Lift", "percentage-signed"),
                    _column("wilson_low", "CI95-", "percentage"),
                    _column("wilson_high", "CI95+", "percentage"),
                    _column("q", "q BH", "decimal-4"),
                    _column("candidate", "Outcome", "candidate"),
                ],
                "rows": rows,
            }
        ],
        "notes": [
            "Wheels share the calendar and are not treated as independent replicates.",
            "The GUI does not promote a historical screen to an operational trigger.",
        ],
    }


_LOADERS = {
    "completion": _completion_payload,
    "validation": _validation_payload,
    "residuals": _residual_payload,
    "twins": _twins_payload,
}


def load_research_payload(root: Path, report_id: str) -> dict[str, Any]:
    try:
        loader = _LOADERS[report_id]
    except KeyError as error:
        raise ValueError(f"Unknown research report: {report_id}") from error
    return loader(root)
