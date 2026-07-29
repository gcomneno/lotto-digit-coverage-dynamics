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
from strategies.lotto_repository import (
    DrawSnapshot,
    LottoRepository,
    split_digits,
)


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")
DISCOVERY_MAX_DRAW = 99
WINDOW_SIZES = (1, 2, 3, 4)
LOTTO_NUMBERS = tuple(range(1, 91))


@dataclass(frozen=True)
class TwoMissingSignal:
    wheel: str
    window_size: int
    source_draws: tuple[int, ...]
    target_draw: int
    target_date: str
    missing_digits: tuple[int, int]
    hit_any: bool
    hit_both: bool

    @property
    def period(self) -> str:
        return (
            "scoperta"
            if self.target_draw <= DISCOVERY_MAX_DRAW
            else "validazione"
        )


def numbers_containing_digit(digit: int) -> frozenset[int]:
    if digit not in range(10):
        raise ValueError(f"Cifra non valida: {digit}")

    return frozenset(
        number
        for number in LOTTO_NUMBERS
        if digit in split_digits(number)
    )


def theoretical_pair_probabilities(
    first_digit: int,
    second_digit: int,
) -> tuple[float, float]:
    """
    Restituisce:
    - probabilità che compaia almeno una delle due cifre;
    - probabilità che compaiano entrambe.
    """

    if first_digit == second_digit:
        raise ValueError("Le due cifre devono essere distinte")

    first_numbers = numbers_containing_digit(first_digit)
    second_numbers = numbers_containing_digit(second_digit)
    union = first_numbers | second_numbers

    total_combinations = math.comb(90, 5)

    probability_first_absent = (
        math.comb(90 - len(first_numbers), 5)
        / total_combinations
    )

    probability_second_absent = (
        math.comb(90 - len(second_numbers), 5)
        / total_combinations
    )

    probability_both_absent = (
        math.comb(90 - len(union), 5)
        / total_combinations
    )

    probability_any = 1.0 - probability_both_absent

    probability_both = (
        1.0
        - probability_first_absent
        - probability_second_absent
        + probability_both_absent
    )

    return probability_any, probability_both


def digits_present_in_draw(
    draw: DrawSnapshot,
) -> frozenset[int]:
    return frozenset(
        digit
        for number in draw.numbers
        for digit in split_digits(number)
    )


def build_signals_for_wheel(
    draws: Sequence[DrawSnapshot],
    window_size: int,
) -> tuple[TwoMissingSignal, ...]:
    if window_size <= 0:
        raise ValueError("window_size deve essere positivo")

    if len(draws) <= window_size:
        return ()

    wheel = draws[0].wheel

    if any(draw.wheel != wheel for draw in draws):
        raise ValueError(
            "Le estrazioni devono appartenere alla stessa ruota"
        )

    signals: list[TwoMissingSignal] = []

    for start in range(len(draws) - window_size):
        source_draws = tuple(
            draws[start:start + window_size]
        )

        target = draws[start + window_size]
        digit_counts = count_all_digits(source_draws)

        missing_digits = tuple(
            digit
            for digit, count in enumerate(digit_counts)
            if count == 0
        )

        if len(missing_digits) != 2:
            continue

        first_digit, second_digit = missing_digits
        target_digits = digits_present_in_draw(target)

        first_hit = first_digit in target_digits
        second_hit = second_digit in target_digits

        signals.append(
            TwoMissingSignal(
                wheel=wheel,
                window_size=window_size,
                source_draws=tuple(
                    draw.draw_number
                    for draw in source_draws
                ),
                target_draw=target.draw_number,
                target_date=target.draw_date,
                missing_digits=(
                    first_digit,
                    second_digit,
                ),
                hit_any=first_hit or second_hit,
                hit_both=first_hit and second_hit,
            )
        )

    return tuple(signals)


def collect_signals(
    repository: LottoRepository,
) -> tuple[TwoMissingSignal, ...]:
    draws_by_wheel = load_draws_by_wheel(repository)
    signals: list[TwoMissingSignal] = []

    for draws in draws_by_wheel.values():
        for window_size in WINDOW_SIZES:
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
    signals: Sequence[TwoMissingSignal],
    outcome: str,
) -> tuple[int, int, float, float, float]:
    if outcome not in {"any", "both"}:
        raise ValueError(f"Esito non valido: {outcome}")

    total = len(signals)

    if outcome == "any":
        hits = sum(signal.hit_any for signal in signals)
    else:
        hits = sum(signal.hit_both for signal in signals)

    observed_rate = hits / total if total else 0.0

    expected_hits = 0.0

    for signal in signals:
        probability_any, probability_both = (
            theoretical_pair_probabilities(
                *signal.missing_digits,
            )
        )

        expected_hits += (
            probability_any
            if outcome == "any"
            else probability_both
        )

    expected_rate = (
        expected_hits / total
        if total
        else 0.0
    )

    return (
        total,
        hits,
        observed_rate,
        expected_rate,
        observed_rate - expected_rate,
    )


def print_summary(
    signals: Sequence[TwoMissingSignal],
    outcome: str,
    title: str,
) -> None:
    print(f"\n===== {title} =====")
    print()
    print(
        "Periodo      Finestra  Segnali  Hit  Osservato  "
        "Atteso    Delta"
    )
    print(
        "-----------  --------  -------  ---  ---------  "
        "--------  --------"
    )

    for period in ("scoperta", "validazione", "totale"):
        for window_size in WINDOW_SIZES:
            selected = tuple(
                signal
                for signal in signals
                if signal.window_size == window_size
                and (
                    period == "totale"
                    or signal.period == period
                )
            )

            (
                total,
                hits,
                observed,
                expected,
                delta,
            ) = summarize(selected, outcome)

            print(
                f"{period:<13}"
                f"{window_size:<10}"
                f"{total:<9}"
                f"{hits:<5}"
                f"{observed:>8.2%}  "
                f"{expected:>7.2%}  "
                f"{delta:>+7.2%}"
            )


def print_validation_pairs(
    signals: Sequence[TwoMissingSignal],
) -> None:
    validation = tuple(
        signal
        for signal in signals
        if signal.period == "validazione"
    )

    pairs = sorted(
        {
            signal.missing_digits
            for signal in validation
        }
    )

    print("\n===== VALIDAZIONE PER COPPIA MANCANTE =====")
    print()
    print(
        "Coppia  Segnali  Almeno una  Atteso    "
        "Entrambe  Atteso"
    )
    print(
        "------  -------  ----------  --------  "
        "--------  --------"
    )

    for pair in pairs:
        selected = tuple(
            signal
            for signal in validation
            if signal.missing_digits == pair
        )

        total = len(selected)
        any_hits = sum(
            signal.hit_any
            for signal in selected
        )
        both_hits = sum(
            signal.hit_both
            for signal in selected
        )

        probability_any, probability_both = (
            theoretical_pair_probabilities(*pair)
        )

        print(
            f"{pair[0]}-{pair[1]:<5}"
            f"{total:<9}"
            f"{any_hits:>3}/{total:<5}"
            f"{probability_any:>8.2%}  "
            f"{both_hits:>3}/{total:<3}"
            f"{probability_both:>9.2%}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Backtest delle finestre con esattamente "
            "due cifre mancanti."
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
            signals = collect_signals(repository)

        print("===== BACKTEST: DUE CIFRE MANCANTI =====")
        print(
            "Segnale: esattamente due cifre assenti dopo "
            "1, 2, 3 o 4 estrazioni."
        )
        print(
            "Verifica: estrazione immediatamente successiva "
            "della stessa ruota."
        )
        print(
            f"Split: scoperta fino al concorso "
            f"{DISCOVERY_MAX_DRAW}; validazione dal "
            f"{DISCOVERY_MAX_DRAW + 1}."
        )

        print_summary(
            signals,
            outcome="any",
            title="COMPARE ALMENO UNA DELLE DUE",
        )

        print_summary(
            signals,
            outcome="both",
            title="COMPAIONO ENTRAMBE: COPERTURA COMPLETA",
        )

        print_validation_pairs(signals)

        print(
            "\nNota: una percentuale osservata alta non basta. "
            "Conta il delta rispetto all'attesa teorica specifica "
            "della coppia."
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
