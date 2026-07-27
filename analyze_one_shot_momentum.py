#!/usr/bin/env python3

"""Valuta un segnale momentum one-shot sui residui prequentiali."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_WINDOW = 10
DEFAULT_ENTRY_Z = 1.5
DEFAULT_REARM_Z = 0.5


@dataclass(frozen=True)
class MomentumSignal:
    report: str
    wheel: str
    target_draw: int
    target_date: str
    source_latest_draw: int
    history_start_draw: int
    history_end_draw: int
    z_score: float
    probability: float
    completed: bool
    missing_digits: tuple[int, ...]
    cycle_age: int


def one_draw_probability(
    observation: dict[str, object],
) -> float:
    probabilities = observation[
        "completion_probability_within"
    ]

    return float(probabilities["1"])


def load_report(
    path: Path,
) -> tuple[str, list[dict[str, object]]]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Replay non trovato: {path}"
        )

    document = json.loads(path.read_text())

    if (
        document.get("report_type")
        != "historical-prequential-replay"
    ):
        raise ValueError(
            f"{path} non è un replay prequentiale storico."
        )

    observations = document.get("observations")

    if not isinstance(observations, list):
        raise ValueError(
            f"{path} non contiene observations valide."
        )

    for observation in observations:
        target = int(observation["target_draw"])
        source = int(observation["source_latest_draw"])

        if source >= target:
            raise ValueError(
                f"Leakage rilevato in {path}: "
                f"sorgente {source}, bersaglio {target}."
            )

    source_database = Path(
        str(document.get("source_database", path.stem))
    ).stem

    start_target = int(document["start_target"])
    end_target = int(document["end_target"])

    label = (
        f"{source_database} · "
        f"{start_target}–{end_target}"
    )

    return label, observations


def residual(
    observation: dict[str, object],
) -> float:
    return (
        float(bool(observation["completed"]))
        - one_draw_probability(observation)
    )


def residual_variance(
    observation: dict[str, object],
) -> float:
    probability = one_draw_probability(observation)

    return probability * (1.0 - probability)


def momentum_z(
    history: Sequence[dict[str, object]],
) -> float:
    if not history:
        raise ValueError(
            "La finestra momentum non può essere vuota."
        )

    residual_sum = sum(
        residual(observation)
        for observation in history
    )

    variance_sum = sum(
        residual_variance(observation)
        for observation in history
    )

    if variance_sum <= 0.0:
        raise ValueError(
            "Varianza nulla nella finestra momentum."
        )

    return residual_sum / math.sqrt(variance_sum)


def group_by_wheel(
    observations: Sequence[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    groups: dict[
        str,
        list[dict[str, object]],
    ] = defaultdict(list)

    for observation in observations:
        groups[str(observation["wheel"])].append(
            observation
        )

    for rows in groups.values():
        rows.sort(
            key=lambda observation: int(
                observation["target_draw"]
            )
        )

    return groups


def detect_signals(
    observations: Sequence[dict[str, object]],
    *,
    report_label: str,
    window: int = DEFAULT_WINDOW,
    entry_z: float = DEFAULT_ENTRY_Z,
    rearm_z: float = DEFAULT_REARM_Z,
) -> tuple[MomentumSignal, ...]:
    if window <= 0:
        raise ValueError(
            "La finestra deve essere positiva."
        )

    if rearm_z >= entry_z:
        raise ValueError(
            "La soglia di riarmo deve essere "
            "inferiore alla soglia di ingresso."
        )

    signals: list[MomentumSignal] = []

    for wheel, rows in group_by_wheel(
        observations
    ).items():
        armed = True

        for index, observation in enumerate(rows):
            if index < window:
                continue

            history = rows[index - window:index]
            z_score = momentum_z(history)

            if not armed and z_score < rearm_z:
                armed = True

            if not armed:
                continue

            if z_score < entry_z:
                continue

            signals.append(
                MomentumSignal(
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
                    history_start_draw=int(
                        history[0]["target_draw"]
                    ),
                    history_end_draw=int(
                        history[-1]["target_draw"]
                    ),
                    z_score=z_score,
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

            # Un solo colpo per onda.
            armed = False

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


def poisson_binomial_distribution(
    probabilities: Iterable[float],
) -> tuple[float, ...]:
    distribution = [1.0]

    for probability in probabilities:
        updated = [0.0] * (
            len(distribution) + 1
        )

        for successes, mass in enumerate(
            distribution
        ):
            updated[successes] += (
                mass * (1.0 - probability)
            )
            updated[successes + 1] += (
                mass * probability
            )

        distribution = updated

    return tuple(distribution)


def poisson_binomial_p_values(
    probabilities: Sequence[float],
    observed: int,
) -> tuple[float, float]:
    if not probabilities:
        return 1.0, 1.0

    distribution = poisson_binomial_distribution(
        probabilities
    )

    if not 0 <= observed < len(distribution):
        raise ValueError(
            "Numero di successi osservati non valido."
        )

    observed_mass = distribution[observed]

    upper_tail = sum(
        distribution[observed:]
    )

    two_sided = sum(
        mass
        for mass in distribution
        if mass <= observed_mass + 1e-15
    )

    return upper_tail, min(two_sided, 1.0)


def summarize(
    signals: Sequence[MomentumSignal],
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
            "mean_entry_z": 0.0,
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
            (
                outcome - probability
            )
            ** 2
            for outcome, probability
            in zip(outcomes, probabilities)
        ),
        "mean_entry_z": statistics.mean(
            signal.z_score
            for signal in signals
        ),
        "p_upper": p_upper,
        "p_two_sided": p_two_sided,
    }


def format_digits(
    digits: Sequence[int],
) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def render_summary(
    title: str,
    signals: Sequence[MomentumSignal],
) -> str:
    result = summarize(signals)

    return "\n".join(
        [
            f"===== {title} =====",
            (
                "Segnali one-shot:        "
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
                "Z medio all'ingresso:    "
                f"{result['mean_entry_z']:.3f}"
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
    signals: Sequence[MomentumSignal],
) -> str:
    if not signals:
        return "Nessun segnale momentum."

    lines = [
        (
            "Report                    Target  Data        "
            "Ruota       Finestra   Z      P1       "
            "Mancanti       Età  Esito"
        ),
        (
            "------------------------  ------  ----------  "
            "----------  ----------  -----  -------  "
            "-------------  ---  ------"
        ),
    ]

    for signal in signals:
        lines.append(
            f"{signal.report:<26}"
            f"{signal.target_draw:<8}"
            f"{signal.target_date:<12}"
            f"{signal.wheel:<12}"
            f"{signal.history_start_draw:03d}"
            f"–{signal.history_end_draw:03d}  "
            f"{signal.z_score:>5.2f}  "
            f"{signal.probability:>6.2%}  "
            f"{format_digits(signal.missing_digits):<15}"
            f"{signal.cycle_age:>3}  "
            f"{'CHIUSO' if signal.completed else 'APERTO'}"
        )

    return "\n".join(lines)


def build_json_report(
    *,
    reports: Sequence[Path],
    signals: Sequence[MomentumSignal],
    window: int,
    entry_z: float,
    rearm_z: float,
) -> dict[str, object]:
    return {
        "report_type": "one-shot-momentum-analysis",
        "methodology": (
            "For target T, momentum is computed only from "
            "the previous observations of the same wheel. "
            "A signal is evaluated on T only."
        ),
        "parameters": {
            "window": window,
            "entry_z": entry_z,
            "rearm_z": rearm_z,
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
            "Valuta un momentum positivo one-shot "
            "sui residui del modello Markov."
        ),
        epilog=(
            "Regola predefinita congelata: finestra 10, "
            "ingresso z>=1.5, un solo target, "
            "riarmo z<0.5."
        ),
    )

    parser.add_argument(
        "reports",
        nargs="+",
        type=Path,
        help="Uno o più replay prequentiali JSON.",
    )

    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW,
    )

    parser.add_argument(
        "--entry-z",
        type=float,
        default=DEFAULT_ENTRY_Z,
    )

    parser.add_argument(
        "--rearm-z",
        type=float,
        default=DEFAULT_REARM_Z,
    )

    parser.add_argument(
        "--show-signals",
        action="store_true",
        help="Mostra ogni ingresso one-shot.",
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        help="Salva anche un rapporto JSON.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        all_signals: list[MomentumSignal] = []
        signals_by_report: list[
            tuple[str, tuple[MomentumSignal, ...]]
        ] = []

        for path in args.reports:
            label, observations = load_report(path)

            signals = detect_signals(
                observations,
                report_label=label,
                window=args.window,
                entry_z=args.entry_z,
                rearm_z=args.rearm_z,
            )

            signals_by_report.append(
                (label, signals)
            )

            all_signals.extend(signals)

        print("===== MOMENTUM ONE-SHOT =====")
        print(f"Finestra:             {args.window}")
        print(
            f"Soglia ingresso:      z >= "
            f"{args.entry_z:.2f}"
        )
        print(
            f"Soglia riarmo:        z < "
            f"{args.rearm_z:.2f}"
        )
        print("Durata:               1 concorso")
        print("Direzione:            positiva")
        print()
        print(
            "Nota: i p-value sono nominali e assumono "
            "indipendenza tra i segnali."
        )

        for label, signals in signals_by_report:
            print()
            print(
                render_summary(
                    label,
                    signals,
                )
            )

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
                window=args.window,
                entry_z=args.entry_z,
                rearm_z=args.rearm_z,
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
                "Rapporto JSON:        "
                f"{args.json_output}"
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
