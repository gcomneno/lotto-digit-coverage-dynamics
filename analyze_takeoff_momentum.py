#!/usr/bin/env python3

"""Valuta MOMENTUM-2: calma, take-off e singolo colpo."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from analyze_one_shot_momentum import (
    format_digits,
    group_by_wheel,
    load_report,
    momentum_z,
    one_draw_probability,
    poisson_binomial_p_values,
)


DEFAULT_CALM_WINDOW = 5
DEFAULT_CALM_ABS_Z = 0.5
DEFAULT_WAVE_WINDOW = 2
DEFAULT_ENTRY_Z = 1.0


@dataclass(frozen=True)
class TakeoffSignal:
    report: str
    wheel: str
    target_draw: int
    target_date: str
    source_latest_draw: int
    calm_start_draw: int
    calm_end_draw: int
    calm_z: float
    wave_start_draw: int
    wave_end_draw: int
    wave_z: float
    probability: float
    completed: bool
    missing_digits: tuple[int, ...]
    cycle_age: int


def detect_takeoff_signals(
    observations: Sequence[dict[str, object]],
    *,
    report_label: str,
    calm_window: int = DEFAULT_CALM_WINDOW,
    calm_abs_z: float = DEFAULT_CALM_ABS_Z,
    wave_window: int = DEFAULT_WAVE_WINDOW,
    entry_z: float = DEFAULT_ENTRY_Z,
) -> tuple[TakeoffSignal, ...]:
    if calm_window <= 0:
        raise ValueError(
            "La finestra di calma deve essere positiva."
        )

    if wave_window <= 0:
        raise ValueError(
            "La finestra dell'onda deve essere positiva."
        )

    if calm_abs_z < 0.0:
        raise ValueError(
            "La soglia assoluta di calma non può essere negativa."
        )

    if entry_z <= 0.0:
        raise ValueError(
            "La soglia di ingresso deve essere positiva."
        )

    signals: list[TakeoffSignal] = []

    for wheel, rows in group_by_wheel(
        observations
    ).items():
        calibrated = False

        calm_start_draw = 0
        calm_end_draw = 0
        calibrated_calm_z = 0.0

        # Indice dell'osservazione bersaglio dell'ultimo colpo.
        # Una nuova finestra di calma deve iniziare dopo questo indice.
        last_signal_index = -1

        minimum_history = max(
            calm_window,
            wave_window,
        )

        for index, observation in enumerate(rows):
            if index < minimum_history:
                continue

            if not calibrated:
                calm_start_index = index - calm_window

                if calm_start_index <= last_signal_index:
                    continue

                calm_history = rows[
                    calm_start_index:index
                ]

                current_calm_z = momentum_z(
                    calm_history
                )

                if abs(current_calm_z) > calm_abs_z:
                    continue

                calibrated = True
                calm_start_draw = int(
                    calm_history[0]["target_draw"]
                )
                calm_end_draw = int(
                    calm_history[-1]["target_draw"]
                )
                calibrated_calm_z = current_calm_z

                # La stessa storia non può essere contemporaneamente
                # la calma e il take-off.
                continue

            wave_history = rows[
                index - wave_window:index
            ]

            current_wave_z = momentum_z(
                wave_history
            )

            if current_wave_z < entry_z:
                continue

            signals.append(
                TakeoffSignal(
                    report=report_label,
                    wheel=wheel,
                    target_draw=int(
                        observation["target_draw"]
                    ),
                    target_date=str(
                        observation["target_date"]
                    ),
                    source_latest_draw=int(
                        observation["source_latest_draw"]
                    ),
                    calm_start_draw=calm_start_draw,
                    calm_end_draw=calm_end_draw,
                    calm_z=calibrated_calm_z,
                    wave_start_draw=int(
                        wave_history[0]["target_draw"]
                    ),
                    wave_end_draw=int(
                        wave_history[-1]["target_draw"]
                    ),
                    wave_z=current_wave_z,
                    probability=one_draw_probability(
                        observation
                    ),
                    completed=bool(
                        observation["completed"]
                    ),
                    missing_digits=tuple(
                        int(digit)
                        for digit in observation[
                            "missing_digits"
                        ]
                    ),
                    cycle_age=int(
                        observation["cycle_age"]
                    ),
                )
            )

            last_signal_index = index
            calibrated = False

    return tuple(
        sorted(
            signals,
            key=lambda signal: (
                signal.report,
                signal.target_draw,
                signal.wheel,
            ),
        )
    )


def summarize(
    signals: Sequence[TakeoffSignal],
) -> dict[str, float | int]:
    cases = len(signals)

    if not signals:
        return {
            "cases": 0,
            "unique_targets": 0,
            "expected": 0.0,
            "observed": 0,
            "expected_rate": 0.0,
            "observed_rate": 0.0,
            "delta": 0.0,
            "brier": 0.0,
            "mean_calm_z": 0.0,
            "mean_wave_z": 0.0,
            "p_upper": 1.0,
            "p_two_sided": 1.0,
        }

    probabilities = tuple(
        signal.probability
        for signal in signals
    )

    outcomes = tuple(
        float(signal.completed)
        for signal in signals
    )

    expected = sum(probabilities)
    observed = int(sum(outcomes))

    p_upper, p_two_sided = (
        poisson_binomial_p_values(
            probabilities,
            observed,
        )
    )

    return {
        "cases": cases,
        "unique_targets": len(
            {
                (
                    signal.report,
                    signal.target_draw,
                )
                for signal in signals
            }
        ),
        "expected": expected,
        "observed": observed,
        "expected_rate": expected / cases,
        "observed_rate": observed / cases,
        "delta": (
            observed / cases
            - expected / cases
        ),
        "brier": statistics.mean(
            (outcome - probability) ** 2
            for outcome, probability
            in zip(outcomes, probabilities)
        ),
        "mean_calm_z": statistics.mean(
            signal.calm_z
            for signal in signals
        ),
        "mean_wave_z": statistics.mean(
            signal.wave_z
            for signal in signals
        ),
        "p_upper": p_upper,
        "p_two_sided": p_two_sided,
    }


def render_summary(
    title: str,
    signals: Sequence[TakeoffSignal],
) -> str:
    result = summarize(signals)

    return "\n".join(
        [
            f"===== {title} =====",
            (
                "Segnali take-off:         "
                f"{result['cases']}"
            ),
            (
                "Concorsi distinti:       "
                f"{result['unique_targets']}"
            ),
            (
                "Chiusure attese:         "
                f"{result['expected']:.3f}"
            ),
            (
                "Chiusure osservate:      "
                f"{result['observed']}"
            ),
            (
                "Tasso previsto:          "
                f"{result['expected_rate']:.2%}"
            ),
            (
                "Tasso osservato:         "
                f"{result['observed_rate']:.2%}"
            ),
            (
                "Delta osservato-atteso:  "
                f"{result['delta']:+.2%}"
            ),
            (
                "Brier score:             "
                f"{result['brier']:.4f}"
            ),
            (
                "Z medio della calma:     "
                f"{result['mean_calm_z']:.3f}"
            ),
            (
                "Z medio del take-off:    "
                f"{result['mean_wave_z']:.3f}"
            ),
            (
                "p nominale unilaterale:  "
                f"{result['p_upper']:.4f}"
            ),
            (
                "p nominale bilaterale:   "
                f"{result['p_two_sided']:.4f}"
            ),
        ]
    )


def render_signals(
    signals: Sequence[TakeoffSignal],
) -> str:
    if not signals:
        return "Nessun segnale take-off."

    lines = [
        (
            "Report                    Target  Data        "
            "Ruota       Calma     z5     Onda      z2     "
            "P1       Mancanti       Età  Esito"
        ),
        (
            "------------------------  ------  ----------  "
            "----------  --------  -----  --------  -----  "
            "-------  -------------  ---  ------"
        ),
    ]

    for signal in signals:
        lines.append(
            f"{signal.report:<26}"
            f"{signal.target_draw:<8}"
            f"{signal.target_date:<12}"
            f"{signal.wheel:<12}"
            f"{signal.calm_start_draw:03d}"
            f"–{signal.calm_end_draw:03d}  "
            f"{signal.calm_z:>5.2f}  "
            f"{signal.wave_start_draw:03d}"
            f"–{signal.wave_end_draw:03d}  "
            f"{signal.wave_z:>5.2f}  "
            f"{signal.probability:>6.2%}  "
            f"{format_digits(signal.missing_digits):<15}"
            f"{signal.cycle_age:>3}  "
            f"{'CHIUSO' if signal.completed else 'APERTO'}"
        )

    return "\n".join(lines)


def build_json_report(
    *,
    reports: Sequence[Path],
    signals: Sequence[TakeoffSignal],
    calm_window: int,
    calm_abs_z: float,
    wave_window: int,
    entry_z: float,
) -> dict[str, object]:
    return {
        "report_type": "takeoff-momentum-analysis",
        "strategy_id": "MOMENTUM-2-TAKEOFF",
        "methodology": (
            "For target T, calm and wave conditions are computed "
            "only from observations strictly earlier than T. "
            "After a signal, a new calm window must consist entirely "
            "of later observations."
        ),
        "parameters": {
            "calm_window": calm_window,
            "calm_abs_z": calm_abs_z,
            "wave_window": wave_window,
            "entry_z": entry_z,
            "duration": 1,
            "direction": "positive",
        },
        "source_reports": [
            str(path)
            for path in reports
        ],
        "summary": summarize(signals),
        "signals": [
            asdict(signal)
            for signal in signals
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Valuta MOMENTUM-2: calma, accelerazione "
            "e singolo segnale take-off."
        ),
        epilog=(
            "Regola congelata: |z5|<=0.5, z2>=1.0, "
            "un solo target e nuova calma completa dopo il colpo."
        ),
    )

    parser.add_argument(
        "reports",
        nargs="+",
        type=Path,
        help="Uno o più replay prequentiali JSON.",
    )

    parser.add_argument(
        "--calm-window",
        type=int,
        default=DEFAULT_CALM_WINDOW,
    )

    parser.add_argument(
        "--calm-abs-z",
        type=float,
        default=DEFAULT_CALM_ABS_Z,
    )

    parser.add_argument(
        "--wave-window",
        type=int,
        default=DEFAULT_WAVE_WINDOW,
    )

    parser.add_argument(
        "--entry-z",
        type=float,
        default=DEFAULT_ENTRY_Z,
    )

    parser.add_argument(
        "--show-signals",
        action="store_true",
    )

    parser.add_argument(
        "--json-output",
        type=Path,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        all_signals: list[TakeoffSignal] = []
        signals_by_report: list[
            tuple[str, tuple[TakeoffSignal, ...]]
        ] = []

        for path in args.reports:
            label, observations = load_report(path)

            signals = detect_takeoff_signals(
                observations,
                report_label=label,
                calm_window=args.calm_window,
                calm_abs_z=args.calm_abs_z,
                wave_window=args.wave_window,
                entry_z=args.entry_z,
            )

            signals_by_report.append(
                (label, signals)
            )
            all_signals.extend(signals)

        print("===== MOMENTUM-2 · TAKE-OFF =====")
        print(
            f"Calma:                |z{args.calm_window}| "
            f"<= {args.calm_abs_z:.2f}"
        )
        print(
            f"Take-off:             z{args.wave_window} "
            f">= {args.entry_z:.2f}"
        )
        print("Durata:               1 concorso")
        print(
            "Ritaratura:           nuova finestra di calma "
            "dopo il colpo"
        )
        print()
        print(
            "Nota: i p-value sono nominali e assumono "
            "indipendenza tra i segnali."
        )

        for label, signals in signals_by_report:
            print()
            print(render_summary(label, signals))

        print()
        print(
            render_summary(
                "COMBINAZIONE DI TUTTI I SEGMENTI",
                all_signals,
            )
        )

        if args.show_signals:
            print()
            print("===== SEGNALI INDIVIDUALI =====")
            print(render_signals(all_signals))

        if args.json_output is not None:
            args.json_output.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            report = build_json_report(
                reports=args.reports,
                signals=all_signals,
                calm_window=args.calm_window,
                calm_abs_z=args.calm_abs_z,
                wave_window=args.wave_window,
                entry_z=args.entry_z,
            )

            args.json_output.write_text(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

            print()
            print(
                f"Rapporto JSON:        {args.json_output}"
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
