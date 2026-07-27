#!/usr/bin/env python3

"""Replay prequentiale walk-forward del modello Markov."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from strategies.digit_coverage import load_draws_by_wheel
from strategies.prequential_replay import (
    PrequentialReplayObservation,
    build_prequential_replay,
)
from strategies.prequential_validation import (
    MODEL_ID,
    sha256_file,
)
from strategies.twin_digits import LottoRepository


DEFAULT_DATABASE = Path("data/lotto-2025.sqlite3")
DEFAULT_START_TARGET = 101
DEFAULT_OUTPUT = Path(
    "_work/prequential-replay-2025-from-0101.json"
)


def repository_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()


def format_digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(
        str(digit)
        for digit in sorted(digits)
    ) + "}"


def summarize(
    observations: Sequence[PrequentialReplayObservation],
) -> dict[str, float | int]:
    total = len(observations)

    if total == 0:
        raise ValueError(
            "Nessuna osservazione da riepilogare."
        )

    probabilities = tuple(
        observation.probability(1)
        for observation in observations
    )

    outcomes = tuple(
        float(observation.completed)
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

    return {
        "cases": total,
        "expected_closures": expected,
        "observed_closures": observed,
        "predicted_rate": expected / total,
        "observed_rate": observed / total,
        "delta_rate": observed / total - expected / total,
        "brier_score": brier,
        "log_loss": log_loss,
    }


def observation_to_dict(
    observation: PrequentialReplayObservation,
) -> dict[str, object]:
    return {
        "target_draw": observation.target_draw,
        "target_date": observation.target_date,
        "wheel": observation.wheel,
        "wheel_order": observation.wheel_order,
        "source_latest_draw": (
            observation.source_latest_draw
        ),
        "source_latest_date": (
            observation.source_latest_date
        ),
        "cycle_age": observation.cycle_age,
        "missing_digits": sorted(
            observation.missing_digits
        ),
        "completion_probability_within": {
            str(horizon): probability
            for horizon, probability
            in observation.completion_probability_within
        },
        "expected_remaining_draws": (
            observation.expected_remaining_draws
        ),
        "target_numbers": list(
            observation.target_numbers
        ),
        "target_digits": sorted(
            observation.target_digits
        ),
        "completed": observation.completed,
        "remaining_before_reset": sorted(
            observation.remaining_before_reset
        ),
    }


def build_report(
    observations: Sequence[PrequentialReplayObservation],
    *,
    database: Path,
    start_target: int,
    end_target: int,
) -> dict[str, object]:
    return {
        "report_format_version": 1,
        "report_type": "historical-prequential-replay",
        "model_id": MODEL_ID,
        "repository_commit": repository_commit(),
        "source_database": str(database),
        "source_database_sha256": sha256_file(database),
        "start_target": start_target,
        "end_target": end_target,
        "methodology": (
            "For every target draw T, model state and probabilities "
            "are computed using only draws strictly earlier than T."
        ),
        "limitations": (
            "Historical walk-forward replay is leakage-safe but is "
            "not equivalent to a forecast published before the event."
        ),
        "summary": summarize(observations),
        "observations": [
            observation_to_dict(observation)
            for observation in observations
        ],
    }


def write_report(
    report: dict[str, object],
    output: Path,
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def print_target_table(
    observations: Sequence[PrequentialReplayObservation],
) -> None:
    groups: dict[
        int,
        list[PrequentialReplayObservation],
    ] = defaultdict(list)

    for observation in observations:
        groups[observation.target_draw].append(observation)

    cumulative_cases = 0
    cumulative_expected = 0.0
    cumulative_observed = 0
    cumulative_squared_error = 0.0

    print("\n===== PROGRESSIONE WALK-FORWARD =====")
    print()
    print(
        "Target  Data        Attese  Reali  Delta  "
        "Brier   Cum.att  Cum.reali  Cum.Brier"
    )
    print(
        "------  ----------  ------  -----  -----  "
        "------  -------  ---------  ---------"
    )

    for target_draw in sorted(groups):
        items = groups[target_draw]
        target_summary = summarize(items)

        target_squared_error = sum(
            (
                float(item.completed)
                - item.probability(1)
            )
            ** 2
            for item in items
        )

        cumulative_cases += len(items)
        cumulative_expected += float(
            target_summary["expected_closures"]
        )
        cumulative_observed += int(
            target_summary["observed_closures"]
        )
        cumulative_squared_error += target_squared_error

        print(
            f"{target_draw:<8}"
            f"{items[0].target_date:<12}"
            f"{target_summary['expected_closures']:>5.2f}  "
            f"{target_summary['observed_closures']:>5}  "
            f"{(
                target_summary['observed_closures']
                - target_summary['expected_closures']
            ):>+5.2f}  "
            f"{target_summary['brier_score']:>6.4f}  "
            f"{cumulative_expected:>7.2f}  "
            f"{cumulative_observed:>9}  "
            f"{(
                cumulative_squared_error
                / cumulative_cases
            ):>9.4f}"
        )


def print_wheel_table(
    observations: Sequence[PrequentialReplayObservation],
) -> None:
    groups: dict[
        str,
        list[PrequentialReplayObservation],
    ] = defaultdict(list)

    wheel_order: dict[str, int] = {}

    for observation in observations:
        groups[observation.wheel].append(observation)
        wheel_order[observation.wheel] = (
            observation.wheel_order
        )

    print("\n===== RISULTATI PER RUOTA =====")
    print()
    print(
        "Ruota       Casi  Attese  Reali  Previsto  "
        "Osservato  Delta    Brier"
    )
    print(
        "----------  ----  ------  -----  --------  "
        "---------  -------  ------"
    )

    for wheel in sorted(
        groups,
        key=lambda name: wheel_order[name],
    ):
        result = summarize(groups[wheel])

        print(
            f"{wheel:<12}"
            f"{result['cases']:<6}"
            f"{result['expected_closures']:>6.2f}  "
            f"{result['observed_closures']:>5}  "
            f"{result['predicted_rate']:>7.2%}  "
            f"{result['observed_rate']:>8.2%}  "
            f"{result['delta_rate']:>+6.2%}  "
            f"{result['brier_score']:>6.4f}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ricostruisce un replay prequentiale storico "
            "senza contaminazione dal futuro."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )

    parser.add_argument(
        "--start-target",
        type=int,
        default=DEFAULT_START_TARGET,
    )

    parser.add_argument(
        "--end-target",
        type=int,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        with LottoRepository(args.database) as repository:
            draws_by_wheel = load_draws_by_wheel(repository)

        observations = build_prequential_replay(
            draws_by_wheel,
            start_target=args.start_target,
            end_target=args.end_target,
        )

        end_target = max(
            observation.target_draw
            for observation in observations
        )

        report = build_report(
            observations,
            database=args.database,
            start_target=args.start_target,
            end_target=end_target,
        )

        write_report(report, args.output)

        result = report["summary"]

        print("===== REPLAY PREQUENTIALE STORICO =====")
        print(f"Database:             {args.database}")
        print(
            "Intervallo target:    "
            f"{args.start_target}–{end_target}"
        )
        print(
            "Concorsi valutati:    "
            f"{len(set(
                observation.target_draw
                for observation in observations
            ))}"
        )
        print(f"Previsioni ruota:     {result['cases']}")
        print(
            "Chiusure attese:      "
            f"{result['expected_closures']:.3f}"
        )
        print(
            "Chiusure osservate:   "
            f"{result['observed_closures']}"
        )
        print(
            "Tasso previsto:       "
            f"{result['predicted_rate']:.2%}"
        )
        print(
            "Tasso osservato:      "
            f"{result['observed_rate']:.2%}"
        )
        print(
            "Delta:                "
            f"{result['delta_rate']:+.2%}"
        )
        print(
            "Brier score:          "
            f"{result['brier_score']:.4f}"
        )
        print(
            "Log loss:             "
            f"{result['log_loss']:.4f}"
        )
        print(f"Registro JSON:        {args.output}")
        print()
        print(
            "Nota: replay walk-forward senza leakage; "
            "non equivale a una previsione pubblicata in anticipo."
        )

        print_target_table(observations)
        print_wheel_table(observations)

    except (
        FileNotFoundError,
        RuntimeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
