#!/usr/bin/env python3

"""Screening controllato dei residui prequentiali sul campione 2023."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Callable, Sequence

from analyze_one_shot_momentum import (
    format_digits,
    load_report,
    one_draw_probability,
    poisson_binomial_p_values,
)


MIN_PROMOTION_CASES = 30
MAX_PROMOTION_Q = 0.05
MIN_EXACT_STATE_CASES = 30

FAMILY_ORDER = (
    "wheel",
    "missing_count",
    "single_missing_digit",
    "contains_nine",
    "cycle_age",
    "exact_missing_state",
)

FAMILY_TITLES = {
    "wheel": "RUOTA",
    "missing_count": "NUMERO DI CIFRE MANCANTI",
    "single_missing_digit": "IDENTITÀ DELLA SINGOLA CIFRA MANCANTE",
    "contains_nine": "PRESENZA DELLA CIFRA 9",
    "cycle_age": "ETÀ DEL CICLO",
    "exact_missing_state": "STATO MANCANTE ESATTO",
}


@dataclass(frozen=True)
class GroupResult:
    family: str
    group: str
    cases: int
    expected: float
    observed: int
    expected_rate: float
    observed_rate: float
    delta_rate: float
    residual_sum: float
    variance_sum: float
    z_score: float
    p_two_sided: float
    q_value: float
    first_cases: int
    first_residual: float
    second_cases: int
    second_residual: float
    stable_direction: bool
    qualifies_for_promotion: bool


def age_bucket(age: int) -> str:
    if age < 0:
        raise ValueError(
            "L'età del ciclo non può essere negativa."
        )

    return str(age) if age <= 4 else "5+"


def observation_features(
    observation: dict[str, object],
) -> dict[str, str | None]:
    missing_digits = tuple(
        sorted(
            int(digit)
            for digit in observation["missing_digits"]
        )
    )

    return {
        "wheel": str(observation["wheel"]),
        "missing_count": str(len(missing_digits)),
        "single_missing_digit": (
            str(missing_digits[0])
            if len(missing_digits) == 1
            else None
        ),
        "contains_nine": (
            "yes"
            if 9 in missing_digits
            else "no"
        ),
        "cycle_age": age_bucket(
            int(observation["cycle_age"])
        ),
        "exact_missing_state": format_digits(
            missing_digits
        ),
    }


def split_target_sets(
    observations: Sequence[dict[str, object]],
) -> tuple[set[int], set[int]]:
    targets = sorted(
        {
            int(observation["target_draw"])
            for observation in observations
        }
    )

    if len(targets) < 2:
        raise ValueError(
            "Servono almeno due concorsi per la divisione temporale."
        )

    split_index = len(targets) // 2

    return (
        set(targets[:split_index]),
        set(targets[split_index:]),
    )


def residual_sum(
    observations: Sequence[dict[str, object]],
) -> float:
    return sum(
        float(bool(observation["completed"]))
        - one_draw_probability(observation)
        for observation in observations
    )


def variance_sum(
    observations: Sequence[dict[str, object]],
) -> float:
    return sum(
        (
            probability
            * (1.0 - probability)
        )
        for probability in (
            one_draw_probability(observation)
            for observation in observations
        )
    )


def same_nonzero_direction(
    first: float,
    second: float,
    *,
    epsilon: float = 1e-12,
) -> bool:
    if abs(first) <= epsilon:
        return False

    if abs(second) <= epsilon:
        return False

    return first * second > 0.0


def benjamini_hochberg(
    p_values: Sequence[float],
) -> tuple[float, ...]:
    if any(
        not 0.0 <= value <= 1.0
        for value in p_values
    ):
        raise ValueError(
            "I p-value devono essere compresi tra zero e uno."
        )

    count = len(p_values)

    if count == 0:
        return ()

    ranked = sorted(
        enumerate(p_values),
        key=lambda item: item[1],
    )

    adjusted_ranked = [1.0] * count
    running_minimum = 1.0

    for reverse_index in range(
        count - 1,
        -1,
        -1,
    ):
        original_index, p_value = ranked[
            reverse_index
        ]
        rank = reverse_index + 1

        adjusted = min(
            1.0,
            p_value * count / rank,
        )

        running_minimum = min(
            running_minimum,
            adjusted,
        )

        adjusted_ranked[reverse_index] = (
            running_minimum
        )

    result = [1.0] * count

    for ranked_index, (
        original_index,
        _,
    ) in enumerate(ranked):
        result[original_index] = (
            adjusted_ranked[ranked_index]
        )

    return tuple(result)


def build_family_groups(
    observations: Sequence[dict[str, object]],
    family: str,
) -> dict[str, list[dict[str, object]]]:
    if family not in FAMILY_ORDER:
        raise ValueError(
            f"Famiglia sconosciuta: {family}"
        )

    groups: dict[
        str,
        list[dict[str, object]],
    ] = defaultdict(list)

    for observation in observations:
        value = observation_features(
            observation
        )[family]

        if value is None:
            continue

        groups[value].append(observation)

    if family == "exact_missing_state":
        groups = defaultdict(
            list,
            {
                group: rows
                for group, rows in groups.items()
                if len(rows)
                >= MIN_EXACT_STATE_CASES
            },
        )

    return dict(groups)


def compute_group_result(
    *,
    family: str,
    group: str,
    observations: Sequence[dict[str, object]],
    first_targets: set[int],
    second_targets: set[int],
) -> GroupResult:
    if not observations:
        raise ValueError(
            "Un gruppo non può essere vuoto."
        )

    probabilities = tuple(
        one_draw_probability(observation)
        for observation in observations
    )

    expected = sum(probabilities)
    observed = sum(
        bool(observation["completed"])
        for observation in observations
    )

    group_residual = observed - expected
    group_variance = sum(
        probability * (1.0 - probability)
        for probability in probabilities
    )

    z_score = (
        group_residual
        / math.sqrt(group_variance)
        if group_variance > 0.0
        else 0.0
    )

    _, p_two_sided = poisson_binomial_p_values(
        probabilities,
        int(observed),
    )

    first_rows = tuple(
        observation
        for observation in observations
        if int(observation["target_draw"])
        in first_targets
    )

    second_rows = tuple(
        observation
        for observation in observations
        if int(observation["target_draw"])
        in second_targets
    )

    first_group_residual = residual_sum(
        first_rows
    )
    second_group_residual = residual_sum(
        second_rows
    )

    stable = same_nonzero_direction(
        first_group_residual,
        second_group_residual,
    )

    cases = len(observations)

    return GroupResult(
        family=family,
        group=group,
        cases=cases,
        expected=expected,
        observed=int(observed),
        expected_rate=expected / cases,
        observed_rate=observed / cases,
        delta_rate=(
            observed / cases
            - expected / cases
        ),
        residual_sum=group_residual,
        variance_sum=group_variance,
        z_score=z_score,
        p_two_sided=p_two_sided,
        q_value=1.0,
        first_cases=len(first_rows),
        first_residual=first_group_residual,
        second_cases=len(second_rows),
        second_residual=second_group_residual,
        stable_direction=stable,
        qualifies_for_promotion=False,
    )


def apply_family_q_values(
    results: Sequence[GroupResult],
) -> tuple[GroupResult, ...]:
    q_values = benjamini_hochberg(
        tuple(
            result.p_two_sided
            for result in results
        )
    )

    adjusted: list[GroupResult] = []

    for result, q_value in zip(
        results,
        q_values,
    ):
        qualifies = (
            result.cases >= MIN_PROMOTION_CASES
            and q_value <= MAX_PROMOTION_Q
            and result.stable_direction
        )

        adjusted.append(
            replace(
                result,
                q_value=q_value,
                qualifies_for_promotion=qualifies,
            )
        )

    return tuple(adjusted)


def group_sort_key(
    family: str,
    group: str,
) -> tuple[int, object]:
    if family == "wheel":
        wheel_order = {
            "Bari": 0,
            "Cagliari": 1,
            "Firenze": 2,
            "Genova": 3,
            "Milano": 4,
            "Napoli": 5,
            "Palermo": 6,
            "Roma": 7,
            "Torino": 8,
            "Venezia": 9,
            "Nazionale": 10,
        }
        return (0, wheel_order.get(group, 999))

    if family in (
        "missing_count",
        "single_missing_digit",
    ):
        return (0, int(group))

    if family == "contains_nine":
        return (
            0,
            0 if group == "no" else 1,
        )

    if family == "cycle_age":
        return (
            0,
            5 if group == "5+" else int(group),
        )

    return (0, group)


def analyze_family(
    observations: Sequence[dict[str, object]],
    *,
    family: str,
    first_targets: set[int],
    second_targets: set[int],
) -> tuple[GroupResult, ...]:
    groups = build_family_groups(
        observations,
        family,
    )

    raw_results = tuple(
        compute_group_result(
            family=family,
            group=group,
            observations=rows,
            first_targets=first_targets,
            second_targets=second_targets,
        )
        for group, rows in sorted(
            groups.items(),
            key=lambda item: group_sort_key(
                family,
                item[0],
            ),
        )
    )

    return apply_family_q_values(
        raw_results
    )


def analyze_discovery(
    observations: Sequence[dict[str, object]],
) -> tuple[
    dict[str, tuple[GroupResult, ...]],
    set[int],
    set[int],
]:
    first_targets, second_targets = (
        split_target_sets(observations)
    )

    results = {
        family: analyze_family(
            observations,
            family=family,
            first_targets=first_targets,
            second_targets=second_targets,
        )
        for family in FAMILY_ORDER
    }

    return (
        results,
        first_targets,
        second_targets,
    )


def promotion_candidates(
    results: dict[
        str,
        tuple[GroupResult, ...],
    ],
) -> tuple[GroupResult, ...]:
    candidates = [
        result
        for family_results in results.values()
        for result in family_results
        if result.qualifies_for_promotion
    ]

    family_positions = {
        family: index
        for index, family
        in enumerate(FAMILY_ORDER)
    }

    return tuple(
        sorted(
            candidates,
            key=lambda result: (
                result.q_value,
                -abs(result.z_score),
                family_positions[result.family],
                result.group,
            ),
        )
    )


def render_family(
    family: str,
    results: Sequence[GroupResult],
) -> str:
    lines = [
        f"===== {FAMILY_TITLES[family]} =====",
        "",
        (
            "Gruppo                    Casi  Attese  Reali  "
            "Delta     Z       p       q       "
            "Residuo 1ª  Residuo 2ª  Stabile  Promuov."
        ),
        (
            "------------------------  ----  ------  -----  "
            "--------  ------  ------  ------  "
            "----------  ----------  -------  --------"
        ),
    ]

    if not results:
        lines.append(
            "Nessun gruppo eleggibile."
        )
        return "\n".join(lines)

    for result in results:
        lines.append(
            f"{result.group:<26}"
            f"{result.cases:<6}"
            f"{result.expected:>6.2f}  "
            f"{result.observed:>5}  "
            f"{result.delta_rate:>+7.2%}  "
            f"{result.z_score:>+6.2f}  "
            f"{result.p_two_sided:>6.4f}  "
            f"{result.q_value:>6.4f}  "
            f"{result.first_residual:>+10.2f}  "
            f"{result.second_residual:>+10.2f}  "
            f"{'sì' if result.stable_direction else 'no':>7}  "
            f"{'SÌ' if result.qualifies_for_promotion else 'no':>8}"
        )

    return "\n".join(lines)


def render_promotion_summary(
    candidates: Sequence[GroupResult],
) -> str:
    lines = [
        "===== ESITO DEL PROTOCOLLO =====",
        "",
    ]

    if not candidates:
        lines.extend(
            [
                "Nessun candidato soddisfa tutti i requisiti:",
                "",
                "- almeno 30 osservazioni;",
                "- q-value <= 0,05;",
                "- stessa direzione nelle due metà del 2023.",
                "",
                "Esito: nessuna ipotesi da promuovere sul 2022.",
            ]
        )
        return "\n".join(lines)

    if len(candidates) == 1:
        candidate = candidates[0]

        lines.extend(
            [
                "Un solo candidato soddisfa il protocollo:",
                "",
                (
                    f"- famiglia: {candidate.family};"
                ),
                (
                    f"- gruppo: {candidate.group};"
                ),
                (
                    f"- casi: {candidate.cases};"
                ),
                (
                    f"- delta: {candidate.delta_rate:+.2%};"
                ),
                (
                    f"- z: {candidate.z_score:+.3f};"
                ),
                (
                    f"- q-value: {candidate.q_value:.4f}."
                ),
                "",
                (
                    "Esito: il candidato può essere trasformato "
                    "in una regola congelata prima di importare il 2022."
                ),
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            (
                f"{len(candidates)} candidati soddisfano "
                "formalmente il protocollo:"
            ),
            "",
        ]
    )

    for candidate in candidates:
        lines.append(
            "- "
            f"{candidate.family} / {candidate.group}: "
            f"casi {candidate.cases}, "
            f"delta {candidate.delta_rate:+.2%}, "
            f"z {candidate.z_score:+.3f}, "
            f"q {candidate.q_value:.4f}"
        )

    lines.extend(
        [
            "",
            (
                "Il protocollo non definisce un criterio di spareggio. "
                "Nessuna selezione viene effettuata automaticamente."
            ),
        ]
    )

    return "\n".join(lines)


def build_json_report(
    *,
    source_report: Path,
    report_label: str,
    results: dict[
        str,
        tuple[GroupResult, ...],
    ],
    first_targets: set[int],
    second_targets: set[int],
) -> dict[str, object]:
    candidates = promotion_candidates(
        results
    )

    return {
        "report_type": "residual-discovery-screen",
        "protocol": (
            "docs/residual-discovery-protocol.md"
        ),
        "source_report": str(source_report),
        "source_label": report_label,
        "parameters": {
            "minimum_promotion_cases": (
                MIN_PROMOTION_CASES
            ),
            "maximum_promotion_q": (
                MAX_PROMOTION_Q
            ),
            "minimum_exact_state_cases": (
                MIN_EXACT_STATE_CASES
            ),
            "multiple_testing": (
                "Benjamini-Hochberg within family"
            ),
            "nominal_test": (
                "exact Poisson-binomial two-sided"
            ),
        },
        "temporal_split": {
            "first_target_start": min(
                first_targets
            ),
            "first_target_end": max(
                first_targets
            ),
            "first_target_count": len(
                first_targets
            ),
            "second_target_start": min(
                second_targets
            ),
            "second_target_end": max(
                second_targets
            ),
            "second_target_count": len(
                second_targets
            ),
        },
        "families": {
            family: [
                asdict(result)
                for result in family_results
            ]
            for family, family_results
            in results.items()
        },
        "promotion_candidates": [
            asdict(candidate)
            for candidate in candidates
        ],
        "automatic_selection": (
            asdict(candidates[0])
            if len(candidates) == 1
            else None
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Esegue lo screening controllato dei residui "
            "prequentiali secondo il protocollo congelato."
        )
    )

    parser.add_argument(
        "report",
        type=Path,
        help=(
            "Replay prequentiale JSON del campione "
            "di scoperta."
        ),
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "_work/residual-discovery-2023.json"
        ),
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        report_label, observations = load_report(
            args.report
        )

        (
            results,
            first_targets,
            second_targets,
        ) = analyze_discovery(observations)

        print("===== RESIDUAL DISCOVERY SCREEN =====")
        print(f"Replay:               {args.report}")
        print(f"Campione:             {report_label}")
        print(
            f"Osservazioni:         {len(observations)}"
        )
        print(
            "Prima metà:           "
            f"{min(first_targets)}–{max(first_targets)} "
            f"({len(first_targets)} concorsi)"
        )
        print(
            "Seconda metà:         "
            f"{min(second_targets)}–{max(second_targets)} "
            f"({len(second_targets)} concorsi)"
        )
        print(
            "Test nominale:        "
            "Poisson-binomial esatto, bilaterale"
        )
        print(
            "Correzione multipla:  "
            "Benjamini–Hochberg entro famiglia"
        )

        for family in FAMILY_ORDER:
            print()
            print(
                render_family(
                    family,
                    results[family],
                )
            )

        candidates = promotion_candidates(
            results
        )

        print()
        print(
            render_promotion_summary(
                candidates
            )
        )

        document = build_json_report(
            source_report=args.report,
            report_label=report_label,
            results=results,
            first_targets=first_targets,
            second_targets=second_targets,
        )

        args.json_output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.json_output.write_text(
            json.dumps(
                document,
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
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
