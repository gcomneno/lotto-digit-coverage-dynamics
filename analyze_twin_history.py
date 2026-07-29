#!/usr/bin/env python3

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

from strategies.twin_digits import (
    LottoRepository,
    TWIN_NUMBERS,
    TwinEvent,
    analyze_event_windows,
    rank_digit_by_presence,
)


DEFAULT_DATABASE = Path("data/lotto-2026.sqlite3")


def load_all_twin_events(
    repository: LottoRepository,
) -> tuple[TwinEvent, ...]:
    twins = sorted(TWIN_NUMBERS)
    placeholders = ",".join("?" for _ in twins)

    rows = repository.connection.execute(
        f"""
        SELECT
            draw_number,
            draw_date,
            wheel,
            wheel_order,
            position,
            value
        FROM v_draw_numbers
        WHERE value IN ({placeholders})
        ORDER BY
            draw_date,
            draw_number,
            wheel_order,
            position
        """,
        twins,
    ).fetchall()

    return tuple(
        TwinEvent(
            draw_number=int(row["draw_number"]),
            draw_date=str(row["draw_date"]),
            wheel=str(row["wheel"]),
            wheel_order=int(row["wheel_order"]),
            position=int(row["position"]),
            twin_number=int(row["value"]),
        )
        for row in rows
    )


def analyze_history(
    repository: LottoRepository,
    lookback: int,
    window_mode: str,
) -> tuple[list[list[float]], int, int]:
    ranks_by_window: list[list[float]] = [
        []
        for _ in range(lookback)
    ]

    analyzed_events = 0
    skipped_events = 0

    for event in load_all_twin_events(repository):
        previous_draws = repository.previous_draws_for_event(
            event,
            limit=lookback,
        )

        # Confrontiamo soltanto eventi con storia completa.
        if len(previous_draws) != lookback:
            skipped_events += 1
            continue

        if any(
            draw.wheel != event.wheel
            for draw in previous_draws
        ):
            raise RuntimeError(
                f"Contaminazione tra ruote per "
                f"{event.wheel} {event.twin_number} "
                f"nel concorso {event.draw_number}."
            )

        analysis = analyze_event_windows(
            event,
            previous_draws,
            lookback=lookback,
            window_mode=window_mode,
        )

        for index, window in enumerate(analysis.windows):
            if not window.is_complete:
                raise RuntimeError(
                    f"Finestra -{index + 1} incompleta "
                    f"per il concorso {event.draw_number}."
                )

            rank = rank_digit_by_presence(
                window.digit_counts,
                event.digit,
            )

            ranks_by_window[index].append(rank)

        analyzed_events += 1

    return ranks_by_window, analyzed_events, skipped_events


def print_report(
    ranks_by_window: list[list[float]],
    analyzed_events: int,
    skipped_events: int,
    window_mode: str,
) -> None:
    mode_label = (
        "cumulativa"
        if window_mode == "cumulative"
        else "singola/non cumulativa"
    )

    print("===== ANALISI STORICA DEI GEMELLI =====")
    print(f"Modalità:                  {mode_label}")
    print(f"Eventi completi analizzati: {analyzed_events}")
    print(f"Eventi iniziali esclusi:    {skipped_events}")
    print("Riferimento neutro:         4.50")
    print()

    print(
        "Finestra  Eventi  Media rango  Mediana  Minimo  Massimo"
    )
    print(
        "--------  ------  -----------  -------  ------  -------"
    )

    all_ranks: list[float] = []

    for index, ranks in enumerate(
        ranks_by_window,
        start=1,
    ):
        if not ranks:
            print(
                f"-{index:<8}0       n/d          "
                "n/d      n/d     n/d"
            )
            continue

        all_ranks.extend(ranks)

        print(
            f"-{index:<8}"
            f"{len(ranks):<8}"
            f"{statistics.mean(ranks):<13.2f}"
            f"{statistics.median(ranks):<9.2f}"
            f"{min(ranks):<8.2f}"
            f"{max(ranks):.2f}"
        )

    print()

    if all_ranks:
        overall_mean = statistics.mean(all_ranks)
        overall_median = statistics.median(all_ranks)

        print(
            f"Media complessiva:          "
            f"{overall_mean:.2f} su 8"
        )
        print(
            f"Mediana complessiva:        "
            f"{overall_median:.2f} su 8"
        )
        print(
            f"Scostamento dal neutro:     "
            f"{overall_mean - 4.50:+.2f}"
        )

    print(
        "\nInterpretazione: valori sotto 4.50 indicano una "
        "cifra relativamente presente; valori sopra 4.50 "
        "una cifra relativamente poco presente."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analizza storicamente i ranghi delle cifre "
            "che generano numeri gemelli."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )

    parser.add_argument(
        "--lookback",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--window-mode",
        choices=("cumulative", "single"),
        required=True,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.lookback <= 0:
        print(
            "ERRORE: --lookback deve essere positivo.",
            file=sys.stderr,
        )
        return 1

    try:
        with LottoRepository(args.database) as repository:
            (
                ranks_by_window,
                analyzed_events,
                skipped_events,
            ) = analyze_history(
                repository,
                lookback=args.lookback,
                window_mode=args.window_mode,
            )

        print_report(
            ranks_by_window,
            analyzed_events,
            skipped_events,
            args.window_mode,
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
