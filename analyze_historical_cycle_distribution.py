#!/usr/bin/env python3

"""Confronto descrittivo tra cicli storici e modello esatto."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from lotto_digit_coverage.application.historical_cycles import (
    CycleDistributionSummary,
    DurationComparisonRow,
    SegmentAnalysis,
    analyze_segment_from_draws,
    build_duration_comparison,
    empirical_quantile,
    summarize_durations,
)
from lotto_digit_coverage.infrastructure.historical_archives import (
    load_merged_coverage_draws,
)


PRIMARY_DATABASES = (
    Path("data/lotto-2023.sqlite3"),
    Path("data/lotto-2024.sqlite3"),
    Path("data/lotto-2025.sqlite3"),
    Path("data/lotto-current.sqlite3"),
)
SECONDARY_DATABASES: tuple[Path, ...] = ()
DEFAULT_TEXT_OUTPUT = Path("_work/historical-cycle-comparison.txt")
DEFAULT_JSON_OUTPUT = Path("_work/historical-cycle-comparison.json")


def analyze_segment(label: str, database_paths: Sequence[Path]) -> SegmentAnalysis:
    if not database_paths:
        raise ValueError("Serve almeno un database per segmento.")
    return analyze_segment_from_draws(
        label,
        tuple(str(path) for path in database_paths),
        load_merged_coverage_draws(database_paths),
    )


def render_segment(segment: SegmentAnalysis) -> list[str]:
    summary = segment.summary
    lines = [
        f"===== {segment.label.upper()} =====",
        "",
        f"Periodo:                 {segment.first_date} → {segment.last_date}",
        "Database:                " + ", ".join(segment.database_paths),
        f"Ruote:                  {len(segment.histories)}",
        f"Cicli completi:         {summary.cycle_count}",
        (
            f"Durata minima/massima:  {summary.minimum_duration} / "
            f"{summary.maximum_duration}"
        ),
        "",
        "Momenti:",
        f"  media osservata:      {summary.observed_mean:.6f}",
        f"  media teorica:        {summary.theoretical_mean:.6f}",
        f"  differenza media:     {summary.mean_difference:+.6f}",
        f"  varianza osservata:   {summary.observed_variance:.6f}",
        f"  varianza teorica:     {summary.theoretical_variance:.6f}",
        f"  differenza varianza:  {summary.variance_difference:+.6f}",
        "",
        "Quantili osservati / teorici:",
        f"  Q50:                  {summary.observed_quantile_50} / {summary.theoretical_quantile_50}",
        f"  Q90:                  {summary.observed_quantile_90} / {summary.theoretical_quantile_90}",
        f"  Q95:                  {summary.observed_quantile_95} / {summary.theoretical_quantile_95}",
        f"  Q99:                  {summary.observed_quantile_99} / {summary.theoretical_quantile_99}",
        "",
        "Errore descrittivo della CDF:",
        f"  medio assoluto:       {summary.cdf_mean_absolute_error:.4%}",
        f"  massimo assoluto:     {summary.cdf_maximum_absolute_error:.4%}",
        (
            f"  coda teorica oltre {summary.comparison_horizon}: "
            f"{summary.theoretical_tail_after_horizon:.6%}"
        ),
        "",
        "Distribuzione delle durate:",
        "",
        (
            "Durata  Osservati  Attesi    P osservata  P teorica  "
            "CDF osservata  CDF teorica"
        ),
        (
            "------  ----------  --------  -----------  ---------  "
            "-------------  -----------"
        ),
    ]

    for row in segment.duration_rows:
        lines.append(
            f"{row.duration:<8}{row.observed_count:<12}{row.expected_count:<10.3f}"
            f"{row.observed_probability:>10.2%}  {row.theoretical_probability:>8.2%}  "
            f"{row.observed_cdf:>12.2%}  {row.theoretical_cdf:>10.2%}"
        )

    lines.extend(
        [
            "",
            "Riepilogo per ruota:",
            "",
            (
                "Ruota        Cicli  Media   Iniziale censurato  "
                "Finale censurato  Mancanti finali"
            ),
            (
                "------------  -----  ------  ------------------  "
                "---------------  ---------------"
            ),
        ]
    )
    for history in segment.histories:
        durations = [cycle.draws_in_cycle for cycle in history.completed_cycles]
        mean = statistics.fmean(durations) if durations else 0.0
        missing = "{" + ",".join(
            str(digit) for digit in sorted(history.right_censored_missing_digits)
        ) + "}"
        lines.append(
            f"{history.wheel:<14}{len(durations):<7}{mean:<8.3f}"
            f"{history.initial_left_censored_draws:<20}"
            f"{history.right_censored_draws:<17}{missing}"
        )
    lines.append("")
    return lines


def render_report(
    primary: SegmentAnalysis,
    secondary: SegmentAnalysis | None = None,
) -> str:
    lines = [
        "===== CONFRONTO STORICO DEI CICLI DI COPERTURA =====",
        "",
        (
            "Il rapporto confronta le durate dei cicli naturali completi con "
            "la distribuzione esatta del tempo di assorbimento dallo stato "
            "{0,1,2,3,4,5,6,7,8,9}."
        ),
        "",
        "Regole di osservazione:",
        "- il primo ciclo di ogni ruota e segmento è escluso perché censurato a sinistra;",
        "- l'ultimo ciclo incompleto è registrato ma escluso dalle durate complete;",
        "- eventuali segmenti aggiuntivi restano separati quando gli archivi non sono temporalmente continui;",
        "- le ruote condividono il calendario delle estrazioni e non sono trattate come osservazioni indipendenti;",
        "- il confronto è descrittivo, non un test inferenziale e non una regola predittiva.",
        "",
    ]
    lines.extend(render_segment(primary))
    if secondary is not None:
        lines.extend(render_segment(secondary))
    return "\n".join(lines)


def segment_to_json(segment: SegmentAnalysis) -> dict[str, object]:
    return {
        "label": segment.label,
        "database_paths": list(segment.database_paths),
        "first_date": segment.first_date,
        "last_date": segment.last_date,
        "summary": asdict(segment.summary),
        "wheel_histories": [
            {
                **asdict(history),
                "right_censored_missing_digits": sorted(
                    history.right_censored_missing_digits
                ),
                "completed_cycles": [asdict(cycle) for cycle in history.completed_cycles],
            }
            for history in segment.histories
        ],
        "duration_rows": [asdict(row) for row in segment.duration_rows],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Confronta le durate storiche complete con la distribuzione teorica."
    )
    parser.add_argument(
        "--primary-databases", nargs="+", type=Path, default=list(PRIMARY_DATABASES)
    )
    parser.add_argument(
        "--secondary-databases", nargs="*", type=Path, default=list(SECONDARY_DATABASES)
    )
    parser.add_argument("--text-output", type=Path, default=DEFAULT_TEXT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        primary = analyze_segment(
            "Segmento continuo 2023–2026",
            args.primary_databases,
        )
        secondary = (
            analyze_segment(
                "Segmento secondario discontinuo",
                args.secondary_databases,
            )
            if args.secondary_databases
            else None
        )
        report = render_report(primary, secondary)
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(report + "\n", encoding="utf-8")
        document = {
            "report_format_version": 1,
            "report_type": "historical-cycle-distribution-comparison",
            "interpretation": (
                "Descriptive mathematical comparison; not an inferential test or betting rule."
            ),
            "primary_segment": segment_to_json(primary),
            "secondary_segment": (
                segment_to_json(secondary) if secondary is not None else None
            ),
        }
        args.json_output.write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(report)
        print(f"Rapporto testuale: {args.text_output}")
        print(f"Rapporto JSON:     {args.json_output}")
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
