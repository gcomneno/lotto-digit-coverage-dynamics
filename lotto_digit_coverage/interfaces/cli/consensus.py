"""Shared terminal rendering for cross-wheel digit consensus."""

from __future__ import annotations

from collections.abc import Sequence

from strategies.coverage_consensus import DigitConsensus


def _wheels(wheels: Sequence[str]) -> str:
    return ",".join(wheels) if wheels else "-"


def render_digit_consensus(rows: Sequence[DigitConsensus]) -> str:
    """Render consensus rows without recomputing application/domain state."""

    lines = [
        "===== CONSENSUS TRASVERSALE DELLE CIFRE =====",
        (
            "Descrittivo: per ogni cifra conta in quante ruote con ciclo attivo "
            "è ancora assente e in quante è tra le più presenti nel ciclo corrente."
        ),
        (
            "Non combina cifre in numeri e non rappresenta "
            "un vantaggio sul gioco."
        ),
        "",
        (
            f"{'Cifra':<7}"
            f"{'Ruote in deficit':>17}  "
            f"{'Ruote in predominanza':>22}  "
            f"{'Dove in deficit':<38}"
            "Dove predominante"
        ),
        (
            f"{'-----':<7}"
            f"{'----------------':>17}  "
            f"{'---------------------':>22}  "
            f"{'---------------':<38}"
            "-----------------"
        ),
    ]

    if not rows:
        lines.append("Nessuna ruota con ciclo attivo.")
        return "\n".join(lines)

    for row in rows:
        lines.append(
            f"{row.digit:<7}"
            f"{row.missing_count:>17}  "
            f"{row.top_count:>22}  "
            f"{_wheels(row.missing_wheels):<38}"
            f"{_wheels(row.top_wheels)}"
        )

    return "\n".join(lines)
