"""Segnale operativo corrente basato sui coverage-hits storici."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from strategies.coverage_completion import (
    CurrentCoverageState,
)
from strategies.coverage_hit_statistics import (
    required_hit_count,
    theoretical_threshold_probability,
)
from strategies.coverage_markov import maturity_metrics


DEFAULT_HISTORICAL_SUMMARY = Path(
    "artifacts/coverage-hits/"
    "coverage-hits-1871-2025.csv"
)

_REQUIRED_COLUMNS = frozenset({
    "top",
    "missing",
    "threshold",
    "cases",
    "obtained",
    "expected_probability",
    "evidence_level",
})


@dataclass(frozen=True)
class HistoricalCoverageClass:
    """Evidenza storica di una classe TOP/mancanti."""

    most_present_count: int
    missing_count: int
    threshold: int
    cases: int
    obtained: int
    expected_probability: float
    evidence_level: str

    @property
    def success_rate(self) -> float:
        """Frequenza osservata del raggiungimento della soglia."""

        if self.cases <= 0:
            return 0.0

        return self.obtained / self.cases

    @property
    def excess(self) -> float:
        """Scarto medio osservato rispetto all'attesa teorica."""

        return (
            self.success_rate
            - self.expected_probability
        )


@dataclass(frozen=True)
class CurrentCoverageSignal:
    """Valutazione corrente corretta con l'evidenza storica."""

    wheel: str
    wheel_order: int
    draws_in_cycle: int
    most_present_digits: frozenset[int]
    missing_digits: frozenset[int]
    historical: HistoricalCoverageClass
    current_event_probability: float
    completion_within_one: float
    lower_success_bound: float
    conservative_excess: float
    conservative_probability: float

    @property
    def class_label(self) -> str:
        """Etichetta quantità TOP, quantità mancanti."""

        return (
            f"{len(self.most_present_digits)},"
            f"{len(self.missing_digits)}"
        )


def wilson_lower_bound(
    successes: int,
    attempts: int,
    *,
    z: float = 1.959963984540054,
) -> float:
    """Limite inferiore Wilson bilaterale al livello indicato."""

    if (
        not isinstance(successes, int)
        or isinstance(successes, bool)
        or successes < 0
    ):
        raise ValueError(
            "successes deve essere un intero non negativo."
        )

    if (
        not isinstance(attempts, int)
        or isinstance(attempts, bool)
        or attempts <= 0
    ):
        raise ValueError(
            "attempts deve essere un intero positivo."
        )

    if successes > attempts:
        raise ValueError(
            "successes non può superare attempts."
        )

    proportion = successes / attempts
    z_squared = z * z
    denominator = 1.0 + z_squared / attempts

    centre = (
        proportion
        + z_squared / (2.0 * attempts)
    ) / denominator

    radius = (
        z
        * math.sqrt(
            (
                proportion
                * (1.0 - proportion)
                / attempts
            )
            + (
                z_squared
                / (4.0 * attempts * attempts)
            )
        )
        / denominator
    )

    return max(
        0.0,
        centre - radius,
    )


def load_historical_coverage_classes(
    path: Path,
) -> dict[
    tuple[int, int],
    HistoricalCoverageClass,
]:
    """Carica e valida il riepilogo storico delle classi."""

    with path.open(
        encoding="utf-8",
        newline="",
    ) as stream:
        reader = csv.DictReader(stream)
        columns = frozenset(
            reader.fieldnames or ()
        )
        missing_columns = (
            _REQUIRED_COLUMNS - columns
        )

        if missing_columns:
            raise ValueError(
                "Colonne mancanti nel riepilogo "
                f"coverage-hits: "
                f"{sorted(missing_columns)}."
            )

        classes: dict[
            tuple[int, int],
            HistoricalCoverageClass,
        ] = {}

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            item = HistoricalCoverageClass(
                most_present_count=int(
                    row["top"]
                ),
                missing_count=int(
                    row["missing"]
                ),
                threshold=int(
                    row["threshold"]
                ),
                cases=int(row["cases"]),
                obtained=int(row["obtained"]),
                expected_probability=float(
                    row["expected_probability"]
                ),
                evidence_level=(
                    row["evidence_level"]
                ),
            )

            if item.cases <= 0:
                raise ValueError(
                    f"Riga {row_number}: cases "
                    "deve essere positivo."
                )

            if not 0 <= item.obtained <= item.cases:
                raise ValueError(
                    f"Riga {row_number}: obtained "
                    "fuori intervallo."
                )

            expected_threshold = (
                required_hit_count(
                    item.missing_count
                )
            )

            if item.threshold != expected_threshold:
                raise ValueError(
                    f"Riga {row_number}: soglia "
                    f"{item.threshold} non coerente "
                    f"con {item.missing_count} "
                    "cifre mancanti."
                )

            key = (
                item.most_present_count,
                item.missing_count,
            )

            if key in classes:
                raise ValueError(
                    "Classe coverage-hits duplicata: "
                    f"{key[0]},{key[1]}."
                )

            classes[key] = item

    return classes


def build_current_coverage_signals(
    states: Sequence[CurrentCoverageState],
    historical_classes: Mapping[
        tuple[int, int],
        HistoricalCoverageClass,
    ],
) -> tuple[CurrentCoverageSignal, ...]:
    """Incrocia gli stati correnti con le classi storiche."""

    signals: list[CurrentCoverageSignal] = []

    for state in states:
        key = (
            len(state.most_present_digits),
            len(state.missing_digits),
        )
        historical = historical_classes.get(
            key
        )

        if historical is None:
            continue

        threshold = required_hit_count(
            len(state.missing_digits)
        )

        if historical.threshold != threshold:
            raise ValueError(
                "Soglia storica non coerente "
                f"per la classe {key[0]},{key[1]}."
            )

        current_event_probability = (
            theoretical_threshold_probability(
                state.missing_digits
            )
        )

        completion_within_one = float(
            maturity_metrics(
                state.missing_digits,
                horizons=(1,),
            )["completion_within"][1]
        )

        lower_success_bound = (
            wilson_lower_bound(
                historical.obtained,
                historical.cases,
            )
        )

        conservative_excess = (
            lower_success_bound
            - historical.expected_probability
        )

        conservative_probability = min(
            1.0,
            max(
                0.0,
                current_event_probability
                + conservative_excess,
            ),
        )

        signals.append(
            CurrentCoverageSignal(
                wheel=state.wheel,
                wheel_order=state.wheel_order,
                draws_in_cycle=(
                    state.draws_in_cycle
                ),
                most_present_digits=(
                    state.most_present_digits
                ),
                missing_digits=(
                    state.missing_digits
                ),
                historical=historical,
                current_event_probability=(
                    current_event_probability
                ),
                completion_within_one=(
                    completion_within_one
                ),
                lower_success_bound=(
                    lower_success_bound
                ),
                conservative_excess=(
                    conservative_excess
                ),
                conservative_probability=(
                    conservative_probability
                ),
            )
        )

    return tuple(
        sorted(
            signals,
            key=lambda signal: (
                -signal.conservative_probability,
                -signal.historical.cases,
                signal.wheel_order,
                signal.wheel,
            ),
        )
    )


def format_digits(
    digits: frozenset[int],
) -> str:
    """Formatta un insieme ordinato di cifre."""

    return (
        "{"
        + ",".join(
            str(digit)
            for digit in sorted(digits)
        )
        + "}"
    )


def print_coverage_hit_signal(
    states: Sequence[CurrentCoverageState],
    *,
    summary_path: Path = (
        DEFAULT_HISTORICAL_SUMMARY
    ),
) -> None:
    """Stampa il ranking operativo corretto con lo storico."""

    historical_classes = (
        load_historical_coverage_classes(
            summary_path
        )
    )
    signals = build_current_coverage_signals(
        states,
        historical_classes,
    )

    print()
    print(
        "===== SEGNALE OPERATIVO "
        "COVERAGE-HITS ====="
    )
    print(f"Fonte storica: {summary_path}")
    print(
        "Evento: almeno max(1, N-1) delle N "
        "cifre mancanti alla prossima estrazione."
    )
    print(
        "Stima95-: probabilità corrente corretta "
        "con il limite inferiore Wilson dello "
        "scarto storico."
    )
    print(
        "Età è descrittiva e non incrementa "
        "la probabilità."
    )

    if not signals:
        print()
        print(
            "Nessuna classe corrente presente "
            "nel riepilogo storico."
        )
        return

    print()
    print(
        f"{'Pos':<5}"
        f"{'Ruota':<12}"
        f"{'Classe':<9}"
        f"{'Età':<5}"
        f"{'Più presenti':<18}"
        f"{'Mancanti':<18}"
        f"{'Casi':>7}  "
        f"{'Storico':>8}  "
        f"{'P evento':>8}  "
        f"{'Lift95-':>8}  "
        f"{'Entro 1':>8}  "
        f"{'Stima95-':>8}"
    )
    print(
        f"{'---':<5}"
        f"{'----------':<12}"
        f"{'-------':<9}"
        f"{'---':<5}"
        f"{'-------------':<18}"
        f"{'-------------':<18}"
        f"{'------':>7}  "
        f"{'--------':>8}  "
        f"{'--------':>8}  "
        f"{'--------':>8}  "
        f"{'--------':>8}  "
        f"{'--------':>8}"
    )

    for position, signal in enumerate(
        signals,
        start=1,
    ):
        print(
            f"{position:<5}"
            f"{signal.wheel:<12}"
            f"{signal.class_label:<9}"
            f"{signal.draws_in_cycle:<5}"
            f"{format_digits(signal.most_present_digits):<18}"
            f"{format_digits(signal.missing_digits):<18}"
            f"{signal.historical.cases:>7}  "
            f"{signal.historical.success_rate:>8.2%}  "
            f"{signal.current_event_probability:>8.2%}  "
            f"{signal.conservative_excess:>+8.2%}  "
            f"{signal.completion_within_one:>8.2%}  "
            f"{signal.conservative_probability:>8.2%}"
        )

    winner = signals[0]

    print()
    print(
        f"Primo segnale: {winner.wheel}, "
        f"classe {winner.class_label}; "
        f"almeno {winner.historical.threshold} tra "
        f"{format_digits(winner.missing_digits)}; "
        f"più presenti "
        f"{format_digits(winner.most_present_digits)}; "
        f"Stima95- "
        f"{winner.conservative_probability:.2%}."
    )
    print(
        "Nota: un lift negativo non indica un "
        "vantaggio storico; la classifica descrive "
        "il segnale operativo più robusto disponibile."
    )
