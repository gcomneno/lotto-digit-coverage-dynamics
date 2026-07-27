#!/usr/bin/env python3

"""Analizza le chiusure prodotte da numeri formati dalla coppia mancante."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_REPORT = Path(
    "_work/prequential-replay-2025-from-0101.json"
)


def format_pair(pair: Iterable[int]) -> str:
    values = tuple(sorted(pair))
    return "{" + ",".join(map(str, values)) + "}"


def format_numbers(numbers: Iterable[int]) -> str:
    return " ".join(
        f"{number:02d}"
        for number in numbers
    )


def pair_numbers(pair: Sequence[int]) -> tuple[int, ...]:
    """Restituisce ab e ba quando sono numeri Lotto validi 01–90."""

    if len(pair) != 2:
        raise ValueError(
            "Una coppia deve contenere esattamente due cifre."
        )

    first, second = sorted(int(value) for value in pair)

    if first == second:
        raise ValueError(
            "Le cifre della coppia devono essere distinte."
        )

    candidates = {
        10 * first + second,
        10 * second + first,
    }

    return tuple(
        sorted(
            number
            for number in candidates
            if 1 <= number <= 90
        )
    )


def candidate_hit_probability(candidate_count: int) -> float:
    """P(almeno un candidato fra 5 numeri estratti su 90)."""

    if not 0 <= candidate_count <= 90:
        raise ValueError(
            "Numero di candidati non valido."
        )

    if candidate_count == 0:
        return 0.0

    return 1.0 - (
        math.comb(90 - candidate_count, 5)
        / math.comb(90, 5)
    )


def load_observations(path: Path) -> list[dict[str, object]]:
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
            "Il documento non è un replay prequentiale storico."
        )

    observations = document.get("observations")

    if not isinstance(observations, list):
        raise ValueError(
            "Il replay non contiene observations valide."
        )

    return observations


def parse_pair(value: str) -> tuple[int, int]:
    try:
        parts = tuple(
            int(part.strip())
            for part in value.split(",")
        )
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Usare il formato a,b, per esempio 2,5."
        ) from error

    if (
        len(parts) != 2
        or parts[0] == parts[1]
        or any(not 0 <= digit <= 9 for digit in parts)
    ):
        raise argparse.ArgumentTypeError(
            "La coppia deve contenere due cifre distinte 0–9."
        )

    return tuple(sorted(parts))


def one_draw_probability(
    observation: dict[str, object],
) -> float:
    probabilities = observation[
        "completion_probability_within"
    ]

    return float(probabilities["1"])


def select_observations(
    observations: Sequence[dict[str, object]],
    *,
    group: str,
    pair_filter: tuple[int, int] | None,
    wheel: str | None,
    start_target: int | None,
    end_target: int | None,
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []

    for observation in observations:
        missing = tuple(
            sorted(
                int(digit)
                for digit in observation["missing_digits"]
            )
        )

        if len(missing) != 2:
            continue

        probability = one_draw_probability(observation)

        if (
            group == "45.02"
            and round(probability * 100, 2) != 45.02
        ):
            continue

        if (
            pair_filter is not None
            and missing != pair_filter
        ):
            continue

        if (
            wheel is not None
            and str(observation["wheel"]).casefold()
            != wheel.casefold()
        ):
            continue

        target = int(observation["target_draw"])

        if (
            start_target is not None
            and target < start_target
        ):
            continue

        if (
            end_target is not None
            and target > end_target
        ):
            continue

        selected.append(observation)

    return sorted(
        selected,
        key=lambda item: (
            int(item["target_draw"]),
            int(item["wheel_order"]),
        ),
    )


def enrich(
    observation: dict[str, object],
) -> dict[str, object]:
    pair = tuple(
        sorted(
            int(digit)
            for digit in observation["missing_digits"]
        )
    )

    candidates = pair_numbers(pair)
    extracted = {
        int(number)
        for number in observation["target_numbers"]
    }

    hits = tuple(
        number
        for number in candidates
        if number in extracted
    )

    if hits and not observation["completed"]:
        raise ValueError(
            "Incoerenza: un numero-coppia è presente "
            "ma il ciclo non risulta chiuso."
        )

    return {
        **observation,
        "pair": pair,
        "candidate_numbers": candidates,
        "candidate_hits": hits,
        "candidate_probability": (
            candidate_hit_probability(len(candidates))
        ),
    }


def summarize(
    observations: Sequence[dict[str, object]],
) -> dict[str, float | int]:
    if not observations:
        raise ValueError(
            "Nessuna osservazione corrisponde ai filtri."
        )

    cases = len(observations)

    expected_closures = sum(
        one_draw_probability(observation)
        for observation in observations
    )

    observed_closures = sum(
        bool(observation["completed"])
        for observation in observations
    )

    expected_pair_hits = sum(
        float(observation["candidate_probability"])
        for observation in observations
    )

    observed_pair_hits = sum(
        bool(observation["candidate_hits"])
        for observation in observations
    )

    return {
        "cases": cases,
        "expected_closures": expected_closures,
        "observed_closures": observed_closures,
        "expected_pair_hits": expected_pair_hits,
        "observed_pair_hits": observed_pair_hits,
        "expected_pair_hit_rate": (
            expected_pair_hits / cases
        ),
        "observed_pair_hit_rate": (
            observed_pair_hits / cases
        ),
        "expected_closure_share": (
            expected_pair_hits / expected_closures
        ),
        "observed_closure_share": (
            observed_pair_hits / observed_closures
            if observed_closures
            else 0.0
        ),
    }


def render_summary(
    observations: Sequence[dict[str, object]],
    *,
    group: str,
) -> str:
    result = summarize(observations)

    return "\n".join(
        [
            "===== NUMERI FORMATI DALLA COPPIA MANCANTE =====",
            (
                "Gruppo:                    "
                + (
                    "coppie con P1 visualizzata 45,02%"
                    if group == "45.02"
                    else "tutte le coppie mancanti"
                )
            ),
            (
                "Intervallo:                "
                f"{observations[0]['target_draw']}"
                "–"
                f"{observations[-1]['target_draw']}"
            ),
            (
                "Casi con due mancanti:     "
                f"{result['cases']}"
            ),
            (
                "Chiusure attese:           "
                f"{result['expected_closures']:.3f}"
            ),
            (
                "Chiusure osservate:        "
                f"{result['observed_closures']}"
            ),
            (
                "Numeri-coppia attesi:      "
                f"{result['expected_pair_hits']:.3f}"
            ),
            (
                "Numeri-coppia osservati:   "
                f"{result['observed_pair_hits']}"
            ),
            (
                "Tasso specifico atteso:   "
                f"{result['expected_pair_hit_rate']:.2%}"
            ),
            (
                "Tasso specifico osservato:"
                f" {result['observed_pair_hit_rate']:.2%}"
            ),
            (
                "Quota chiusure attesa:     "
                f"{result['expected_closure_share']:.2%}"
            ),
            (
                "Quota chiusure osservata:  "
                f"{result['observed_closure_share']:.2%}"
            ),
            (
                "Scarto hit osservati:      "
                f"{result['observed_pair_hits'] - result['expected_pair_hits']:+.3f}"
            ),
        ]
    )


def render_by_pair(
    observations: Sequence[dict[str, object]],
) -> str:
    groups: dict[
        tuple[int, int],
        list[dict[str, object]],
    ] = defaultdict(list)

    for observation in observations:
        groups[observation["pair"]].append(observation)

    lines = [
        (
            "Coppia  P(chiude)  Candidati  Casi  "
            "Chiusure  Hit ab/ba  Hit attesi  "
            "% casi   % chiusure"
        ),
        (
            "------  ---------  ---------  ----  "
            "--------  ---------  ----------  "
            "-------  ----------"
        ),
    ]

    for pair in sorted(groups):
        rows = groups[pair]
        result = summarize(rows)

        candidates = "/".join(
            f"{number:02d}"
            for number in rows[0]["candidate_numbers"]
        )

        lines.append(
            f"{format_pair(pair):<8}"
            f"{one_draw_probability(rows[0]):>8.2%}  "
            f"{candidates:<11}"
            f"{result['cases']:>4}  "
            f"{result['observed_closures']:>8}  "
            f"{result['observed_pair_hits']:>9}  "
            f"{result['expected_pair_hits']:>10.2f}  "
            f"{result['observed_pair_hit_rate']:>7.2%}  "
            f"{result['observed_closure_share']:>10.2%}"
        )

    return "\n".join(lines)


def render_hits(
    observations: Sequence[dict[str, object]],
) -> str:
    hits = [
        observation
        for observation in observations
        if observation["candidate_hits"]
    ]

    if not hits:
        return "Nessun numero-coppia osservato."

    lines = [
        (
            "Target  Data        Ruota       Coppia  "
            "Candidati  Numeri estratti       Hit"
        ),
        (
            "------  ----------  ----------  ------  "
            "---------  --------------------  -----"
        ),
    ]

    for observation in hits:
        candidates = "/".join(
            f"{number:02d}"
            for number in observation["candidate_numbers"]
        )

        matched = "/".join(
            f"{number:02d}"
            for number in observation["candidate_hits"]
        )

        lines.append(
            f"{int(observation['target_draw']):<8}"
            f"{str(observation['target_date']):<12}"
            f"{str(observation['wheel']):<12}"
            f"{format_pair(observation['pair']):<8}"
            f"{candidates:<11}"
            f"{format_numbers(observation['target_numbers']):<22}"
            f"{matched}"
        )

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica se le due cifre mancanti compaiono "
            "insieme come numero ab o ba."
        ),
        epilog=(
            "Esempio: "
            "python3 analyze_missing_pair_numbers.py "
            "--show-hits | less -S"
        ),
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"Replay JSON. Default: {DEFAULT_REPORT}",
    )

    parser.add_argument(
        "--group",
        choices=("45.02", "all"),
        default="45.02",
        help=(
            "Analizza soltanto le coppie visualizzate "
            "al 45,02%% oppure tutte. Default: 45.02."
        ),
    )

    parser.add_argument(
        "--pair",
        type=parse_pair,
        help="Limita l'analisi a una coppia, per esempio 2,5.",
    )

    parser.add_argument(
        "--wheel",
        help="Limita l'analisi a una ruota.",
    )

    parser.add_argument(
        "--start-target",
        type=int,
        help="Primo concorso incluso.",
    )

    parser.add_argument(
        "--end-target",
        type=int,
        help="Ultimo concorso incluso.",
    )

    parser.add_argument(
        "--show-hits",
        action="store_true",
        help="Elenca tutti i concorsi con numero ab o ba.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        raw = load_observations(args.report)

        selected = select_observations(
            raw,
            group=args.group,
            pair_filter=args.pair,
            wheel=args.wheel,
            start_target=args.start_target,
            end_target=args.end_target,
        )

        enriched = [
            enrich(observation)
            for observation in selected
        ]

        print(
            render_summary(
                enriched,
                group=args.group,
            )
        )

        print()
        print("===== DETTAGLIO PER COPPIA =====")
        print(render_by_pair(enriched))

        if args.show_hits:
            print()
            print("===== CONCORSI CON NUMERO-COPPIA =====")
            print(render_hits(enriched))

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
