#!/usr/bin/env python3

"""Genera il checkpoint storico dinamico della copertura."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Sequence

from strategies.coverage_checkpoint import (
    apply_draws,
    checkpoint_payload,
    discover_archive_segments,
    freeze_state,
    load_draws,
    previous_complete_year,
    resolve_archive_chain,
    write_checkpoint,
)


DEFAULT_DATA_DIRECTORY = Path("data")
DEFAULT_ARTIFACT_DIRECTORY = Path(
    "artifacts/coverage-checkpoints"
)
FIRST_HISTORICAL_YEAR = 1871


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ricostruisce una sola volta i cicli storici "
            "fino all'ultimo anno completo e salva uno "
            "stato riprendibile per l'anno corrente."
        )
    )

    parser.add_argument(
        "--current-year",
        type=int,
        default=date.today().year,
        metavar="YYYY",
        help=(
            "Anno considerato corrente "
            "(predefinito: anno di sistema)."
        ),
    )

    parser.add_argument(
        "--data-directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY,
        help="Directory contenente i database Lotto.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Percorso JSON esplicito. In assenza viene "
            "usato artifacts/coverage-checkpoints/ con "
            "la data reale dell'ultima estrazione."
        ),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    checkpoint_year = previous_complete_year(
        arguments.current_year
    )

    segments = discover_archive_segments(
        arguments.data_directory
    )

    chain = resolve_archive_chain(
        segments,
        first_year=FIRST_HISTORICAL_YEAR,
        last_year=checkpoint_year,
    )

    print("===== CHECKPOINT STORICO DINAMICO =====")
    print(
        f"Anno corrente:   {arguments.current_year}"
    )
    print(
        f"Anno checkpoint: {checkpoint_year}"
    )
    print("Archivi concatenati:")

    states = {}
    total_draws = 0
    checkpoint_date = ""

    for segment in chain:
        print(
            f"  {segment.first_year}–"
            f"{segment.last_year}: {segment.path}"
        )

        draws = load_draws(segment.path)
        apply_draws(states, draws)

        total_draws += len(draws)

        if draws:
            checkpoint_date = max(
                checkpoint_date,
                max(
                    draw.draw_date
                    for draw in draws
                ),
            )

    if not checkpoint_date:
        parser.error(
            "Gli archivi selezionati non contengono estrazioni."
        )

    wheels = tuple(
        freeze_state(state)
        for state in states.values()
    )

    payload = checkpoint_payload(
        current_year=arguments.current_year,
        checkpoint_year=checkpoint_year,
        checkpoint_date=checkpoint_date,
        chain=chain,
        states=wheels,
        total_draws=total_draws,
    )

    destination = (
        arguments.output
        if arguments.output is not None
        else (
            DEFAULT_ARTIFACT_DIRECTORY
            / f"coverage-state-{checkpoint_date}.json"
        )
    )

    write_checkpoint(
        payload,
        destination,
    )

    print()
    print("===== RISULTATO =====")
    print(f"Data checkpoint: {checkpoint_date}")
    print(f"Ruote:          {len(wheels)}")
    print(f"Snapshot ruota: {total_draws}")
    print(f"Output:         {destination}")

    print()
    print("===== STATO PER RUOTA =====")

    for wheel in sorted(
        wheels,
        key=lambda item: (
            item.wheel_order,
            item.wheel,
        ),
    ):
        missing = ",".join(
            str(digit)
            for digit in wheel.missing_digits
        )

        print(
            f"{wheel.wheel:<14} "
            f"ultimo={wheel.latest_date} "
            f"ciclo={wheel.draws_in_cycle:<3} "
            f"mancanti={{{missing}}}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
