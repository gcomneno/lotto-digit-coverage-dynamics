"""Monotonia per inclusione del processo di copertura."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from strategies.coverage_markov import (
    absorption_quantiles,
    completion_probability_within,
    expected_remaining_draws,
)
from strategies.coverage_transition_enumerator import (
    ALL_DIGITS_MASK,
    mask_to_state,
)


STATE_COUNT = ALL_DIGITS_MASK + 1

HORIZONS = (1, 2, 3, 5, 10)
QUANTILES = (0.50, 0.90, 0.95, 0.99)


@dataclass(frozen=True)
class UpdateMonotonicitySummary:
    state_count: int
    cover_relations_checked: int
    observed_masks_checked: int
    update_checks: int
    violations: int


@dataclass(frozen=True)
class AbsorptionMonotonicitySummary:
    state_count: int
    strict_comparable_pairs: int
    expected_time_checks: int
    completion_cdf_checks: int
    quantile_checks: int
    maximum_expected_time_violation: float
    maximum_completion_cdf_violation: float
    maximum_quantile_violation: int


def validate_mask(
    mask: int,
    *,
    name: str,
) -> int:
    if not isinstance(mask, int):
        raise TypeError(
            f"{name} deve essere una maschera intera."
        )

    if not 0 <= mask <= ALL_DIGITS_MASK:
        raise ValueError(
            f"{name} deve essere compresa tra "
            f"0 e {ALL_DIGITS_MASK}."
        )

    return mask


def next_missing_mask(
    current_mask: int,
    observed_mask: int,
) -> int:
    """
    Applica un'estrazione rappresentata dalla sua maschera.

    Se ``S`` è lo stato mancante e ``G`` è l'insieme
    delle cifre osservate, il nuovo stato è ``S \\ G``.
    """

    current = validate_mask(
        current_mask,
        name="La maschera dello stato",
    )

    observed = validate_mask(
        observed_mask,
        name="La maschera osservata",
    )

    return (
        current
        & ~observed
        & ALL_DIGITS_MASK
    )


def is_subset_mask(
    lower_mask: int,
    upper_mask: int,
) -> bool:
    lower = validate_mask(
        lower_mask,
        name="La maschera inferiore",
    )

    upper = validate_mask(
        upper_mask,
        name="La maschera superiore",
    )

    return lower & ~upper == 0


def comparable_mask_pairs(
    *,
    include_equal: bool = False,
) -> Iterator[tuple[int, int]]:
    """
    Genera le coppie ``lower ⊆ upper``.

    Il numero totale, includendo l'uguaglianza, è ``3^10``:
    ogni cifra può essere assente da entrambi, presente solo
    nello stato superiore oppure presente in entrambi.
    """

    for upper_mask in range(STATE_COUNT):
        lower_mask = upper_mask

        while True:
            if (
                include_equal
                or lower_mask != upper_mask
            ):
                yield lower_mask, upper_mask

            if lower_mask == 0:
                break

            lower_mask = (
                lower_mask - 1
            ) & upper_mask


def cover_relation_pairs() -> Iterator[
    tuple[int, int]
]:
    """
    Genera gli archi del reticolo booleano.

    Ogni coppia differisce per l'aggiunta di una sola cifra.
    """

    for lower_mask in range(STATE_COUNT):
        for digit in range(10):
            bit = 1 << digit

            if lower_mask & bit:
                continue

            yield (
                lower_mask,
                lower_mask | bit,
            )


def verify_update_monotonicity(
) -> UpdateMonotonicitySummary:
    """
    Verifica esaustivamente la monotonia dell'aggiornamento.

    Basta controllare tutte le relazioni di copertura:
    la monotonia per ogni coppia comparabile segue per
    transitività.
    """

    cover_relations = 0
    update_checks = 0
    violations = 0

    for lower_mask, upper_mask in (
        cover_relation_pairs()
    ):
        cover_relations += 1

        for observed_mask in range(
            STATE_COUNT
        ):
            lower_next = next_missing_mask(
                lower_mask,
                observed_mask,
            )

            upper_next = next_missing_mask(
                upper_mask,
                observed_mask,
            )

            update_checks += 1

            if not is_subset_mask(
                lower_next,
                upper_next,
            ):
                violations += 1

                raise RuntimeError(
                    "Monotonia dell'aggiornamento violata: "
                    f"{lower_mask} ⊆ {upper_mask}, "
                    f"maschera osservata {observed_mask}, "
                    f"ma {lower_next} non è sottoinsieme "
                    f"di {upper_next}."
                )

    return UpdateMonotonicitySummary(
        state_count=STATE_COUNT,
        cover_relations_checked=(
            cover_relations
        ),
        observed_masks_checked=STATE_COUNT,
        update_checks=update_checks,
        violations=violations,
    )


def expected_times_by_mask() -> tuple[
    float,
    ...,
]:
    return tuple(
        expected_remaining_draws(
            mask_to_state(mask)
        )
        for mask in range(STATE_COUNT)
    )


def completion_cdfs_by_horizon() -> dict[
    int,
    tuple[float, ...],
]:
    return {
        horizon: tuple(
            completion_probability_within(
                mask_to_state(mask),
                horizon,
            )
            for mask in range(STATE_COUNT)
        )
        for horizon in HORIZONS
    }


def quantiles_by_mask() -> tuple[
    dict[float, int],
    ...,
]:
    return tuple(
        absorption_quantiles(
            mask_to_state(mask),
            QUANTILES,
        )
        for mask in range(STATE_COUNT)
    )


def verify_absorption_monotonicity(
    *,
    tolerance: float = 1e-12,
) -> AbsorptionMonotonicitySummary:
    """
    Verifica l'ordine stocastico su tutte le coppie strette.

    Per ``lower ⊂ upper`` devono valere:

    - E[tau_lower] <= E[tau_upper];
    - P(tau_lower <= h) >= P(tau_upper <= h);
    - Q_p(tau_lower) <= Q_p(tau_upper).
    """

    if tolerance < 0.0:
        raise ValueError(
            "La tolleranza non può essere negativa."
        )

    expected_times = (
        expected_times_by_mask()
    )

    completion_cdfs = (
        completion_cdfs_by_horizon()
    )

    quantiles = quantiles_by_mask()

    comparable_pairs = 0
    expected_checks = 0
    cdf_checks = 0
    quantile_checks = 0

    maximum_expected_violation = 0.0
    maximum_cdf_violation = 0.0
    maximum_quantile_violation = 0

    for lower_mask, upper_mask in (
        comparable_mask_pairs()
    ):
        comparable_pairs += 1

        expected_violation = max(
            0.0,
            expected_times[lower_mask]
            - expected_times[upper_mask],
        )

        expected_checks += 1

        maximum_expected_violation = max(
            maximum_expected_violation,
            expected_violation,
        )

        if expected_violation > tolerance:
            raise RuntimeError(
                "Tempo atteso non monotono per "
                f"{sorted(mask_to_state(lower_mask))} "
                "⊂ "
                f"{sorted(mask_to_state(upper_mask))}: "
                f"{expected_violation:.15e}."
            )

        for horizon in HORIZONS:
            cdf_violation = max(
                0.0,
                completion_cdfs[horizon][
                    upper_mask
                ]
                - completion_cdfs[horizon][
                    lower_mask
                ],
            )

            cdf_checks += 1

            maximum_cdf_violation = max(
                maximum_cdf_violation,
                cdf_violation,
            )

            if cdf_violation > tolerance:
                raise RuntimeError(
                    "CDF di completamento non monotona "
                    f"all'orizzonte {horizon} per "
                    f"{sorted(mask_to_state(lower_mask))} "
                    "⊂ "
                    f"{sorted(mask_to_state(upper_mask))}: "
                    f"{cdf_violation:.15e}."
                )

        for probability in QUANTILES:
            quantile_violation = max(
                0,
                quantiles[lower_mask][
                    probability
                ]
                - quantiles[upper_mask][
                    probability
                ],
            )

            quantile_checks += 1

            maximum_quantile_violation = max(
                maximum_quantile_violation,
                quantile_violation,
            )

            if quantile_violation:
                raise RuntimeError(
                    "Quantile non monotono "
                    f"Q{probability:.2f} per "
                    f"{sorted(mask_to_state(lower_mask))} "
                    "⊂ "
                    f"{sorted(mask_to_state(upper_mask))}: "
                    f"{quantile_violation}."
                )

    return AbsorptionMonotonicitySummary(
        state_count=STATE_COUNT,
        strict_comparable_pairs=(
            comparable_pairs
        ),
        expected_time_checks=expected_checks,
        completion_cdf_checks=cdf_checks,
        quantile_checks=quantile_checks,
        maximum_expected_time_violation=(
            maximum_expected_violation
        ),
        maximum_completion_cdf_violation=(
            maximum_cdf_violation
        ),
        maximum_quantile_violation=(
            maximum_quantile_violation
        ),
    )
