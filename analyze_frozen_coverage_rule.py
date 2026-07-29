#!/usr/bin/env python3

"""Replica indipendente 2025 della regola di copertura congelata."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Sequence

from analyze_coverage_backtest import (
    CoverageSignal,
    collect_signals,
    theoretical_hit_probability,
)
from strategies.lotto_repository import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")
WINDOW_SIZE = 3


def poisson_binomial_upper_tail(
    probabilities: Sequence[float],
    observed_hits: int,
) -> float:
    """
    Calcola P(X >= observed_hits) per Bernoulli indipendenti
    con probabilità eventualmente differenti.
    """

    distribution = [1.0]

    for probability in probabilities:
        updated = [0.0] * (len(distribution) + 1)

        for hits, mass in enumerate(distribution):
            updated[hits] += mass * (1.0 - probability)
            updated[hits + 1] += mass * probability

        distribution = updated

    return sum(distribution[observed_hits:])


def wilson_interval(
    hits: int,
    total: int,
    z: float = 1.959963984540054,
) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0

    observed = hits / total
    denominator = 1.0 + z * z / total

    center = (
        observed
        + z * z / (2.0 * total)
    ) / denominator

    margin = (
        z
        * math.sqrt(
            observed * (1.0 - observed) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )

    return center - margin, center + margin


def summarize(
    signals: Sequence[CoverageSignal],
) -> tuple[int, int, float, float, float, float]:
    total = len(signals)
    hits = sum(signal.hit for signal in signals)

    observed_rate = hits / total if total else 0.0

    probabilities = [
        theoretical_hit_probability(signal.missing_digit)
        for signal in signals
    ]

    expected_rate = (
        sum(probabilities) / total
        if total
        else 0.0
    )

    p_value = (
        poisson_binomial_upper_tail(
            probabilities,
            hits,
        )
        if total
        else 1.0
    )

    return (
        total,
        hits,
        observed_rate,
        expected_rate,
        observed_rate - expected_rate,
        p_value,
    )


def print_main_summary(
    signals: Sequence[CoverageSignal],
) -> None:
    (
        total,
        hits,
        observed,
        expected,
        delta,
        p_value,
    ) = summarize(signals)

    lower, upper = wilson_interval(hits, total)

    first_target = min(
        signal.target_draw
        for signal in signals
    )

    last_target = max(
        signal.target_draw
        for signal in signals
    )

    print("===== REPLICA INDIPENDENTE 2025 =====")
    print(
        "Regola congelata: dopo tre estrazioni manca "
        "esattamente una cifra 0–9; verifica sulla quarta."
    )
    print()
    print(f"Database:                    {DEFAULT_DATABASE}")
    print(f"Concorsi bersaglio:          {first_target}–{last_target}")
    print(f"Segnali:                     {total}")
    print(f"Hit:                         {hits}")
    print(f"Tasso osservato:             {observed:.2%}")
    print(f"Tasso teorico ponderato:     {expected:.2%}")
    print(f"Delta osservato:             {delta:+.2%}")
    print(
        "Intervallo Wilson 95%:       "
        f"{lower:.2%} – {upper:.2%}"
    )
    print(
        "p-value teorico indipendente:"
        f" {p_value:.6f}"
    )
    print()
    print(
        "ATTENZIONE: il p-value teorico considera i segnali "
        "indipendenti; le finestre mobili si sovrappongono. "
        "Il test di permutazione sarà il controllo decisivo."
    )


def print_half_year_summary(
    signals: Sequence[CoverageSignal],
) -> None:
    print("\n===== STABILITÀ TEMPORALE =====")
    print()
    print(
        "Periodo             Segnali  Hit  Osservato  "
        "Atteso    Delta     p teorico"
    )
    print(
        "------------------  -------  ---  ---------  "
        "--------  --------  ---------"
    )

    groups = (
        (
            "Concorsi 4–104",
            tuple(
                signal
                for signal in signals
                if signal.target_draw <= 104
            ),
        ),
        (
            "Concorsi 105–208",
            tuple(
                signal
                for signal in signals
                if signal.target_draw >= 105
            ),
        ),
    )

    for label, selected in groups:
        (
            total,
            hits,
            observed,
            expected,
            delta,
            p_value,
        ) = summarize(selected)

        print(
            f"{label:<20}"
            f"{total:<9}"
            f"{hits:<5}"
            f"{observed:>8.2%}  "
            f"{expected:>7.2%}  "
            f"{delta:>+7.2%}  "
            f"{p_value:>9.6f}"
        )


def print_by_digit(
    signals: Sequence[CoverageSignal],
) -> None:
    print("\n===== RISULTATI PER CIFRA MANCANTE =====")
    print()
    print(
        "Cifra  Segnali  Hit  Osservato  Baseline   Delta"
    )
    print(
        "-----  -------  ---  ---------  ---------  --------"
    )

    for digit in range(10):
        selected = tuple(
            signal
            for signal in signals
            if signal.missing_digit == digit
        )

        if not selected:
            continue

        total = len(selected)
        hits = sum(signal.hit for signal in selected)
        observed = hits / total
        baseline = theoretical_hit_probability(digit)

        print(
            f"{digit:<7}"
            f"{total:<9}"
            f"{hits:<5}"
            f"{observed:>8.2%}  "
            f"{baseline:>8.2%}  "
            f"{observed - baseline:>+7.2%}"
        )


def print_by_wheel(
    signals: Sequence[CoverageSignal],
) -> None:
    print("\n===== RISULTATI PER RUOTA =====")
    print()
    print(
        "Ruota       Segnali  Hit  Osservato  "
        "Atteso    Delta"
    )
    print(
        "-----------  -------  ---  ---------  "
        "--------  --------"
    )

    wheels = tuple(
        dict.fromkeys(
            signal.wheel
            for signal in signals
        )
    )

    for wheel in wheels:
        selected = tuple(
            signal
            for signal in signals
            if signal.wheel == wheel
        )

        (
            total,
            hits,
            observed,
            expected,
            delta,
            _,
        ) = summarize(selected)

        print(
            f"{wheel:<12}"
            f"{total:<9}"
            f"{hits:<5}"
            f"{observed:>8.2%}  "
            f"{expected:>7.2%}  "
            f"{delta:>+7.2%}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Replica indipendente della regola congelata "
            "di copertura su un database annuale."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        with LottoRepository(args.database) as repository:
            signals = collect_signals(
                repository,
                window_sizes=(WINDOW_SIZE,),
            )

        if not signals:
            raise RuntimeError(
                "Nessun segnale trovato nel database."
            )

        print_main_summary(signals)
        print_half_year_summary(signals)
        print_by_digit(signals)
        print_by_wheel(signals)

    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
