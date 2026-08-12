"""JSON-compatible bridge between the desktop frontend and Python services."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from analyze_current_coverage import checkpoint_for_current_archive
from lotto_digit_coverage.application.current import build_current_coverage_report
from lotto_digit_coverage.application.occurrence_groups import (
    DrawKey,
    WheelNumbers,
    build_occurrence_group_report,
)
from lotto_digit_coverage.application.reporting import (
    current_report_to_dict,
    occurrence_group_report_to_dict,
)
from lotto_digit_coverage.domain.draws import DrawSnapshot
from lotto_digit_coverage.infrastructure.sqlite_lotto_repository import (
    SQLiteLottoRepository,
)
from strategies.current_coverage_signal import (
    DEFAULT_HISTORICAL_SUMMARY,
    load_historical_coverage_classes,
)


DEFAULT_DATABASE = Path("data/lotto-current.sqlite3")

PayloadLoader = Callable[..., dict[str, Any]]


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _parse_optional_date(value: str | None) -> date | None:
    if value is None or value == "":
        return None
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("La data deve usare il formato YYYY-MM-DD.")
    return parsed


def _occurrence_input(
    draws_by_wheel: Mapping[str, Sequence[DrawSnapshot]],
) -> tuple[dict[DrawKey, dict[str, tuple[int, ...]]], tuple[str, ...]]:
    ordered_wheels = tuple(
        sorted(
            draws_by_wheel,
            key=lambda wheel: (
                draws_by_wheel[wheel][0].wheel_order
                if draws_by_wheel[wheel]
                else 10_000,
                wheel,
            ),
        )
    )
    draws: dict[DrawKey, dict[str, tuple[int, ...]]] = {}

    for wheel in ordered_wheels:
        for draw in draws_by_wheel[wheel]:
            key = (draw.draw_number, draw.draw_date)
            draws.setdefault(key, {})[wheel] = tuple(draw.numbers)

    return draws, ordered_wheels


def load_current_payload(
    *,
    root: Path,
    database: str | Path = DEFAULT_DATABASE,
    to_draw_number: int | None = None,
    to_date: str | None = None,
    use_checkpoint: bool = True,
) -> dict[str, Any]:
    """Build the stable current contract without terminal rendering."""

    if to_draw_number is not None and to_date:
        raise ValueError("Specificare al massimo uno tra numero e data di cutoff.")
    if to_draw_number is not None and (
        not isinstance(to_draw_number, int)
        or isinstance(to_draw_number, bool)
        or to_draw_number <= 0
    ):
        raise ValueError("Il numero di cutoff deve essere un intero positivo.")

    database_path = _resolve_path(root, database)
    with SQLiteLottoRepository(database_path) as repository:
        all_draws_by_wheel = repository.draws_by_wheel()

    checkpoint_payload = None
    if use_checkpoint:
        _checkpoint_path, checkpoint_payload = checkpoint_for_current_archive(
            explicit_path=None,
            current_draws_by_wheel=all_draws_by_wheel,
            directory=root / "artifacts/coverage-checkpoints",
        )

    historical_classes = load_historical_coverage_classes(
        root / DEFAULT_HISTORICAL_SUMMARY
    )
    report = build_current_coverage_report(
        all_draws_by_wheel=all_draws_by_wheel,
        historical_classes=historical_classes,
        cutoff_date=_parse_optional_date(to_date),
        cutoff_draw_number=to_draw_number,
        checkpoint_payload=checkpoint_payload,
    )
    return current_report_to_dict(report)


def load_occurrence_payload(
    *,
    root: Path,
    database: str | Path = DEFAULT_DATABASE,
    group_size: int = 10,
    requested_draw_number: int | None = None,
) -> dict[str, Any]:
    """Build the stable grouped-occurrence contract without CLI parsing."""

    database_path = _resolve_path(root, database)
    with SQLiteLottoRepository(database_path) as repository:
        draws_by_wheel = repository.draws_by_wheel()

    draws, expected_wheels = _occurrence_input(draws_by_wheel)
    report = build_occurrence_group_report(
        draws=draws,
        expected_wheels=expected_wheels,
        group_size=group_size,
        requested_draw_number=requested_draw_number,
    )
    return occurrence_group_report_to_dict(report)


class LottoGuiApi:
    """Small pywebview-safe API returning only JSON-compatible values."""

    def __init__(
        self,
        root: Path,
        *,
        current_loader: PayloadLoader = load_current_payload,
        occurrence_loader: PayloadLoader = load_occurrence_payload,
    ) -> None:
        self._root = root
        self._current_loader = current_loader
        self._occurrence_loader = occurrence_loader

    @staticmethod
    def _success(data: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "data": data, "error": None}

    @staticmethod
    def _failure(error: Exception) -> dict[str, Any]:
        return {
            "ok": False,
            "data": None,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "ok": True,
            "data": {
                "bridge_version": 1,
                "contracts": [
                    {"schema": "lotto.current", "version": 1},
                    {"schema": "lotto.occurrence-groups", "version": 1},
                ],
                "scientific_mode": "descriptive-research",
            },
            "error": None,
        }

    def get_current(
        self,
        database: str = str(DEFAULT_DATABASE),
        to_draw_number: int | None = None,
        to_date: str | None = None,
        use_checkpoint: bool = True,
    ) -> dict[str, Any]:
        try:
            payload = self._current_loader(
                root=self._root,
                database=database,
                to_draw_number=to_draw_number,
                to_date=to_date,
                use_checkpoint=use_checkpoint,
            )
            return self._success(payload)
        except Exception as error:  # pywebview boundary: convert to stable envelope
            return self._failure(error)

    def get_occurrence_groups(
        self,
        database: str = str(DEFAULT_DATABASE),
        group_size: int = 10,
        requested_draw_number: int | None = None,
    ) -> dict[str, Any]:
        try:
            payload = self._occurrence_loader(
                root=self._root,
                database=database,
                group_size=group_size,
                requested_draw_number=requested_draw_number,
            )
            return self._success(payload)
        except Exception as error:  # pywebview boundary: convert to stable envelope
            return self._failure(error)
