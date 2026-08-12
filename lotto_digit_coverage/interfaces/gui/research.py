"""GUI-specific view models over presentation-neutral historical services."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lotto_digit_coverage.application.historical_markov import (
    build_coverage_completion_report,
    build_markov_residual_report,
    build_markov_validation_report,
)
from lotto_digit_coverage.application.historical_twins import (
    build_twin_number_report,
)
from lotto_digit_coverage.infrastructure.historical_archives import (
    load_draw_collection,
)
from lotto_digit_coverage.infrastructure.sqlite_lotto_repository import (
    SQLiteLottoRepository,
)


HISTORICAL_DATABASE = Path("data/lotto-2025.sqlite3")
TWIN_DATABASE = Path("data/lotto-1871-2025.sqlite3")

RESEARCH_CATALOG: tuple[dict[str, str], ...] = (
    {
        "id": "completion",
        "title": "Completamento dei cicli",
        "summary": "Probabilità one-step e distanza residua per stato di copertura.",
        "interpretation": "descriptive",
    },
    {
        "id": "validation",
        "title": "Calibrazione Markov",
        "summary": "Confronto tra probabilità teoriche e completamenti osservati.",
        "interpretation": "descriptive-calibration",
    },
    {
        "id": "residuals",
        "title": "Durata residua Markov",
        "summary": "Confronto tra attesa residua teorica e durata residua osservata.",
        "interpretation": "descriptive-validation",
    },
    {
        "id": "twins",
        "title": "Numeri gemelli 11–88",
        "summary": "Screen one-step contro il null esatto 1/18 con gate multipli.",
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
        "title": "Completamento dei cicli",
        "interpretation": (
            "Confronto descrittivo tra frequenze one-step osservate e probabilità "
            "esatte dello stato. Il primo ciclo di ogni ruota resta escluso perché "
            "censurato a sinistra."
        ),
        "source": str(HISTORICAL_DATABASE),
        "metrics": [
            _metric("Stati incompleti", len(report.observations), "integer"),
            _metric("Stati censurati a destra", report.right_censored_states, "integer"),
            _metric("Soglia stati esatti", report.minimum_state_cases, "integer"),
        ],
        "tables": [
            {
                "title": "Per numero di cifre mancanti",
                "columns": [
                    _column("missing", "Mancanti", "integer"),
                    _column("cases", "Casi", "integer"),
                    _column("completions", "Chiusure", "integer"),
                    _column("observed", "Osservato", "percentage"),
                    _column("theoretical", "Teorico", "percentage"),
                    _column("delta", "Delta", "percentage-signed"),
                ],
                "rows": rows,
            }
        ],
        "notes": [
            "Le frequenze storiche non modificano la probabilità teorica del prossimo evento."
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
        "title": "Calibrazione Markov",
        "interpretation": (
            "Validazione descrittiva della calibrazione. Le osservazioni sono "
            "sovrapposte e dipendenti: il report non è un test inferenziale."
        ),
        "source": str(HISTORICAL_DATABASE),
        "metrics": [
            _metric("Osservazioni", len(report.observations), "integer"),
            _metric("Orizzonti", ", ".join(str(value) for value in report.horizons)),
            _metric("Soglia stati esatti", report.minimum_state_cases, "integer"),
        ],
        "tables": [
            {
                "title": "Calibrazione complessiva",
                "columns": [
                    _column("horizon", "Entro", "integer"),
                    _column("cases", "Casi", "integer"),
                    _column("completions", "Chiusure", "integer"),
                    _column("observed", "Osservato", "percentage"),
                    _column("predicted", "Previsto", "percentage"),
                    _column("delta", "Delta", "percentage-signed"),
                    _column("brier", "Brier", "decimal-4"),
                ],
                "rows": rows,
            }
        ],
        "notes": [
            "Una buona calibrazione descrive il modello; non costituisce un vantaggio predittivo sul gioco."
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
        "title": "Durata residua Markov",
        "interpretation": (
            "Confronto descrittivo tra tempo residuo osservato e attesa Markov. "
            "Sono inclusi soltanto stati il cui completamento successivo è osservabile."
        ),
        "source": str(HISTORICAL_DATABASE),
        "metrics": [
            _metric("Stati", overall.states, "integer"),
            _metric("Residuo reale", overall.actual_mean, "decimal-3"),
            _metric("Residuo previsto", overall.predicted_mean, "decimal-3"),
            _metric("Bias", overall.bias, "decimal-signed-3"),
            _metric("MAE", overall.mean_absolute_error, "decimal-3"),
            _metric("RMSE", overall.root_mean_square_error, "decimal-3"),
        ],
        "tables": [
            {
                "title": "Per numero di cifre mancanti",
                "columns": [
                    _column("missing", "Mancanti", "integer"),
                    _column("states", "Stati", "integer"),
                    _column("actual", "Reale", "decimal-3"),
                    _column("predicted", "Previsto", "decimal-3"),
                    _column("bias", "Bias", "decimal-signed-3"),
                    _column("mae", "MAE", "decimal-3"),
                    _column("rmse", "RMSE", "decimal-3"),
                ],
                "rows": rows,
            }
        ],
        "notes": [
            "Le osservazioni successive dello stesso ciclo non sono indipendenti."
        ],
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
        "title": "Numeri gemelli 11–88",
        "interpretation": (
            "Screen esplorativo one-step contro il null esatto 1/18. Uno stato "
            "eventualmente candidato richiede comunque validazione cronologica "
            "out-of-sample o forward prima di qualunque interpretazione predittiva."
        ),
        "source": str(TWIN_DATABASE),
        "metrics": [
            _metric("Osservazioni", len(report.observations), "integer"),
            _metric("Primo target", report.first_target_date),
            _metric("Ultimo target", report.last_target_date),
            _metric("Candidati esplorativi", report.candidate_count, "integer"),
        ],
        "tables": [
            {
                "title": "Screen per condizione e gemello",
                "columns": [
                    _column("condition", "Condizione"),
                    _column("twin", "Gemello", "lotto-number"),
                    _column("cases", "Casi", "integer"),
                    _column("hits", "Hit", "integer"),
                    _column("expected", "Attesi", "decimal-2"),
                    _column("observed", "Osservato", "percentage"),
                    _column("lift", "Lift", "percentage-signed"),
                    _column("wilson_low", "CI95-", "percentage"),
                    _column("wilson_high", "CI95+", "percentage"),
                    _column("q", "q BH", "decimal-4"),
                    _column("candidate", "Esito", "candidate"),
                ],
                "rows": rows,
            }
        ],
        "notes": [
            "Le ruote condividono il calendario e non sono trattate come repliche indipendenti.",
            "La GUI non promuove uno screen storico a trigger operativo."
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
        raise ValueError(f"Report di ricerca sconosciuto: {report_id}") from error
    return loader(root)
