#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from strategies.lotto_repository import format_number
from strategies.twin_digits import (
    LottoRepository,
    TwinAnalysis,
    analyze_latest,
    rank_digit_by_presence,
)


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")


def format_draw_numbers(numbers: tuple[int, ...]) -> str:
    return " ".join(format_number(number) for number in numbers)


def print_window_table(analysis: TwinAnalysis) -> None:
    event = analysis.event

    print(
        f"\nRuota {event.wheel} — gemello "
        f"{format_number(event.twin_number)} "
        f"in posizione {event.position}"
    )
    print(
        f"Cifra ricercata: {event.digit} | "
        f"Concorso n. {event.draw_number} "
        f"del {event.draw_date}"
    )

    for window in analysis.windows:
        completion = (
            ""
            if window.is_complete
            else " — finestra incompleta"
        )

        print(
            f"\n-{window.window_size}"
            f"{completion}"
        )
        print()
        print("Cfr.  Pr.")
        print("====  ===")

        ranking = sorted(
            (
                (digit, window.digit_counts[digit])
                for digit in range(1, 9)
            ),
            key=lambda item: (-item[1], item[0]),
        )

        for digit, presence in ranking:
            marker = (
                "  <-- cifra del gemello"
                if digit == event.digit
                else ""
            )

            print(
                f"{digit:<5} {presence:<3}{marker}"
            )

        print(
            f"Totale posti-cifra analizzati: "
            f"{window.digit_slots}"
        )

    print("\nDettaglio delle estrazioni precedenti:")

    longest_window = analysis.windows[-1]

    if not longest_window.draws:
        print("  Nessuna estrazione precedente disponibile.")
        return

    for index, draw in enumerate(
        longest_window.draws,
        start=1,
    ):
        print(
            f"  -{index}: n. {draw.draw_number} "
            f"del {draw.draw_date} | "
            f"{format_draw_numbers(draw.numbers)}"
        )



def print_rank_summary(
    analyses: tuple[TwinAnalysis, ...],
) -> None:
    """Mostra la posizione media della cifra di ogni gemello."""

    if not analyses:
        return

    window_count = len(analyses[0].windows)

    print(
        "\n===== POSIZIONE DELLA CIFRA GEMELLO ====="
    )
    print(
        "Rango medio nei pari merito: "
        "1,00 = più presente; 8,00 = meno presente."
    )
    print()

    header = f"{'Evento':<20}"

    for window_size in range(1, window_count + 1):
        header += f"{f'-{window_size}':>8}"

    header += f"{'Media':>10}"

    print(header)
    print("=" * len(header))

    ranks_by_window: list[list[float]] = [
        []
        for _ in range(window_count)
    ]
    all_ranks: list[float] = []

    for analysis in analyses:
        event = analysis.event
        event_ranks: list[float] = []

        for index, window in enumerate(analysis.windows):
            rank = rank_digit_by_presence(
                window.digit_counts,
                event.digit,
            )

            event_ranks.append(rank)
            ranks_by_window[index].append(rank)
            all_ranks.append(rank)

        event_average = sum(event_ranks) / len(event_ranks)
        event_label = (
            f"{event.wheel} "
            f"{format_number(event.twin_number)}"
        )

        row = f"{event_label:<20}"

        for rank in event_ranks:
            row += f"{rank:>8.2f}"

        row += f"{event_average:>10.2f}"
        print(row)

    print("-" * len(header))

    average_row = f"{'Media per finestra':<20}"

    for ranks in ranks_by_window:
        average = sum(ranks) / len(ranks)
        average_row += f"{average:>8.2f}"

    overall_average = sum(all_ranks) / len(all_ranks)
    average_row += f"{overall_average:>10.2f}"

    print(average_row)

    print(
        f"\nMedia complessiva: "
        f"{overall_average:.2f} su 8"
    )


def print_latest(analyses: tuple[TwinAnalysis, ...]) -> None:
    print("===== STRATEGIA GEMELLI — ULTIMA ESTRAZIONE =====")

    if not analyses:
        print(
            "Nessun numero gemello presente "
            "nell'ultima estrazione."
        )
        return

    first_event = analyses[0].event

    print(
        f"Concorso analizzato: n. {first_event.draw_number} "
        f"del {first_event.draw_date}"
    )
    print(f"Eventi gemelli trovati: {len(analyses)}")

    window_mode = analyses[0].windows[0].window_mode
    mode_label = (
        "cumulativa"
        if window_mode == "cumulative"
        else "singola/non cumulativa"
    )

    print(f"Modalità finestre: {mode_label}")

    for analysis in analyses:
        print_window_table(analysis)

    print_rank_summary(analyses)

    print(
        "\nNota: i conteggi descrivono il passato. "
        "Non dimostrano che l'assenza precedente della cifra "
        "aumenti la probabilità della successiva estrazione."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analizza strategie descrittive sulle estrazioni "
            "del Lotto."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=(
            "Percorso del database SQLite "
            f"(predefinito: {DEFAULT_DATABASE})"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="strategy",
        required=True,
    )

    twins = subparsers.add_parser(
        "twins",
        help="Analisi delle cifre dei numeri gemelli.",
    )

    twins_subparsers = twins.add_subparsers(
        dest="mode",
        required=True,
    )

    latest_parser = twins_subparsers.add_parser(
        "latest",
        help=(
            "Analizza ogni gemello dell'ultima estrazione, "
            "uno alla volta e sulla stessa ruota."
        ),
    )

    latest_parser.add_argument(
        "--lookback",
        type=int,
        default=6,
        help=(
            "Numero massimo di estrazioni precedenti "
            "da analizzare (predefinito: 6)."
        ),
    )

    latest_parser.add_argument(
        "--window-mode",
        choices=("cumulative", "single"),
        default="cumulative",
        help=(
            "cumulative: -N comprende tutte le estrazioni "
            "da -1 a -N; single: -N considera soltanto "
            "l'ennesima estrazione precedente "
            "(predefinito: cumulative)."
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.lookback <= 0:
        parser.error("--lookback deve essere maggiore di zero")

    try:
        with LottoRepository(args.database) as repository:
            analyses = analyze_latest(
                repository,
                lookback=args.lookback,
                window_mode=args.window_mode,
            )
            print_latest(analyses)

    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
        sqlite3.Error,
    ) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    import sqlite3

    raise SystemExit(main())
