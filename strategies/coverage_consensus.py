"""Consensus trasversale descrittivo degli stati di copertura correnti."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from strategies.coverage_completion import CurrentCoverageState


@dataclass(frozen=True)
class DigitConsensus:
    """Presenza trasversale di una cifra negli stati attivi."""

    digit: int
    missing_wheels: tuple[str, ...]
    top_wheels: tuple[str, ...]

    @property
    def missing_count(self) -> int:
        return len(self.missing_wheels)

    @property
    def top_count(self) -> int:
        return len(self.top_wheels)

    @property
    def involved_wheels(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                set(self.missing_wheels)
                | set(self.top_wheels)
            )
        )


def build_digit_consensus(
    states: Sequence[CurrentCoverageState],
) -> tuple[DigitConsensus, ...]:
    """
    Costruisce il consenso soltanto sulle ruote con ciclo attivo.

    Una ruota appena ripartita da uno stato vuoto non contribuisce:
    in quello stato tutte le cifre risultano tecnicamente mancanti e
    introdurrebbero un artefatto trasversale privo di informazione.
    """

    active = tuple(
        state
        for state in states
        if state.draws_in_cycle > 0
    )

    rows: list[DigitConsensus] = []

    for digit in range(10):
        missing_wheels = tuple(
            state.wheel
            for state in active
            if digit in state.missing_digits
        )
        top_wheels = tuple(
            state.wheel
            for state in active
            if digit in state.most_present_digits
        )

        if not missing_wheels and not top_wheels:
            continue

        rows.append(
            DigitConsensus(
                digit=digit,
                missing_wheels=missing_wheels,
                top_wheels=top_wheels,
            )
        )

    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.missing_count,
                -row.top_count,
                row.digit,
            ),
        )
    )


def _wheels(wheels: Sequence[str]) -> str:
    return ",".join(wheels) if wheels else "-"


def render_digit_consensus(
    states: Sequence[CurrentCoverageState],
) -> str:
    rows = build_digit_consensus(states)

    lines = [
        "===== CONSENSUS TRASVERSALE DELLE CIFRE =====",
        (
            "Descrittivo: conta dove ogni cifra è ancora Mancante "
            "e dove è TOP nelle sole ruote con ciclo attivo."
        ),
        (
            "Non combina cifre in numeri e non rappresenta "
            "un vantaggio sul gioco."
        ),
        "",
        (
            f"{'Cifra':<7}"
            f"{'Mancante':>10}  "
            f"{'TOP':>5}  "
            f"{'Ruote mancanti':<38}"
            "Ruote TOP"
        ),
        (
            f"{'-----':<7}"
            f"{'--------':>10}  "
            f"{'---':>5}  "
            f"{'---------------':<38}"
            "---------"
        ),
    ]

    if not rows:
        lines.append("Nessuna ruota con ciclo attivo.")
        return "\n".join(lines)

    for row in rows:
        lines.append(
            f"{row.digit:<7}"
            f"{row.missing_count:>10}  "
            f"{row.top_count:>5}  "
            f"{_wheels(row.missing_wheels):<38}"
            f"{_wheels(row.top_wheels)}"
        )

    return "\n".join(lines)
