#!/usr/bin/env python3

"""Ispeziona l'intero replay prequentiale di una singola ruota."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_REPORT = Path(
    "_work/prequential-replay-2025-from-0101.json"
)


def format_digits(digits: Iterable[int]) -> str:
    values = tuple(sorted(digits))

    return "{" + ",".join(
        str(digit)
        for digit in values
    ) + "}"


def format_numbers(numbers: Iterable[int]) -> str:
    return " ".join(
        f"{number:02d}"
        for number in numbers
    )


def load_report(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Registro prequentiale non trovato: {path}"
        )

    document = json.loads(path.read_text())

    required = {
        "report_type",
        "start_target",
        "end_target",
        "summary",
        "observations",
    }

    missing = required.difference(document)

    if missing:
        raise ValueError(
            "Registro incompleto; campi mancanti: "
            + ", ".join(sorted(missing))
        )

    if (
        document["report_type"]
        != "historical-prequential-replay"
    ):
        raise ValueError(
            "Il file non è un replay prequentiale storico."
        )

    if not isinstance(document["observations"], list):
        raise ValueError(
            "Il campo observations deve essere una lista."
        )

    return document


def available_wheels(
    observations: Sequence[dict[str, object]],
) -> tuple[str, ...]:
    order: dict[str, int] = {}

    for observation in observations:
        wheel = str(observation["wheel"])
        wheel_order = int(observation["wheel_order"])

        order[wheel] = wheel_order

    return tuple(
        sorted(
            order,
            key=lambda wheel: order[wheel],
        )
    )


def resolve_wheel(
    requested: str,
    wheels: Sequence[str],
) -> str:
    normalized = requested.casefold().strip()

    for wheel in wheels:
        if wheel.casefold() == normalized:
            return wheel

    raise ValueError(
        f"Ruota sconosciuta: {requested}. "
        "Ruote disponibili: "
        + ", ".join(wheels)
    )


def select_observations(
    observations: Sequence[dict[str, object]],
    *,
    wheel: str,
    start_target: int | None = None,
    end_target: int | None = None,
) -> tuple[dict[str, object], ...]:
    if (
        start_target is not None
        and end_target is not None
        and end_target < start_target
    ):
        raise ValueError(
            "Il concorso finale precede quello iniziale."
        )

    selected = tuple(
        sorted(
            (
                observation
                for observation in observations
                if observation["wheel"] == wheel
                and (
                    start_target is None
                    or int(observation["target_draw"])
                    >= start_target
                )
                and (
                    end_target is None
                    or int(observation["target_draw"])
                    <= end_target
                )
            ),
            key=lambda observation: int(
                observation["target_draw"]
            ),
        )
    )

    if not selected:
        raise ValueError(
            "Nessuna osservazione corrisponde ai filtri richiesti."
        )

    return selected


def one_draw_probability(
    observation: dict[str, object],
) -> float:
    probabilities = observation[
        "completion_probability_within"
    ]

    return float(probabilities["1"])


def summarize(
    observations: Sequence[dict[str, object]],
) -> dict[str, float | int]:
    if not observations:
        raise ValueError(
            "Nessuna osservazione da riepilogare."
        )

    probabilities = tuple(
        one_draw_probability(observation)
        for observation in observations
    )

    outcomes = tuple(
        float(bool(observation["completed"]))
        for observation in observations
    )

    expected = sum(probabilities)
    observed = int(sum(outcomes))

    brier = statistics.mean(
        (outcome - probability) ** 2
        for outcome, probability
        in zip(outcomes, probabilities)
    )

    epsilon = 1e-15

    log_loss = -statistics.mean(
        outcome
        * math.log(
            min(
                max(probability, epsilon),
                1.0 - epsilon,
            )
        )
        + (1.0 - outcome)
        * math.log(
            min(
                max(1.0 - probability, epsilon),
                1.0 - epsilon,
            )
        )
        for outcome, probability
        in zip(outcomes, probabilities)
    )

    longest_open_run = 0
    current_open_run = 0

    for observation in observations:
        if observation["completed"]:
            current_open_run = 0
        else:
            current_open_run += 1
            longest_open_run = max(
                longest_open_run,
                current_open_run,
            )

    return {
        "cases": len(observations),
        "expected_closures": expected,
        "observed_closures": observed,
        "predicted_rate": expected / len(observations),
        "observed_rate": observed / len(observations),
        "delta_rate": (
            observed / len(observations)
            - expected / len(observations)
        ),
        "brier_score": brier,
        "log_loss": log_loss,
        "longest_open_run": longest_open_run,
    }


def render_summary(
    wheel: str,
    observations: Sequence[dict[str, object]],
) -> str:
    result = summarize(observations)

    lines = [
        f"===== REPLAY PREQUENTIALE: {wheel.upper()} =====",
        (
            "Intervallo:             "
            f"{observations[0]['target_draw']}"
            "–"
            f"{observations[-1]['target_draw']}"
        ),
        f"Concorsi:               {result['cases']}",
        (
            "Chiusure attese:        "
            f"{result['expected_closures']:.3f}"
        ),
        (
            "Chiusure osservate:     "
            f"{result['observed_closures']}"
        ),
        (
            "Tasso previsto:         "
            f"{result['predicted_rate']:.2%}"
        ),
        (
            "Tasso osservato:        "
            f"{result['observed_rate']:.2%}"
        ),
        (
            "Delta osservato-atteso: "
            f"{result['delta_rate']:+.2%}"
        ),
        (
            "Brier score:            "
            f"{result['brier_score']:.4f}"
        ),
        (
            "Log loss:               "
            f"{result['log_loss']:.4f}"
        ),
        (
            "Serie aperta massima:   "
            f"{result['longest_open_run']} concorsi"
        ),
    ]

    return "\n".join(lines)


def render_table(
    observations: Sequence[dict[str, object]],
) -> str:
    lines = [
        (
            "Target  Data        Src  Età  Mancanti       "
            "P1       Attesa  Numeri              Esito   "
            "Restano        Cum.att  Cum.reali  Cum.Brier"
        ),
        (
            "------  ----------  ---  ---  -------------  "
            "-------  ------  ------------------  ------  "
            "-------------  -------  ---------  ---------"
        ),
    ]

    cumulative_expected = 0.0
    cumulative_observed = 0
    cumulative_squared_error = 0.0

    for index, observation in enumerate(
        observations,
        start=1,
    ):
        probability = one_draw_probability(observation)
        outcome = float(bool(observation["completed"]))

        cumulative_expected += probability
        cumulative_observed += int(outcome)
        cumulative_squared_error += (
            outcome - probability
        ) ** 2

        missing = format_digits(
            observation["missing_digits"]
        )

        remaining = format_digits(
            observation["remaining_before_reset"]
        )

        numbers = format_numbers(
            observation["target_numbers"]
        )

        lines.append(
            f"{int(observation['target_draw']):<8}"
            f"{str(observation['target_date']):<12}"
            f"{int(observation['source_latest_draw']):<5}"
            f"{int(observation['cycle_age']):<5}"
            f"{missing:<15}"
            f"{probability:>6.2%}  "
            f"{float(observation['expected_remaining_draws']):>6.3f}  "
            f"{numbers:<20}"
            f"{'CHIUSO' if observation['completed'] else 'APERTO':<8}"
            f"{remaining:<15}"
            f"{cumulative_expected:>7.2f}  "
            f"{cumulative_observed:>9}  "
            f"{cumulative_squared_error / index:>9.4f}"
        )

    return "\n".join(lines)


def render_detail(
    observations: Sequence[dict[str, object]],
) -> str:
    blocks: list[str] = []

    for observation in observations:
        probabilities = observation[
            "completion_probability_within"
        ]

        blocks.append(
            "\n".join(
                [
                    (
                        "===== CONCORSO "
                        f"{observation['target_draw']} · "
                        f"{observation['target_date']} ====="
                    ),
                    (
                        "Sorgente disponibile fino al: "
                        f"{observation['source_latest_draw']} · "
                        f"{observation['source_latest_date']}"
                    ),
                    (
                        "Età del ciclo:               "
                        f"{observation['cycle_age']}"
                    ),
                    (
                        "Cifre mancanti:              "
                        f"{format_digits(
                            observation['missing_digits']
                        )}"
                    ),
                    (
                        "Chiusura entro 1:            "
                        f"{float(probabilities['1']):.2%}"
                    ),
                    (
                        "Chiusura entro 2:            "
                        f"{float(probabilities['2']):.2%}"
                    ),
                    (
                        "Chiusura entro 3:            "
                        f"{float(probabilities['3']):.2%}"
                    ),
                    (
                        "Chiusura entro 5:            "
                        f"{float(probabilities['5']):.2%}"
                    ),
                    (
                        "Attesa residua teorica:      "
                        f"{float(
                            observation[
                                'expected_remaining_draws'
                            ]
                        ):.3f}"
                    ),
                    (
                        "Numeri estratti:             "
                        f"{format_numbers(
                            observation['target_numbers']
                        )}"
                    ),
                    (
                        "Cifre estratte:              "
                        f"{format_digits(
                            observation['target_digits']
                        )}"
                    ),
                    (
                        "Esito:                       "
                        f"{'CHIUSO' if observation['completed'] else 'APERTO'}"
                    ),
                    (
                        "Cifre rimaste:               "
                        f"{format_digits(
                            observation[
                                'remaining_before_reset'
                            ]
                        )}"
                    ),
                ]
            )
        )

    return "\n\n".join(blocks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Mostra l'intero replay prequentiale "
            "di una singola ruota."
        ),
        epilog=(
            "Esempio: "
            "python3 inspect_prequential_wheel.py Bari | less -S"
        ),
    )

    parser.add_argument(
        "wheel",
        help="Ruota da ispezionare, per esempio Bari.",
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help=(
            "Registro JSON del replay. "
            f"Default: {DEFAULT_REPORT}"
        ),
    )

    parser.add_argument(
        "--start-target",
        type=int,
        help="Primo concorso da mostrare.",
    )

    parser.add_argument(
        "--end-target",
        type=int,
        help="Ultimo concorso da mostrare.",
    )

    parser.add_argument(
        "--format",
        choices=("table", "detail"),
        default="table",
        help="Formato dell'output. Default: table.",
    )

    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Non mostrare il riepilogo iniziale.",
    )

    parser.add_argument(
        "--list-wheels",
        action="store_true",
        help="Elenca le ruote disponibili ed esce.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        report = load_report(args.report)
        observations = report["observations"]
        wheels = available_wheels(observations)

        if args.list_wheels:
            print("\n".join(wheels))
            return 0

        wheel = resolve_wheel(
            args.wheel,
            wheels,
        )

        selected = select_observations(
            observations,
            wheel=wheel,
            start_target=args.start_target,
            end_target=args.end_target,
        )

        if not args.no_summary:
            print(render_summary(wheel, selected))
            print()

        if args.format == "table":
            print(render_table(selected))
        else:
            print(render_detail(selected))

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
