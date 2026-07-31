"""Backtest puro delle frequenze mobili delle cifre."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from itertools import combinations
from math import comb
from random import Random

from strategies.coverage_completion import (
    current_coverage_state,
)
from strategies.digit_coverage import count_all_digits
from strategies.lotto_repository import (
    DrawSnapshot,
    split_digits,
)


ALL_DIGITS = frozenset(range(10))


@dataclass(frozen=True)
class RollingDigitFrequency:
    """Frequenza delle cifre nelle ultime N estrazioni di una ruota."""

    wheel: str
    wheel_order: int
    window_size: int
    draw_numbers: tuple[int, ...]
    start_date: str
    end_date: str
    digit_counts: tuple[int, ...]
    most_frequent_digits: frozenset[int]
    maximum_count: int


@dataclass(frozen=True)
class CandidateOutcome:
    """Esito di una rosa prefissata sull'estrazione target."""

    wheel: str
    wheel_order: int
    target_draw: int
    target_date: str
    candidate_numbers: tuple[int, ...]
    hit_numbers: tuple[int, ...]
    ambo_hits: tuple[tuple[int, int], ...]
    covered_ambo_count: int
    hit_ambo_count: int


@dataclass(frozen=True)
class WalkForwardObservation:
    """Selezione pre-target ed esito osservato senza look-ahead."""

    wheel: str
    wheel_order: int
    window_size: int
    history_draw_numbers: tuple[int, ...]
    history_start_draw: int
    history_end_draw: int
    target_draw: int
    target_date: str
    target_numbers: tuple[int, ...]
    most_frequent_digits: frozenset[int]
    missing_digits: frozenset[int]
    candidate_numbers: tuple[int, ...]
    hit_numbers: tuple[int, ...]
    ambo_hits: tuple[tuple[int, int], ...]
    covered_ambo_count: int
    hit_ambo_count: int


@dataclass(frozen=True)
class WalkForwardSummary:
    """Riepilogo descrittivo di una finestra in un periodo."""

    period: str
    window_size: int
    start_date: str
    end_date: str
    observation_count: int
    candidate_number_count: int
    covered_ambo_count: int
    observations_with_number_hit: int
    observations_with_ambo_hit: int
    hit_number_count: int
    hit_ambo_count: int
    mean_candidate_number_count: float
    mean_covered_ambo_count: float


@dataclass(frozen=True)
class EqualSizeRandomBaseline:
    """Distribuzione casuale a parità di dimensione delle rose."""

    period: str
    window_size: int
    start_date: str
    end_date: str
    repetitions: int
    seed: int
    observation_count: int
    covered_ambo_count: int
    observed_hit_number_count: int
    observed_hit_ambo_count: int
    replicate_hit_number_counts: tuple[int, ...]
    replicate_hit_ambo_counts: tuple[int, ...]
    mean_hit_number_count: float
    mean_hit_ambo_count: float
    empirical_p_value_hit_number: float
    empirical_p_value_hit_ambo: float


def _validate_digit_set(
    name: str,
    digits: Iterable[int],
) -> frozenset[int]:
    normalized = frozenset(digits)

    invalid = tuple(
        sorted(
            digit
            for digit in normalized
            if (
                not isinstance(digit, int)
                or isinstance(digit, bool)
                or digit not in ALL_DIGITS
            )
        )
    )

    if invalid:
        raise ValueError(
            f"{name} contiene cifre non valide: "
            + ", ".join(str(digit) for digit in invalid)
        )

    return normalized


def _ordered_single_wheel(
    draws: Sequence[DrawSnapshot],
) -> tuple[DrawSnapshot, ...]:
    if not draws:
        raise ValueError(
            "Servono estrazioni per calcolare "
            "la frequenza mobile."
        )

    wheel = draws[0].wheel
    wheel_order = draws[0].wheel_order

    for draw in draws:
        if draw.wheel != wheel:
            raise ValueError(
                "La frequenza mobile non può mescolare ruote."
            )

        if draw.wheel_order != wheel_order:
            raise ValueError(
                "Ordine ruota incoerente nelle estrazioni."
            )

    return tuple(
        sorted(
            draws,
            key=lambda draw: (
                draw.draw_date,
                draw.draw_number,
            ),
        )
    )


def rolling_digit_frequency(
    draws: Sequence[DrawSnapshot],
    *,
    window_size: int,
) -> RollingDigitFrequency:
    """Calcola le cifre più frequenti nelle ultime N estrazioni."""

    if (
        not isinstance(window_size, int)
        or isinstance(window_size, bool)
        or window_size <= 0
    ):
        raise ValueError(
            "window_size deve essere un intero positivo"
        )

    ordered = _ordered_single_wheel(draws)

    if len(ordered) < window_size:
        raise ValueError(
            "La storia disponibile è più corta "
            "della finestra richiesta."
        )

    selected = ordered[-window_size:]
    digit_counts = count_all_digits(selected)
    maximum_count = max(digit_counts)

    most_frequent_digits = frozenset(
        digit
        for digit, count in enumerate(digit_counts)
        if count == maximum_count
    )

    return RollingDigitFrequency(
        wheel=selected[0].wheel,
        wheel_order=selected[0].wheel_order,
        window_size=window_size,
        draw_numbers=tuple(
            draw.draw_number
            for draw in selected
        ),
        start_date=selected[0].draw_date,
        end_date=selected[-1].draw_date,
        digit_counts=digit_counts,
        most_frequent_digits=most_frequent_digits,
        maximum_count=maximum_count,
    )


def generate_candidate_numbers(
    *,
    most_frequent_digits: Iterable[int],
    missing_digits: Iterable[int],
) -> tuple[int, ...]:
    """
    Genera presente-mancante, mancante-presente e gemelli validi.

    Sono conservati soltanto i numeri del Lotto compresi tra 1 e 90.
    """

    frequent = _validate_digit_set(
        "most_frequent_digits",
        most_frequent_digits,
    )
    missing = _validate_digit_set(
        "missing_digits",
        missing_digits,
    )

    candidates: set[int] = set()

    for frequent_digit in frequent:
        gemello = 11 * frequent_digit

        if 1 <= gemello <= 90:
            candidates.add(gemello)

        for missing_digit in missing:
            forward = (
                10 * frequent_digit
                + missing_digit
            )
            reverse = (
                10 * missing_digit
                + frequent_digit
            )

            if 1 <= forward <= 90:
                candidates.add(forward)

            if 1 <= reverse <= 90:
                candidates.add(reverse)

    return tuple(sorted(candidates))


def evaluate_candidate_numbers(
    *,
    candidate_numbers: Iterable[int],
    target: DrawSnapshot,
) -> CandidateOutcome:
    """Valuta una rosa già fissata contro una sola estrazione target."""

    candidates = tuple(
        sorted(set(candidate_numbers))
    )

    invalid = tuple(
        number
        for number in candidates
        if (
            not isinstance(number, int)
            or isinstance(number, bool)
            or not 1 <= number <= 90
        )
    )

    if invalid:
        raise ValueError(
            "candidate_numbers contiene numeri non validi: "
            + ", ".join(str(number) for number in invalid)
        )

    if len(target.numbers) != 5:
        raise ValueError(
            f"Estrazione {target.draw_number}, "
            f"ruota {target.wheel}: "
            f"attesi 5 numeri, "
            f"trovati {len(target.numbers)}."
        )

    target_numbers = frozenset(target.numbers)

    if len(target_numbers) != 5:
        raise ValueError(
            f"Estrazione {target.draw_number}, "
            f"ruota {target.wheel}: "
            "i cinque numeri devono essere distinti."
        )

    if any(
        not isinstance(number, int)
        or isinstance(number, bool)
        or not 1 <= number <= 90
        for number in target_numbers
    ):
        raise ValueError(
            f"Estrazione {target.draw_number}, "
            f"ruota {target.wheel}: "
            "numero fuori intervallo 1–90."
        )

    hit_numbers = tuple(
        number
        for number in candidates
        if number in target_numbers
    )
    ambo_hits = tuple(
        combinations(hit_numbers, 2)
    )

    covered_ambo_count = (
        comb(len(candidates), 2)
        if len(candidates) >= 2
        else 0
    )

    return CandidateOutcome(
        wheel=target.wheel,
        wheel_order=target.wheel_order,
        target_draw=target.draw_number,
        target_date=target.draw_date,
        candidate_numbers=candidates,
        hit_numbers=hit_numbers,
        ambo_hits=ambo_hits,
        covered_ambo_count=covered_ambo_count,
        hit_ambo_count=len(ambo_hits),
    )


def build_walk_forward_observation(
    draws: Sequence[DrawSnapshot],
    *,
    target_index: int,
    window_size: int,
) -> WalkForwardObservation | None:
    """
    Costruisce una singola osservazione usando solo dati pre-target.

    Restituisce ``None`` quando la storia è troppo corta oppure
    quando il ciclo naturale pre-target non è ancora sincronizzato.
    """

    if (
        not isinstance(target_index, int)
        or isinstance(target_index, bool)
        or target_index < 0
        or target_index >= len(draws)
    ):
        raise IndexError(
            "target_index fuori dalla sequenza disponibile"
        )

    ordered = _ordered_single_wheel(draws)

    if target_index >= len(ordered):
        raise IndexError(
            "target_index fuori dalla sequenza disponibile"
        )

    target = ordered[target_index]
    history = ordered[:target_index]

    if len(history) < window_size:
        return None

    state = current_coverage_state(history)

    if (
        not state.synchronized
        or state.draws_in_cycle == 0
    ):
        return None

    frequency = rolling_digit_frequency(
        history,
        window_size=window_size,
    )
    candidate_numbers = generate_candidate_numbers(
        most_frequent_digits=(
            frequency.most_frequent_digits
        ),
        missing_digits=state.missing_digits,
    )
    outcome = evaluate_candidate_numbers(
        candidate_numbers=candidate_numbers,
        target=target,
    )

    return WalkForwardObservation(
        wheel=target.wheel,
        wheel_order=target.wheel_order,
        window_size=window_size,
        history_draw_numbers=frequency.draw_numbers,
        history_start_draw=frequency.draw_numbers[0],
        history_end_draw=frequency.draw_numbers[-1],
        target_draw=target.draw_number,
        target_date=target.draw_date,
        target_numbers=target.numbers,
        most_frequent_digits=(
            frequency.most_frequent_digits
        ),
        missing_digits=state.missing_digits,
        candidate_numbers=outcome.candidate_numbers,
        hit_numbers=outcome.hit_numbers,
        ambo_hits=outcome.ambo_hits,
        covered_ambo_count=(
            outcome.covered_ambo_count
        ),
        hit_ambo_count=outcome.hit_ambo_count,
    )


def build_walk_forward_observations(
    draws: Sequence[DrawSnapshot],
    *,
    window_size: int,
) -> tuple[WalkForwardObservation, ...]:
    """
    Costruisce tutte le osservazioni walk-forward valide di una ruota.

    Lo stato del ciclo viene aggiornato incrementalmente in una sola
    scansione. Ogni rosa usa soltanto le ultime N estrazioni precedenti
    al target, senza ricostruire l'intero prefisso storico.
    """

    if (
        not isinstance(window_size, int)
        or isinstance(window_size, bool)
        or window_size <= 0
    ):
        raise ValueError(
            "window_size deve essere un intero positivo"
        )

    if not draws:
        return ()

    ordered = _ordered_single_wheel(draws)
    covered: set[int] = set()
    synchronized = False
    observations: list[WalkForwardObservation] = []

    for target_index in range(1, len(ordered)):
        current = ordered[target_index - 1]

        for number in current.numbers:
            covered.update(split_digits(number))

        if covered == ALL_DIGITS:
            covered.clear()
            synchronized = True
            continue

        if (
            not synchronized
            or target_index < window_size
        ):
            continue

        target = ordered[target_index]
        selected_history = ordered[
            target_index - window_size:
            target_index
        ]
        frequency = rolling_digit_frequency(
            selected_history,
            window_size=window_size,
        )
        candidate_numbers = generate_candidate_numbers(
            most_frequent_digits=(
                frequency.most_frequent_digits
            ),
            missing_digits=(
                ALL_DIGITS.difference(covered)
            ),
        )
        outcome = evaluate_candidate_numbers(
            candidate_numbers=candidate_numbers,
            target=target,
        )

        observations.append(
            WalkForwardObservation(
                wheel=target.wheel,
                wheel_order=target.wheel_order,
                window_size=window_size,
                history_draw_numbers=(
                    frequency.draw_numbers
                ),
                history_start_draw=(
                    frequency.draw_numbers[0]
                ),
                history_end_draw=(
                    frequency.draw_numbers[-1]
                ),
                target_draw=target.draw_number,
                target_date=target.draw_date,
                target_numbers=target.numbers,
                most_frequent_digits=(
                    frequency.most_frequent_digits
                ),
                missing_digits=(
                    ALL_DIGITS.difference(covered)
                ),
                candidate_numbers=(
                    outcome.candidate_numbers
                ),
                hit_numbers=outcome.hit_numbers,
                ambo_hits=outcome.ambo_hits,
                covered_ambo_count=(
                    outcome.covered_ambo_count
                ),
                hit_ambo_count=(
                    outcome.hit_ambo_count
                ),
            )
        )

    return tuple(observations)


def build_walk_forward_experiment(
    draws_by_wheel: Mapping[
        str,
        Sequence[DrawSnapshot],
    ],
    *,
    window_sizes: Iterable[int],
) -> dict[int, tuple[WalkForwardObservation, ...]]:
    """
    Aggrega il backtest walk-forward per più ruote e finestre.

    Le finestre vengono deduplicate e ordinate. Per ciascuna finestra,
    le osservazioni sono ordinate cronologicamente e poi per ordine
    ufficiale della ruota.
    """

    normalized_windows: set[int] = set()

    for window_size in window_sizes:
        if (
            not isinstance(window_size, int)
            or isinstance(window_size, bool)
            or window_size <= 0
        ):
            raise ValueError(
                "window_sizes deve contenere "
                "soltanto interi positivi"
            )

        normalized_windows.add(window_size)

    if not normalized_windows:
        raise ValueError(
            "Servono almeno una finestra mobile."
        )

    experiment: dict[
        int,
        tuple[WalkForwardObservation, ...],
    ] = {}

    for window_size in sorted(normalized_windows):
        observations: list[
            WalkForwardObservation
        ] = []

        for draws in draws_by_wheel.values():
            observations.extend(
                build_walk_forward_observations(
                    draws,
                    window_size=window_size,
                )
            )

        experiment[window_size] = tuple(
            sorted(
                observations,
                key=lambda observation: (
                    observation.target_date,
                    observation.target_draw,
                    observation.wheel_order,
                    observation.wheel,
                ),
            )
        )

    return experiment


def _parse_strict_iso_date(
    name: str,
    value: str,
) -> date:
    if not isinstance(value, str):
        raise ValueError(
            f"{name} deve essere una data ISO YYYY-MM-DD"
        )

    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"{name} deve essere una data ISO valida YYYY-MM-DD"
        ) from error

    if parsed.isoformat() != value:
        raise ValueError(
            f"{name} deve usare il formato ISO YYYY-MM-DD"
        )

    return parsed


def summarize_walk_forward_observations(
    observations: Sequence[WalkForwardObservation],
    *,
    window_size: int,
    period: str,
    start_date: str,
    end_date: str,
) -> WalkForwardSummary:
    """
    Riepiloga esposizione e risultati entro limiti ISO inclusivi.

    Le osservazioni devono appartenere tutte alla stessa finestra
    dichiarata. I periodi vuoti producono conteggi e medie pari a zero.
    """

    if (
        not isinstance(window_size, int)
        or isinstance(window_size, bool)
        or window_size <= 0
    ):
        raise ValueError(
            "window_size deve essere un intero positivo"
        )

    if not isinstance(period, str) or not period.strip():
        raise ValueError(
            "period deve essere una stringa non vuota"
        )

    start = _parse_strict_iso_date(
        "start_date",
        start_date,
    )
    end = _parse_strict_iso_date(
        "end_date",
        end_date,
    )

    if start > end:
        raise ValueError(
            "start_date non può essere successiva a end_date"
        )

    for observation in observations:
        if observation.window_size != window_size:
            raise ValueError(
                "La serie contiene osservazioni "
                "con una finestra diversa da window_size."
            )

    selected: list[WalkForwardObservation] = []

    for observation in observations:
        target = _parse_strict_iso_date(
            "observation.target_date",
            observation.target_date,
        )

        if start <= target <= end:
            selected.append(observation)

    observation_count = len(selected)
    candidate_number_count = sum(
        len(observation.candidate_numbers)
        for observation in selected
    )
    covered_ambo_count = sum(
        observation.covered_ambo_count
        for observation in selected
    )
    observations_with_number_hit = sum(
        bool(observation.hit_numbers)
        for observation in selected
    )
    observations_with_ambo_hit = sum(
        bool(observation.ambo_hits)
        for observation in selected
    )
    hit_number_count = sum(
        len(observation.hit_numbers)
        for observation in selected
    )
    hit_ambo_count = sum(
        observation.hit_ambo_count
        for observation in selected
    )

    if observation_count:
        mean_candidate_number_count = (
            candidate_number_count
            / observation_count
        )
        mean_covered_ambo_count = (
            covered_ambo_count
            / observation_count
        )
    else:
        mean_candidate_number_count = 0.0
        mean_covered_ambo_count = 0.0

    return WalkForwardSummary(
        period=period,
        window_size=window_size,
        start_date=start_date,
        end_date=end_date,
        observation_count=observation_count,
        candidate_number_count=candidate_number_count,
        covered_ambo_count=covered_ambo_count,
        observations_with_number_hit=(
            observations_with_number_hit
        ),
        observations_with_ambo_hit=(
            observations_with_ambo_hit
        ),
        hit_number_count=hit_number_count,
        hit_ambo_count=hit_ambo_count,
        mean_candidate_number_count=(
            mean_candidate_number_count
        ),
        mean_covered_ambo_count=(
            mean_covered_ambo_count
        ),
    )


def merge_draw_histories(
    archives: Sequence[
        Mapping[str, Sequence[DrawSnapshot]]
    ],
) -> dict[str, tuple[DrawSnapshot, ...]]:
    """
    Unisce archivi consecutivi conservando i cicli tra gli anni.

    Ogni archivio deve contenere lo stesso insieme di ruote. Il numero
    di concorso può ripartire da 1 in un nuovo anno, perché l'identità
    di una riga è data dalla coppia data-numero sulla singola ruota.
    """

    if not archives:
        return {}

    expected_wheels = frozenset(archives[0])

    for archive_index, archive in enumerate(archives):
        actual_wheels = frozenset(archive)

        if actual_wheels != expected_wheels:
            missing = tuple(
                sorted(expected_wheels - actual_wheels)
            )
            unexpected = tuple(
                sorted(actual_wheels - expected_wheels)
            )

            details: list[str] = []

            if missing:
                details.append(
                    "ruote mancanti: "
                    + ", ".join(missing)
                )

            if unexpected:
                details.append(
                    "ruote inattese: "
                    + ", ".join(unexpected)
                )

            description = "; ".join(details)

            raise ValueError(
                f"Archivio {archive_index}: "
                f"insieme di ruote incoerente"
                + (
                    f" ({description})"
                    if description
                    else ""
                )
            )

    grouped: dict[str, list[DrawSnapshot]] = {
        wheel: []
        for wheel in expected_wheels
    }
    wheel_orders: dict[str, int] = {}
    seen_keys: dict[
        str,
        set[tuple[str, int]],
    ] = {
        wheel: set()
        for wheel in expected_wheels
    }

    for archive_index, archive in enumerate(archives):
        for wheel in expected_wheels:
            for draw in archive[wheel]:
                if draw.wheel != wheel:
                    raise ValueError(
                        f"Archivio {archive_index}: "
                        f"la chiave {wheel!r} contiene "
                        f"un’estrazione della ruota "
                        f"{draw.wheel!r}."
                    )

                _parse_strict_iso_date(
                    "draw.draw_date",
                    draw.draw_date,
                )

                known_order = wheel_orders.get(wheel)

                if known_order is None:
                    wheel_orders[wheel] = draw.wheel_order
                elif draw.wheel_order != known_order:
                    raise ValueError(
                        f"Ordine incoerente per la ruota "
                        f"{wheel}: atteso {known_order}, "
                        f"trovato {draw.wheel_order}."
                    )

                draw_key = (
                    draw.draw_date,
                    draw.draw_number,
                )

                if draw_key in seen_keys[wheel]:
                    raise ValueError(
                        f"Estrazione duplicata per {wheel}: "
                        f"{draw.draw_date}, "
                        f"concorso {draw.draw_number}."
                    )

                seen_keys[wheel].add(draw_key)
                grouped[wheel].append(draw)

    ordered_wheels = tuple(
        sorted(
            expected_wheels,
            key=lambda wheel: (
                wheel_orders.get(wheel, 0),
                wheel,
            ),
        )
    )

    return {
        wheel: tuple(
            sorted(
                grouped[wheel],
                key=lambda draw: (
                    draw.draw_date,
                    draw.draw_number,
                ),
            )
        )
        for wheel in ordered_wheels
    }


def simulate_equal_size_random_baseline(
    observations: Sequence[WalkForwardObservation],
    *,
    window_size: int,
    period: str,
    start_date: str,
    end_date: str,
    repetitions: int,
    seed: int,
) -> EqualSizeRandomBaseline:
    """
    Simula rose uniformi casuali della stessa dimensione osservata.

    Per ciascuna osservazione e replica viene estratta senza
    reinserimento una rosa da 1 a 90. La sua dimensione coincide
    esattamente con quella prodotta dal metodo, ma l'identità dei
    numeri metodologici non influenza il baseline.
    """

    if (
        not isinstance(repetitions, int)
        or isinstance(repetitions, bool)
        or repetitions <= 0
    ):
        raise ValueError(
            "repetitions deve essere un intero positivo"
        )

    if (
        not isinstance(seed, int)
        or isinstance(seed, bool)
    ):
        raise ValueError(
            "seed deve essere un intero"
        )

    summary = summarize_walk_forward_observations(
        observations,
        window_size=window_size,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    start = _parse_strict_iso_date(
        "start_date",
        start_date,
    )
    end = _parse_strict_iso_date(
        "end_date",
        end_date,
    )

    selected: list[WalkForwardObservation] = []

    for observation in observations:
        target_date = _parse_strict_iso_date(
            "observation.target_date",
            observation.target_date,
        )

        if not start <= target_date <= end:
            continue

        target_numbers = observation.target_numbers

        if len(target_numbers) != 5:
            raise ValueError(
                "Ogni osservazione deve conservare "
                "esattamente cinque numeri target."
            )

        if len(set(target_numbers)) != 5:
            raise ValueError(
                "I cinque numeri target devono essere distinti."
            )

        if any(
            not isinstance(number, int)
            or isinstance(number, bool)
            or not 1 <= number <= 90
            for number in target_numbers
        ):
            raise ValueError(
                "I numeri target devono essere "
                "interi compresi tra 1 e 90."
            )

        candidate_numbers = observation.candidate_numbers

        if len(set(candidate_numbers)) != len(
            candidate_numbers
        ):
            raise ValueError(
                "La rosa metodologica deve essere deduplicata."
            )

        if len(candidate_numbers) > 90:
            raise ValueError(
                "La rosa metodologica non può superare 90 numeri."
            )

        selected.append(observation)

    covered_ambo_count = sum(
        comb(len(observation.candidate_numbers), 2)
        for observation in selected
    )

    rng = Random(seed)
    population = tuple(range(1, 91))

    replicate_hit_number_counts: list[int] = []
    replicate_hit_ambo_counts: list[int] = []

    for _ in range(repetitions):
        hit_number_count = 0
        hit_ambo_count = 0

        for observation in selected:
            candidate_size = len(
                observation.candidate_numbers
            )
            random_candidates = rng.sample(
                population,
                candidate_size,
            )
            target_numbers = frozenset(
                observation.target_numbers
            )
            hits = sum(
                number in target_numbers
                for number in random_candidates
            )

            hit_number_count += hits
            hit_ambo_count += (
                comb(hits, 2)
                if hits >= 2
                else 0
            )

        replicate_hit_number_counts.append(
            hit_number_count
        )
        replicate_hit_ambo_counts.append(
            hit_ambo_count
        )

    mean_hit_number_count = (
        sum(replicate_hit_number_counts)
        / repetitions
    )
    mean_hit_ambo_count = (
        sum(replicate_hit_ambo_counts)
        / repetitions
    )

    at_least_observed_numbers = sum(
        count >= summary.hit_number_count
        for count in replicate_hit_number_counts
    )
    at_least_observed_ambi = sum(
        count >= summary.hit_ambo_count
        for count in replicate_hit_ambo_counts
    )

    empirical_p_value_hit_number = (
        at_least_observed_numbers + 1
    ) / (repetitions + 1)
    empirical_p_value_hit_ambo = (
        at_least_observed_ambi + 1
    ) / (repetitions + 1)

    return EqualSizeRandomBaseline(
        period=period,
        window_size=window_size,
        start_date=start_date,
        end_date=end_date,
        repetitions=repetitions,
        seed=seed,
        observation_count=len(selected),
        covered_ambo_count=covered_ambo_count,
        observed_hit_number_count=(
            summary.hit_number_count
        ),
        observed_hit_ambo_count=(
            summary.hit_ambo_count
        ),
        replicate_hit_number_counts=tuple(
            replicate_hit_number_counts
        ),
        replicate_hit_ambo_counts=tuple(
            replicate_hit_ambo_counts
        ),
        mean_hit_number_count=mean_hit_number_count,
        mean_hit_ambo_count=mean_hit_ambo_count,
        empirical_p_value_hit_number=(
            empirical_p_value_hit_number
        ),
        empirical_p_value_hit_ambo=(
            empirical_p_value_hit_ambo
        ),
    )
