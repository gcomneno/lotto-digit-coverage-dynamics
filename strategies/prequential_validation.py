"""Primitive per una validazione prequentiale immutabile."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from strategies.coverage_completion import CurrentCoverageState
from strategies.coverage_markov import maturity_metrics


FORECAST_FORMAT_VERSION = 1
MODEL_ID = "digit-coverage-markov-v1"
DEFAULT_HORIZONS = (1, 2, 3, 5)


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def default_forecast_path(
    target_draw: int,
) -> Path:
    if target_draw <= 0:
        raise ValueError(
            "Il numero del concorso deve essere positivo."
        )

    return Path(
        "prequential/forecasts"
    ) / f"draw-{target_draw:04d}.json"


def normalize_horizons(
    horizons: Iterable[int],
) -> tuple[int, ...]:
    normalized = tuple(sorted(set(horizons)))

    if not normalized:
        raise ValueError(
            "Serve almeno un orizzonte."
        )

    if any(horizon <= 0 for horizon in normalized):
        raise ValueError(
            "Gli orizzonti devono essere positivi."
        )

    return normalized


def build_forecast_document(
    states: Sequence[CurrentCoverageState],
    *,
    database_path: Path,
    database_sha256: str,
    repository_commit: str,
    generated_at_utc: str,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> dict[str, object]:
    if not states:
        raise ValueError(
            "Serve almeno uno stato di copertura."
        )

    normalized_horizons = normalize_horizons(horizons)

    latest_draws = {
        state.latest_draw
        for state in states
    }

    latest_dates = {
        state.latest_date
        for state in states
    }

    if len(latest_draws) != 1:
        raise ValueError(
            "Le ruote non sono allineate sullo stesso concorso."
        )

    if len(latest_dates) != 1:
        raise ValueError(
            "Le ruote non sono allineate sulla stessa data."
        )

    if any(not state.synchronized for state in states):
        raise ValueError(
            "Tutte le ruote devono avere un ciclo sincronizzato."
        )

    wheel_names = [
        state.wheel
        for state in states
    ]

    if len(wheel_names) != len(set(wheel_names)):
        raise ValueError(
            "Le ruote devono essere univoche."
        )

    source_latest_draw = next(iter(latest_draws))
    source_latest_date = next(iter(latest_dates))
    target_draw = source_latest_draw + 1

    wheel_forecasts: list[dict[str, object]] = []

    for state in sorted(
        states,
        key=lambda item: item.wheel_order,
    ):
        metrics = maturity_metrics(
            state.missing_digits,
            horizons=normalized_horizons,
        )

        completion = metrics["completion_within"]

        wheel_forecasts.append(
            {
                "wheel": state.wheel,
                "wheel_order": state.wheel_order,
                "completed_cycles": state.completed_cycles,
                "cycle_age": state.draws_in_cycle,
                "covered_digits": sorted(
                    state.covered_digits
                ),
                "missing_digits": sorted(
                    state.missing_digits
                ),
                "completion_probability_within": {
                    str(horizon): completion[horizon]
                    for horizon in normalized_horizons
                },
                "expected_remaining_draws": (
                    metrics["expected_remaining_draws"]
                ),
            }
        )

    return {
        "forecast_format_version": FORECAST_FORMAT_VERSION,
        "model_id": MODEL_ID,
        "status": "pending",
        "generated_at_utc": generated_at_utc,
        "repository_commit": repository_commit,
        "source_database": str(database_path),
        "source_database_sha256": database_sha256,
        "source_latest_draw": source_latest_draw,
        "source_latest_date": source_latest_date,
        "target_draw": target_draw,
        "horizons": list(normalized_horizons),
        "wheel_count": len(wheel_forecasts),
        "interpretation": (
            "State-dependent coverage probabilities; "
            "not evidence of a gambling advantage."
        ),
        "wheels": wheel_forecasts,
    }


def canonical_json_bytes(
    document: Mapping[str, object],
) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def document_sha256(
    document: Mapping[str, object],
) -> str:
    return hashlib.sha256(
        canonical_json_bytes(document)
    ).hexdigest()


def write_forecast_document(
    document: Mapping[str, object],
    path: Path,
) -> str:
    """
    Scrive il forecast una sola volta.

    L'apertura esclusiva impedisce la sovrascrittura di una previsione
    già congelata.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = canonical_json_bytes(document)

    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise FileExistsError(
            f"Forecast già esistente e immutabile: {path}"
        ) from error

    return hashlib.sha256(payload).hexdigest()
