"""Shared terminal rendering for cross-wheel digit consensus."""

from __future__ import annotations

from collections.abc import Sequence

from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    DEFAULT_PRESENTATION_CATALOG,
)
from strategies.coverage_consensus import DigitConsensus


def _text(key: str, locale: str) -> str:
    return DEFAULT_PRESENTATION_CATALOG.resolve(key, locale).text


def _wheels(wheels: Sequence[str]) -> str:
    return ",".join(wheels) if wheels else "-"


def render_digit_consensus(
    rows: Sequence[DigitConsensus],
    *,
    locale: str = CANONICAL_LOCALE,
) -> str:
    """Render consensus rows without recomputing application/domain state."""

    lines = [
        _text("cli.consensus.title", locale),
        _text("cli.consensus.description", locale),
        _text("cli.consensus.warning", locale),
        "",
        (
            f"{_text('cli.consensus.digit', locale):<7}"
            f"{_text('cli.consensus.missing_wheels', locale):>22}  "
            f"{_text('cli.consensus.top_wheels', locale):>22}  "
            f"{_text('cli.consensus.where_missing', locale):<38}"
            f"{_text('cli.consensus.where_top', locale)}"
        ),
        (
            f"{'-----':<7}"
            f"{'---------------------':>22}  "
            f"{'---------------------':>22}  "
            f"{'---------------':<38}"
            "-----------------"
        ),
    ]

    if not rows:
        lines.append(_text("cli.consensus.empty", locale))
        return "\n".join(lines)

    for row in rows:
        lines.append(
            f"{row.digit:<7}"
            f"{row.missing_count:>22}  "
            f"{row.top_count:>22}  "
            f"{_wheels(row.missing_wheels):<38}"
            f"{_wheels(row.top_wheels)}"
        )

    return "\n".join(lines)
