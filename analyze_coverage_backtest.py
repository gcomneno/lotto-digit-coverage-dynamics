#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from strategies.digit_coverage import (
    count_all_digits,
    load_draws_by_wheel,
)
from strategies.twin_digits import (
    DrawSnapshot,
    LottoRepository,
    split_digits,
)


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")
DISCOVERY_MAX_DRAW = 99


@dataclass(frozen=True)
class CoverageSignal:
    wheel: str
    window_size: int
    source_draws: tuple[int, ...]
    target_draw: int
    target_date: str
    missing_digit: int
    hit: bool

    @property
    def period(self) -> str:
        return (
            "scoperta"
            if self.target_draw <= DISCOVERY_MAX_DRAW
            else "validazione"
        )


def theoretical_hit_probability(digit: int) -> float:
    """Probabilità che la cifra compaia nei 5 numeri successivi."""

    if digit not in range(10):
        raise ValueError(f"Cifra non valida: {digit}")

    numbers_containing_digit = 10 if digit == 9 else 18

    return 1.0 - (
        math.comb(
            90 - numbers_containing_digit,
            5,
        )
        / math.comb(90, 5)
    )


def draw_contains_digit(
    draw: DrawSnapshot,
    digit: int,
) -> bool:
    return any(
        digit in split_digits(number)
        for number in draw.numbers
    )


def build_signals_for_wheel(
    draws: Sequence[DrawSnapshot],
    window_size: int,
) -> tuple[CoverageSignal, ...]:
    """Crea i segnali con una cifra esattamente mancante."""

    if window_size <= 0:
        raise ValueError("window_size deve essere positivo")

    if len(draws) <= window_size:
        return ()

    wheel = draws[0].wheel

    if any(draw.wheel != wheel for draw in draws):
        raise ValueError("Le estrazioni devono appartenere alla stessa ruota")

    signals: list[CoverageSignal] = []

    for start in range(len(draws) - window_size):
        source_draws = tuple(
            draws[start:start + window_size]
        )
        target_draw = draws[start + window_size]

        digit_counts = count_all_digits(source_draws)

        missing_digits = tuple(
            digit
            for digit, count in enumerate(digit_counts)
            if count == 0
        )

        if len(missing_digits) != 1:
            continue

        missing_digit = missing_digits[0]

        signals.append(
            CoverageSignal(
                wheel=wheel,
                window_size=window_size,
                source_draws=tuple(
                    draw.draw_number
                    for draw in source_draws
                ),
                target_draw=target_draw.draw_number,
                target_date=target_draw.draw_date,
                missing_digit=missing_digit,
                hit=draw_contains_digit(
                    target_draw,
                    missing_digit,
                ),
            )
        )

    return tuple(signals)


def collect_signals(
    repository: LottoRepository,
    window_sizes: Sequence[int],
) -> tuple[CoverageSignal, ...]:
    draws_by_wheel = load_draws_by_wheel(repository)
    signals: list[CoverageSignal] = []

    for draws in draws_by_wheel.values():
        for window_size in window_sizes:
            signals.extend(
                build_signals_for_wheel(
                    draws,
                    window_size,
                )
            )

    return tuple(
        sorted(
            signals,
            key=lambda signal: (
                signal.target_draw,
                signal.wheel,
                signal.window_size,
            ),
        )
    )


def summarize(
    signals: Sequence[CoverageSignal],
) -> tuple[int, int, float, float, float]:
    total = len(signals)
    hits = sum(signal.hit for signal in signals)

    observed_rate = hits / total if total else 0.0

    expected_hits = sum(
        theoretical_hit_probability(signal.missing_digit)
        for signal in signals
    )

    expected_rate = (
        expected_hits / total
        if total
        else 0.0
    )

    delta = observed_rate - expected_rate

    return (
        total,
        hits,
        observed_rate,
        expected_rate,
        delta,
    )


def print_summary_table(
    signals: Sequence[CoverageSignal],
) -> None:
    print("===== BACKTEST CHIUSURA DELLA COPERTURA =====")
    print(
        "Segnale: una sola cifra assente dopo 2 o 3 estrazioni."
    )
    print(
        "Hit: la cifra assente compare nell'estrazione successiva "
        "della stessa ruota."
    )
    print(
        f"Split: scoperta fino al concorso {DISCOVERY_MAX_DRAW}; "
        f"validazione dal {DISCOVERY_MAX_DRAW + 1}."
    )
    print()

    print(
        "Periodo      Finestra  Segnali  Hit  Osservato  "
        "Atteso    Delta"
    )
    print(
        "-----------  --------  -------  ---  ---------  "
        "--------  --------"
    )

    periods = ("scoperta", "validazione", "totale")

    for period in periods:
        for window_size in (2, 3):
            selected = [
                signal
                for signal in signals
                if signal.window_size == window_size
                and (
                    period == "totale"
                    or signal.period == period
                )
            ]

            (
                total,
                hits,
                observed_rate,
                expected_rate,
                delta,
            ) = summarize(selected)

            print(
                f"{period:<13}"
                f"{window_size:<10}"
                f"{total:<9}"
                f"{hits:<5}"
                f"{observed_rate:>8.2%}  "
                f"{expected_rate:>7.2%}  "
                f"{delta:>+7.2%}"
            )


def print_validation_by_digit(
    signals: Sequence[CoverageSignal],
) -> None:
    validation = [
        signal
        for signal in signals
        if signal.period == "validazione"
    ]

    print("\n===== VALIDAZIONE PER CIFRA MANCANTE =====")
    print(
        "Sono mostrate soltanto le cifre che hanno prodotto segnali."
    )
    print()
    print(
        "Cifra  Segnali  Hit  Osservato  Baseline   Delta"
    )
    print(
        "-----  -------  ---  ---------  ---------  --------"
    )

    for digit in range(10):
        selected = [
            signal
            for signal in validation
            if signal.missing_digit == digit
        ]

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


def print_signal_distribution(
    signals: Sequence[CoverageSignal],
) -> None:
    print("\n===== DISTRIBUZIONE DEI SEGNALI =====")
    print()
    print("Finestra  Cifra  Segnali  Quota")
    print("--------  -----  -------  ------")

    for window_size in (2, 3):
        window_signals = [
            signal
            for signal in signals
            if signal.window_size == window_size
        ]

        for digit in range(10):
            count = sum(
                signal.missing_digit == digit
                for signal in window_signals
            )

            if count == 0:
                continue

            quota = count / len(window_signals)

            print(
                f"{window_size:<10}"
                f"{digit:<7}"
                f"{count:<9}"
                f"{quota:>6.2%}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Backtest della comparsa della cifra rimasta "
            "fuori dalla copertura."
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
                window_sizes=(2, 3),
            )

        print_summary_table(signals)
        print_validation_by_digit(signals)
        print_signal_distribution(signals)

        print(
            "\nNota: è un backtest descrittivo. Le finestre mobili "
            "si sovrappongono, quindi i segnali non sono tutti "
            "statisticamente indipendenti."
        )

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
