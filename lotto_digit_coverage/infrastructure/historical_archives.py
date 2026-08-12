"""Read-only composition helpers for historical SQLite archives."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from lotto_digit_coverage.domain.draws import DrawSnapshot
from lotto_digit_coverage.infrastructure.sqlite_lotto_repository import (
    SQLiteLottoRepository,
)
from strategies.coverage_cycle_history import merge_draws_by_wheel
from strategies.rolling_frequency import merge_draw_histories


def load_draw_collection(
    path: Path,
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """Load one archive through the canonical read-only SQLite adapter."""

    with SQLiteLottoRepository(path) as repository:
        return repository.draws_by_wheel()


def load_merged_coverage_draws(
    paths: Sequence[Path],
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """Merge archives with the chronology rules used by coverage histories."""

    if not paths:
        raise ValueError("Serve almeno un database.")
    return merge_draws_by_wheel(
        [load_draw_collection(path) for path in paths]
    )


def load_merged_rolling_draws(
    paths: Sequence[Path],
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """Merge archives with the frozen rolling-frequency protocol."""

    if not paths:
        raise ValueError("Serve almeno un database.")
    return merge_draw_histories(
        tuple(load_draw_collection(path) for path in paths)
    )
