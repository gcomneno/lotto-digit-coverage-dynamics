#!/usr/bin/env python3

"""Quadro corrente Markov e anomalie della copertura."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from analyze_coverage_anomalies import (
    ALL_CATEGORIES,
    AnomalyEvent,
    build_all_transitions,
    detect_anomalies,
)
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
    item: tuple[
        CurrentCoverageState,
        dict[str, object],
    ],
) -> tuple[float, float, int]:
    state, metrics = item
    completion = metrics["completion_within"]

    return (
        metrics["expected_remaining_draws"],
        -completion[1],
        state.wheel_order,
    )


def latest_target(
    states: Sequence[CurrentCoverageState],
) -> tuple[int, str]:
    targets = {
        (
            state.latest_draw,
            state.latest_date,
        )
        for state in states
    }

    if not targets:
        raise RuntimeError(
            "Nessuno stato corrente disponibile."
        )

    if len(targets) != 1:
        details = ", ".join(
            f"{draw}/{date}"
            for draw, date in sorted(targets)
        )

        raise RuntimeError(
            "Le ruote non terminano sulla stessa "
            f"estrazione: {details}."
        )

    return next(iter(targets))


def active_anomalies(
    events: Sequence[AnomalyEvent],
    *,
    latest_draw: int,
    latest_date: str,
) -> tuple[AnomalyEvent, ...]:
    """
    Seleziona le anomalie ancora rilevanti all'ultimo target.

    A1 resta attiva finché il ciclo finale è censurato a destra.
    A2, A3 e A4 sono eventi istantanei e sono correnti soltanto
    quando coincidono con l'ultima estrazione disponibile.
    """

    selected = [
        event
        for event in events
        if (
            event.category == "A1"
            and event.right_censored
        )
        or (
            event.category in {
                "A2",
                "A3",
                "A4",
            }
            and event.target_draw == latest_draw
            and event.target_date == latest_date
        )
    ]

    return tuple(
        sorted(
            selected,
            key=lambda event: (
                event.category,
                event.wheel_order,
                event.target_date,
                event.target_draw,
            ),
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Calcola lo stato corrente, la maturità Markov "
            "e le anomalie A1-A4 dei cicli naturali "
            "di copertura."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )

    return parser


def print_markov_summary(
    states: Sequence[CurrentCoverageState],
) -> None:
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
    print(
        "Stato: cifre ancora mancanti "
        "nel ciclo naturale corrente."
    )
    print(
        "Classifica: attesa residua crescente; "
        "non rappresenta un vantaggio sul gioco."
    )
    print(
        "Più presenti: cifre con il massimo numero "
        "di occorrenze nel ciclo corrente."
    )
    print()
    print(
        f"{'Pos':<5}"
        f"{'Ruota':<12}"
        f"{'Ultimo':<8}"
        f"{'Età':<5}"
        f"{'Più presenti':<23}"
        f"{'Mancanti':<23}"
        "Entro 1  Entro 2  Entro 3  Entro 5  Attesa"
    )
    print(
        f"{'---':<5}"
        f"{'----------':<12}"
        f"{'------':<8}"
        f"{'---':<5}"
        f"{'-------------':<23}"
        f"{'-------------':<23}"
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
            f"{format_digits(state.most_present_digits):<23}"
            f"{format_digits(state.missing_digits):<23}"
            f"{completion[1]:>6.2%}  "
            f"{completion[2]:>6.2%}  "
            f"{completion[3]:>6.2%}  "
            f"{completion[5]:>6.2%}  "
            f"{metrics['expected_remaining_draws']:>6.3f}"
        )


def print_cycle_details(
    states: Sequence[CurrentCoverageState],
) -> None:
    print()
    print("===== DETTAGLIO CICLI =====")
    print()
    print(
        "Ruota       Cicli completi  Età corrente  Mancanti"
    )
    print(
        "----------  --------------  ------------  "
        "---------------------"
    )

    for state in sorted(
        states,
        key=lambda current: current.wheel_order,
    ):
        print(
            f"{state.wheel:<12}"
            f"{state.completed_cycles:<16}"
            f"{state.draws_in_cycle:<14}"
            f"{format_digits(state.missing_digits)}"
        )


def print_anomaly_history(
    events: Sequence[AnomalyEvent],
    *,
    transition_count: int,
) -> None:
    counts = Counter(
        event.category
        for event in events
    )

    print()
    print("===== ANOMALIE A1-A4 NEL DATABASE =====")
    print(f"Transizioni valide: {transition_count}")
    print(f"Eventi osservati:   {len(events)}")
    print(
        "Categorie:         "
        + ", ".join(
            f"{category}={counts.get(category, 0)}"
            for category in ALL_CATEGORIES
        )
    )

    if not events:
        print()
        print("Nessuna anomalia storica rilevata.")
        return

    print()
    print(
        "Cat Data       Estr. Ruota       "
        "P(evento)  Livello   Firma"
    )
    print(
        "--- ---------- ----- ----------- "
        "---------- --------  ----------------"
    )

    for event in events:
        print(
            f"{event.category:<3} "
            f"{event.target_date:<10} "
            f"{event.target_draw:<5} "
            f"{event.wheel:<11} "
            f"{event.conditional_probability:>10.6%} "
            f"{event.severity:<8}  "
            f"{event.signature}"
        )


def print_active_anomalies(
    events: Sequence[AnomalyEvent],
    *,
    latest_draw: int,
    latest_date: str,
) -> None:
    active = active_anomalies(
        events,
        latest_draw=latest_draw,
        latest_date=latest_date,
    )

    print()
    print(
        "===== ANOMALIE ATTIVE "
        f"ALLA {latest_draw} ({latest_date}) ====="
    )

    if not active:
        print(
            "Nessuna anomalia A1-A4 attiva."
        )
        return

    print()
    print(
        "Cat Ruota       P(evento)  "
        "Attiva/osservata da       Firma"
    )
    print(
        "--- ----------- ---------- "
        "-------------------------  ----------------"
    )

    for event in active:
        if event.category == "A1":
            timing = (
                f"{event.target_draw} "
                f"({event.target_date})"
            )
        else:
            timing = (
                f"{latest_draw} "
                f"({latest_date})"
            )

        print(
            f"{event.category:<3} "
            f"{event.wheel:<11} "
            f"{event.conditional_probability:>10.6%} "
            f"{timing:<25}  "
            f"{event.signature}"
        )


def main() -> int:
    args = build_parser().parse_args()

    try:
        with LottoRepository(args.database) as repository:
            draws_by_wheel = load_draws_by_wheel(
                repository
            )

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

        latest_draw, latest_date = latest_target(
            states
        )

        transitions = build_all_transitions(
            draws_by_wheel
        )
        events = detect_anomalies(
            transitions
        )

        print(f"Database: {args.database}")
        print(
            f"Ultima estrazione: {latest_draw} "
            f"del {latest_date}"
        )
        print()

        print_markov_summary(states)
        print_cycle_details(states)
        print_anomaly_history(
            events,
            transition_count=len(transitions),
        )
        print_active_anomalies(
            events,
            latest_draw=latest_draw,
            latest_date=latest_date,
        )

    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
