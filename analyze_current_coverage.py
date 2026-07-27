#!/usr/bin/env python3

"""Misuratore Markov dello stato corrente delle ruote."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from strategies.coverage_completion import (
    CurrentCoverageState,
    current_coverage_state,
)
from strategies.coverage_markov import maturity_metrics
from strategies.digit_coverage import load_draws_by_wheel
from strategies.twin_digits import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")
HORIZONS = (1, 2, 3, 5)


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def maturity_sort_key(
    item: tuple[CurrentCoverageState, dict[str, object]],
) -> tuple[float, float, int]:
    state, metrics = item
    completion = metrics["completion_within"]

    return (
        metrics["expected_remaining_draws"],
        -completion[1],
        state.wheel_order,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Calcola lo stato corrente e la maturità Markov "
            "dei cicli naturali di copertura."
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
            draws_by_wheel = load_draws_by_wheel(repository)

        states = tuple(
            current_coverage_state(draws)
            for draws in draws_by_wheel.values()
        )

        unsynchronized = tuple(
            state
            for state in states
            if not state.synchronized
        )

        if unsynchronized:
            wheels = ", ".join(
                state.wheel
                for state in unsynchronized
            )

            raise RuntimeError(
                "Ciclo corrente non sincronizzato per: "
                f"{wheels}."
            )

        measured = tuple(
            (
                state,
                maturity_metrics(
                    state.missing_digits,
                    horizons=HORIZONS,
                ),
            )
            for state in states
        )

        ranked = tuple(
            sorted(
                measured,
                key=maturity_sort_key,
            )
        )

        print("===== MISURATORE MARKOV DELLA COPERTURA =====")
        print(f"Database: {args.database}")
        print(
            "Stato: cifre ancora mancanti nel ciclo naturale corrente."
        )
        print(
            "Classifica: attesa residua crescente; "
            "non rappresenta un vantaggio sul gioco."
        )
        print()
        print(
            "Pos  Ruota       Ultimo  Età  Mancanti       "
            "Entro 1  Entro 2  Entro 3  Entro 5  Attesa"
        )
        print(
            "---  ----------  ------  ---  -------------  "
            "-------  -------  -------  -------  ------"
        )

        for position, (state, metrics) in enumerate(
            ranked,
            start=1,
        ):
            completion = metrics["completion_within"]

            print(
                f"{position:<5}"
                f"{state.wheel:<12}"
                f"{state.latest_draw:<8}"
                f"{state.draws_in_cycle:<5}"
                f"{format_digits(state.missing_digits):<15}"
                f"{completion[1]:>6.2%}  "
                f"{completion[2]:>6.2%}  "
                f"{completion[3]:>6.2%}  "
                f"{completion[5]:>6.2%}  "
                f"{metrics['expected_remaining_draws']:>6.3f}"
            )

        print()
        print("===== DETTAGLIO CICLI =====")
        print()
        print(
            "Ruota       Cicli completi  Età corrente  "
            "Coperte         Mancanti"
        )
        print(
            "----------  --------------  ------------  "
            "--------------  --------------"
        )

        for state in sorted(
            states,
            key=lambda current: current.wheel_order,
        ):
            print(
                f"{state.wheel:<12}"
                f"{state.completed_cycles:<16}"
                f"{state.draws_in_cycle:<14}"
                f"{format_digits(state.covered_digits):<16}"
                f"{format_digits(state.missing_digits)}"
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
