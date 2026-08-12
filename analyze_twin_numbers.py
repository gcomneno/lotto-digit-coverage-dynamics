#!/usr/bin/env python3

"""Valutazione storica one-step dei numeri gemelli 11–88."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from strategies.digit_coverage import load_draws_by_wheel
from strategies.lotto_repository import LottoRepository
from strategies.twin_numbers import (
    MIN_CANDIDATE_CASES,
    NULL_TWIN_PROBABILITY,
    TwinObservation,
    TwinStatisticsRow,
    build_all_twin_observations,
    build_twin_statistics,
)


DEFAULT_DATABASE = Path("data/lotto-1871-2025.sqlite3")
DEFAULT_CSV_OUTPUT = Path("_work/twin-number-statistics.csv")
DEFAULT_JSON_OUTPUT = Path("_work/twin-number-statistics.json")


def parse_iso_date(value: str) -> str:
    from datetime import date

    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "La data deve usare il formato YYYY-MM-DD."
        ) from error

    if parsed.isoformat() != value:
        raise argparse.ArgumentTypeError(
            "La data deve usare il formato YYYY-MM-DD."
        )

    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta la frequenza one-step dei gemelli 11–88 "
            "con il null esatto 1/18, condizionando soltanto su "
            "informazioni disponibili prima dell'estrazione target."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=(
            "Database SQLite da analizzare "
            f"(default: {DEFAULT_DATABASE})."
        ),
    )
    parser.add_argument(
        "--wheel",
        action="append",
        default=[],
        help=(
            "Limita l'analisi a una ruota. Ripetibile. "
            "Senza opzione usa tutte le ruote disponibili."
        ),
    )
    parser.add_argument(
        "--from-date",
        type=parse_iso_date,
        help="Prima data target inclusa (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--to-date",
        type=parse_iso_date,
        help="Ultima data target inclusa (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_OUTPUT,
        help=f"Output CSV (default: {DEFAULT_CSV_OUTPUT}).",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help=f"Output JSON (default: {DEFAULT_JSON_OUTPUT}).",
    )
    parser.add_argument(
        "--only-candidates",
        action="store_true",
        help="Mostra in tabella soltanto le righe candidate.",
    )
    return parser


def filter_observations(
    observations: Sequence[TwinObservation],
    *,
    wheels: Sequence[str] = (),
    from_date: str | None = None,
    to_date: str | None = None,
) -> tuple[TwinObservation, ...]:
    selected_wheels = {
        wheel.casefold()
        for wheel in wheels
    }

    if from_date and to_date and from_date > to_date:
        raise ValueError("--from-date non può superare --to-date.")

    return tuple(
        observation
        for observation in observations
        if (
            not selected_wheels
            or observation.wheel.casefold() in selected_wheels
        )
        and (
            from_date is None
            or observation.target_date >= from_date
        )
        and (
            to_date is None
            or observation.target_date <= to_date
        )
    )


def validate_wheels(
    requested: Sequence[str],
    available: Sequence[str],
) -> None:
    known = {
        wheel.casefold(): wheel
        for wheel in available
    }
    unknown = [
        wheel
        for wheel in requested
        if wheel.casefold() not in known
    ]

    if unknown:
        raise ValueError(
            "Ruote sconosciute: " + ", ".join(unknown)
            + ". Disponibili: " + ", ".join(available) + "."
        )


def format_percent(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def render_rows(
    rows: Sequence[TwinStatisticsRow],
    *,
    only_candidates: bool = False,
) -> str:
    selected = tuple(
        row
        for row in rows
        if not only_candidates or row.candidate
    )

    lines = [
        (
            f"{'Condizione':<20}"
            f"{'Gem':>4} "
            f"{'Casi':>7} "
            f"{'Hit':>6} "
            f"{'Attesi':>8} "
            f"{'Oss.':>8} "
            f"{'Lift':>8} "
            f"{'CI95':>19} "
            f"{'q':>9} "
            "Esito"
        ),
        (
            f"{'----------':<20}"
            f"{'---':>4} "
            f"{'----':>7} "
            f"{'---':>6} "
            f"{'------':>8} "
            f"{'----':>8} "
            f"{'----':>8} "
            f"{'----':>19} "
            f"{'-':>9} "
            "-----"
        ),
    ]

    if not selected:
        lines.append("Nessuna riga da mostrare.")
        return "\n".join(lines)

    for row in selected:
        q_display = (
            "-"
            if row.condition == "baseline"
            else f"{row.q_value:.4g}"
        )
        outcome = "CANDIDATO" if row.candidate else "-"
        interval = (
            f"[{format_percent(row.wilson_low)},"
            f"{format_percent(row.wilson_high)}]"
        )

        lines.append(
            f"{row.condition:<20}"
            f"{row.twin_number:>4} "
            f"{row.cases:>7} "
            f"{row.hits:>6} "
            f"{row.expected_hits:>8.2f} "
            f"{format_percent(row.observed_probability):>8} "
            f"{format_percent(row.lift_probability):>8} "
            f"{interval:>19} "
            f"{q_display:>9} "
            f"{outcome}"
        )

    return "\n".join(lines)


def write_csv(rows: Sequence[TwinStatisticsRow], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    documents = [asdict(row) for row in rows]

    if not documents:
        output.write_text("", encoding="utf-8")
        return

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(documents[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(documents)


def write_json(
    rows: Sequence[TwinStatisticsRow],
    observations: Sequence[TwinObservation],
    *,
    database: Path,
    wheels: Sequence[str],
    from_date: str | None,
    to_date: str | None,
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    dates = [observation.target_date for observation in observations]
    candidates = [row for row in rows if row.candidate]

    document = {
        "report_format_version": 1,
        "report_type": "twin-number-one-step-screen",
        "database": str(database),
        "null_probability": NULL_TWIN_PROBABILITY,
        "null_interpretation": (
            "For one fixed twin number on one fixed wheel, five "
            "numbers are drawn without replacement from 1..90; "
            "therefore P(hit)=5/90=1/18."
        ),
        "requested_wheels": list(wheels),
        "from_date": from_date,
        "to_date": to_date,
        "first_target_date": min(dates) if dates else None,
        "last_target_date": max(dates) if dates else None,
        "observation_count": len(observations),
        "candidate_rule": {
            "minimum_cases": MIN_CANDIDATE_CASES,
            "bh_q_below": 0.05,
            "wilson_95_excludes_null": True,
        },
        "interpretation": (
            "Exploratory screen only. Conditions are defined from "
            "the state available before each target draw. Pooled "
            "wheels share the draw calendar and are not treated as "
            "independent replications. A candidate is not a validated "
            "predictive trigger and requires chronological out-of-sample "
            "or forward validation."
        ),
        "candidate_count": len(candidates),
        "rows": [asdict(row) for row in rows],
    }

    output.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.database.is_file():
        parser.error(f"Database non trovato: {args.database}")

    try:
        with LottoRepository(args.database) as repository:
            draws_by_wheel = load_draws_by_wheel(repository)

        available_wheels = tuple(draws_by_wheel)
        validate_wheels(args.wheel, available_wheels)

        observations = build_all_twin_observations(draws_by_wheel)
        observations = filter_observations(
            observations,
            wheels=args.wheel,
            from_date=args.from_date,
            to_date=args.to_date,
        )

        if not observations:
            raise RuntimeError(
                "Nessuna osservazione one-step disponibile "
                "con i filtri richiesti."
            )

        rows = build_twin_statistics(observations)
        write_csv(rows, args.csv)
        write_json(
            rows,
            observations,
            database=args.database,
            wheels=args.wheel,
            from_date=args.from_date,
            to_date=args.to_date,
            output=args.json,
        )
    except (RuntimeError, ValueError) as error:
        parser.error(str(error))

    dates = [observation.target_date for observation in observations]
    candidates = tuple(row for row in rows if row.candidate)

    print("===== LABORATORIO STATISTICO NUMERI GEMELLI =====")
    print("Gemelli analizzati: 11 22 33 44 55 66 77 88")
    print(
        "Null per singolo gemello/ruota: "
        f"1/18 = {format_percent(NULL_TWIN_PROBABILITY)}."
    )
    print(
        "Stato e condizioni sono fotografati prima "
        "dell'estrazione target."
    )
    print(
        "Screen esplorativo: q Benjamini-Hochberg < 0,05, "
        f"almeno {MIN_CANDIDATE_CASES} casi e CI95 Wilson "
        "che esclude il null."
    )
    print(
        "Un candidato non è un trigger validato: serve una "
        "verifica cronologica out-of-sample o forward."
    )
    print()
    print(f"Database:      {args.database}")
    print(f"Periodo target: {min(dates)} – {max(dates)}")
    print(
        "Ruote:         "
        + (", ".join(args.wheel) if args.wheel else "tutte")
    )
    print(f"Osservazioni:  {len(observations)}")
    print()
    print(render_rows(rows, only_candidates=args.only_candidates))
    print()

    if candidates:
        print("===== CANDIDATI ESPLORATIVI =====")
        for row in candidates:
            print(
                f"{row.twin_number:02d} / {row.condition}: "
                f"{format_percent(row.observed_probability)} "
                f"su {row.cases} casi, q={row.q_value:.4g}."
            )
        print(
            "Nessun candidato è promosso a segnale operativo "
            "senza validazione indipendente."
        )
    else:
        print(
            "Nessun trigger sui numeri gemelli "
            "statisticamente supportato."
        )

    print()
    print(f"CSV:  {args.csv}")
    print(f"JSON: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
