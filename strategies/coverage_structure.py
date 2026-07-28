"""Struttura e simmetrie del processo di copertura."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from strategies.coverage_completion import (
    digits_in_number,
    normalize_digits,
)
from strategies.coverage_markov import (
    DigitState,
    transition_distribution,
)


ALL_DIGITS = frozenset(range(10))
NON_NINE_DIGITS = frozenset(range(9))
MIDDLE_DIGITS = frozenset(range(1, 9))


@dataclass(frozen=True, order=True)
class StateSymmetryClass:
    """
    Classe strutturale di uno stato mancante.

    Families:

    absorbing:
        stato vuoto;

    no-nine:
        stato che non contiene 9; tutte le cifre 0–8
        sono intercambiabili nel sottoprocesso;

    nine-no-zero:
        stato contenente 9 ma non 0; le cifre 1–8
        sono intercambiabili;

    zero-nine:
        stato contenente sia 0 sia 9; le cifre 1–8
        sono intercambiabili.
    """

    family: str
    exchangeable_count: int

    @property
    def missing_count(self) -> int:
        if self.family == "absorbing":
            return 0

        if self.family == "no-nine":
            return self.exchangeable_count

        if self.family == "nine-no-zero":
            return self.exchangeable_count + 1

        if self.family == "zero-nine":
            return self.exchangeable_count + 2

        raise RuntimeError(
            f"Famiglia strutturale sconosciuta: {self.family}."
        )

    @property
    def canonical_state(self) -> DigitState:
        if self.family == "absorbing":
            return frozenset()

        if self.family == "no-nine":
            return frozenset(
                range(self.exchangeable_count)
            )

        if self.family == "nine-no-zero":
            return frozenset(
                (
                    *range(
                        1,
                        self.exchangeable_count + 1,
                    ),
                    9,
                )
            )

        if self.family == "zero-nine":
            return frozenset(
                (
                    0,
                    *range(
                        1,
                        self.exchangeable_count + 1,
                    ),
                    9,
                )
            )

        raise RuntimeError(
            f"Famiglia strutturale sconosciuta: {self.family}."
        )


@dataclass(frozen=True)
class StructuralVerificationSummary:
    forbidden_states_checked: int
    markov_states_checked: int
    nonempty_symmetry_classes: int
    transition_entries_compared: int
    maximum_transition_error: float


def all_digit_states(
    *,
    include_empty: bool = True,
) -> tuple[DigitState, ...]:
    start = 0 if include_empty else 1

    return tuple(
        frozenset(
            digit
            for digit in range(10)
            if mask & (1 << digit)
        )
        for mask in range(start, 1 << 10)
    )


def allowed_number_count_closed_form(
    forbidden_digits: Iterable[int],
) -> int:
    """
    Conta i numeri di 01–90 che evitano le cifre vietate.

    Si parte dalle coppie ordinate delle cifre ammesse.

    Da queste si eliminano:

    - 00, quando lo zero è ammesso;
    - 91–99, limitatamente alle unità ammesse,
      quando il nove è ammesso.
    """

    forbidden = frozenset(
        normalize_digits(forbidden_digits)
    )

    allowed_digit_count = (
        10 - len(forbidden)
    )

    zero_is_allowed = 0 not in forbidden
    nine_is_allowed = 9 not in forbidden

    invalid_zero_number = (
        1 if zero_is_allowed else 0
    )

    invalid_numbers_above_ninety = (
        allowed_digit_count
        - int(zero_is_allowed)
        if nine_is_allowed
        else 0
    )

    return (
        allowed_digit_count**2
        - invalid_zero_number
        - invalid_numbers_above_ninety
    )


def allowed_number_count_enumerated(
    forbidden_digits: Iterable[int],
) -> int:
    forbidden = frozenset(
        normalize_digits(forbidden_digits)
    )

    return sum(
        digits_in_number(number).isdisjoint(
            forbidden
        )
        for number in range(1, 91)
    )


def state_symmetry_class(
    missing_digits: Iterable[int],
) -> StateSymmetryClass:
    state = frozenset(
        normalize_digits(missing_digits)
    )

    if not state:
        return StateSymmetryClass(
            family="absorbing",
            exchangeable_count=0,
        )

    if 9 not in state:
        return StateSymmetryClass(
            family="no-nine",
            exchangeable_count=len(state),
        )

    middle_count = len(
        state.intersection(MIDDLE_DIGITS)
    )

    if 0 in state:
        return StateSymmetryClass(
            family="zero-nine",
            exchangeable_count=middle_count,
        )

    return StateSymmetryClass(
        family="nine-no-zero",
        exchangeable_count=middle_count,
    )


def canonical_relabeling(
    missing_digits: Iterable[int],
) -> dict[int, int]:
    state = frozenset(
        normalize_digits(missing_digits)
    )

    symmetry_class = state_symmetry_class(
        state
    )

    if not state:
        return {}

    mapping: dict[int, int] = {}

    if symmetry_class.family == "no-nine":
        mapping.update(
            zip(
                sorted(state),
                range(len(state)),
            )
        )

    elif symmetry_class.family == "nine-no-zero":
        mapping[9] = 9

        mapping.update(
            zip(
                sorted(
                    state.intersection(
                        MIDDLE_DIGITS
                    )
                ),
                range(
                    1,
                    symmetry_class
                    .exchangeable_count
                    + 1,
                ),
            )
        )

    elif symmetry_class.family == "zero-nine":
        mapping[0] = 0
        mapping[9] = 9

        mapping.update(
            zip(
                sorted(
                    state.intersection(
                        MIDDLE_DIGITS
                    )
                ),
                range(
                    1,
                    symmetry_class
                    .exchangeable_count
                    + 1,
                ),
            )
        )

    else:
        raise RuntimeError(
            "Famiglia non gestita nella "
            f"canonicalizzazione: "
            f"{symmetry_class.family}."
        )

    canonicalized = relabel_state(
        state,
        mapping,
    )

    if (
        canonicalized
        != symmetry_class.canonical_state
    ):
        raise RuntimeError(
            "La canonicalizzazione non produce "
            "il rappresentante previsto."
        )

    return mapping


def relabel_state(
    state: Iterable[int],
    mapping: Mapping[int, int],
) -> DigitState:
    normalized = frozenset(
        normalize_digits(state)
    )

    missing_keys = (
        normalized - mapping.keys()
    )

    if missing_keys:
        raise ValueError(
            "La mappa non definisce le cifre: "
            + ", ".join(
                str(digit)
                for digit in sorted(missing_keys)
            )
        )

    relabelled = frozenset(
        mapping[digit]
        for digit in normalized
    )

    if len(relabelled) != len(normalized):
        raise ValueError(
            "La mappa non è iniettiva sullo stato."
        )

    return relabelled


def group_nonempty_states_by_symmetry() -> dict[
    StateSymmetryClass,
    tuple[DigitState, ...],
]:
    groups: dict[
        StateSymmetryClass,
        list[DigitState],
    ] = {}

    for state in all_digit_states(
        include_empty=False
    ):
        symmetry_class = state_symmetry_class(
            state
        )

        groups.setdefault(
            symmetry_class,
            [],
        ).append(state)

    return {
        symmetry_class: tuple(
            sorted(
                states,
                key=lambda state: (
                    len(state),
                    tuple(sorted(state)),
                ),
            )
        )
        for symmetry_class, states
        in sorted(groups.items())
    }


def canonicalized_transition_distribution(
    missing_digits: Iterable[int],
) -> dict[DigitState, float]:
    state = frozenset(
        normalize_digits(missing_digits)
    )

    mapping = canonical_relabeling(state)

    return {
        relabel_state(
            next_state,
            mapping,
        ): probability
        for next_state, probability
        in transition_distribution(state).items()
    }


def transition_symmetry_error(
    missing_digits: Iterable[int],
) -> tuple[int, float]:
    state = frozenset(
        normalize_digits(missing_digits)
    )

    symmetry_class = state_symmetry_class(
        state
    )

    observed = (
        canonicalized_transition_distribution(
            state
        )
    )

    expected = transition_distribution(
        symmetry_class.canonical_state
    )

    compared_states = (
        set(observed) | set(expected)
    )

    maximum_error = max(
        (
            abs(
                observed.get(next_state, 0.0)
                - expected.get(next_state, 0.0)
            )
            for next_state in compared_states
        ),
        default=0.0,
    )

    return len(compared_states), maximum_error


def verify_structural_symmetry(
    *,
    tolerance: float = 1e-12,
) -> StructuralVerificationSummary:
    if tolerance < 0.0:
        raise ValueError(
            "La tolleranza non può essere negativa."
        )

    states = all_digit_states()

    for forbidden in states:
        derived = (
            allowed_number_count_closed_form(
                forbidden
            )
        )

        enumerated = (
            allowed_number_count_enumerated(
                forbidden
            )
        )

        if derived != enumerated:
            raise RuntimeError(
                "Conteggio strutturale errato per "
                f"{sorted(forbidden)}: "
                f"formula {derived}, "
                f"enumerazione {enumerated}."
            )

    transition_entries = 0
    maximum_transition_error = 0.0

    for state in states:
        (
            compared_entries,
            error,
        ) = transition_symmetry_error(state)

        transition_entries += compared_entries
        maximum_transition_error = max(
            maximum_transition_error,
            error,
        )

        if error > tolerance:
            raise RuntimeError(
                "Simmetria di transizione violata "
                f"per {sorted(state)}: "
                f"{error:.15e}."
            )

    groups = (
        group_nonempty_states_by_symmetry()
    )

    if len(groups) != 27:
        raise RuntimeError(
            "Attese 27 classi metriche non vuote, "
            f"trovate {len(groups)}."
        )

    return StructuralVerificationSummary(
        forbidden_states_checked=len(states),
        markov_states_checked=len(states),
        nonempty_symmetry_classes=len(groups),
        transition_entries_compared=(
            transition_entries
        ),
        maximum_transition_error=(
            maximum_transition_error
        ),
    )
