#!/usr/bin/env python3

"""Confronta il kernel Markov con l'enumeratore indipendente."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategies.coverage_markov import (
    transition_distribution,
)
from strategies.coverage_transition_enumerator import (
    TOTAL_DRAW_COMBINATIONS,
    all_digit_states,
    draw_digit_mask_counts,
    transition_probability_distribution,
)


DEFAULT_TOLERANCE = 1e-12
DEFAULT_OUTPUT = Path(
    "_work/transition-kernel-verification.json"
)


def canonical_state(
    state: frozenset[int],
) -> list[int]:
    return sorted(state)


def verify_kernel(
    tolerance: float,
) -> dict[str, object]:
    if tolerance <= 0.0:
        raise ValueError(
            "La tolleranza deve essere positiva."
        )

    states = all_digit_states()

    discrepancies: list[
        dict[str, object]
    ] = []

    transition_entries = 0
    maximum_error = 0.0
    maximum_model_normalization_error = 0.0
    worst_case: dict[str, object] | None = None

    for current_state in states:
        enumerated = (
            transition_probability_distribution(
                current_state
            )
        )

        modelled = transition_distribution(
            current_state
        )

        model_normalization_error = abs(
            sum(modelled.values()) - 1.0
        )

        maximum_model_normalization_error = max(
            maximum_model_normalization_error,
            model_normalization_error,
        )

        next_states = sorted(
            set(enumerated) | set(modelled),
            key=lambda state: (
                len(state),
                tuple(sorted(state)),
            ),
        )

        transition_entries += len(next_states)

        for next_state in next_states:
            exact_probability = enumerated.get(
                next_state,
                0.0,
            )

            model_probability = modelled.get(
                next_state,
                0.0,
            )

            error = abs(
                exact_probability
                - model_probability
            )

            if error > maximum_error:
                maximum_error = error

                worst_case = {
                    "current_state": (
                        canonical_state(
                            current_state
                        )
                    ),
                    "next_state": (
                        canonical_state(
                            next_state
                        )
                    ),
                    "enumerated_probability": (
                        exact_probability
                    ),
                    "model_probability": (
                        model_probability
                    ),
                    "absolute_error": error,
                }

            if error > tolerance:
                discrepancies.append(
                    {
                        "current_state": (
                            canonical_state(
                                current_state
                            )
                        ),
                        "next_state": (
                            canonical_state(
                                next_state
                            )
                        ),
                        "enumerated_probability": (
                            exact_probability
                        ),
                        "model_probability": (
                            model_probability
                        ),
                        "absolute_error": error,
                    }
                )

    return {
        "report_type": (
            "transition-kernel-verification"
        ),
        "methodology": (
            "Independent dynamic-programming enumeration "
            "of five-number combinations by observed "
            "digit-union mask."
        ),
        "states_verified": len(states),
        "draw_combinations": (
            TOTAL_DRAW_COMBINATIONS
        ),
        "observed_digit_mask_classes": len(
            draw_digit_mask_counts()
        ),
        "transition_entries_compared": (
            transition_entries
        ),
        "tolerance": tolerance,
        "maximum_absolute_error": (
            maximum_error
        ),
        "maximum_model_normalization_error": (
            maximum_model_normalization_error
        ),
        "discrepancy_count": len(
            discrepancies
        ),
        "worst_case": worst_case,
        "discrepancies": discrepancies,
        "verified": not discrepancies,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica tutti i 1.024 stati del kernel "
            "Markov con un enumeratore indipendente."
        )
    )

    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE,
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
        report = verify_kernel(
            args.tolerance
        )

        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.output.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        print(
            "===== VERIFICA INDIPENDENTE "
            "DEL KERNEL ====="
        )
        print(
            "Metodo:               "
            "DP esatta sulle maschere di cifre"
        )
        print(
            "Combinazioni:         "
            f"{report['draw_combinations']}"
        )
        print(
            "Maschere osservate:   "
            f"{report['observed_digit_mask_classes']}"
        )
        print(
            "Stati verificati:     "
            f"{report['states_verified']}"
        )
        print(
            "Transizioni:          "
            f"{report['transition_entries_compared']}"
        )
        print(
            "Tolleranza:           "
            f"{report['tolerance']:.1e}"
        )
        print(
            "Errore massimo:       "
            f"{report['maximum_absolute_error']:.3e}"
        )
        print(
            "Errore normalizzazione:"
            f" {report[
                'maximum_model_normalization_error'
            ]:.3e}"
        )
        print(
            "Discrepanze:          "
            f"{report['discrepancy_count']}"
        )
        print(
            "Esito:                "
            + (
                "VERIFICATO"
                if report["verified"]
                else "FALLITO"
            )
        )
        print(
            f"Rapporto JSON:        {args.output}"
        )

        return (
            0
            if report["verified"]
            else 1
        )

    except (
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
    ) as error:
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
