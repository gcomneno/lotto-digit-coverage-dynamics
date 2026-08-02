"""Checkpoint incrementale dei cicli naturali di copertura."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from strategies.coverage_completion import (
    ALL_DIGITS,
    digits_in_draw,
)
from strategies.lotto_repository import (
    DrawSnapshot,
    split_digits,
)


CONSOLIDATED_PATTERN = re.compile(
    r"^lotto-(\d{4})-(\d{4})\.sqlite3$"
)
ANNUAL_PATTERN = re.compile(
    r"^lotto-(\d{4})\.sqlite3$"
)


@dataclass(frozen=True)
class ArchiveSegment:
    """Archivio non sovrapposto usato dal checkpoint."""

    first_year: int
    last_year: int
    path: Path


@dataclass(frozen=True)
class WheelCheckpoint:
    """Stato riprendibile di una singola ruota."""

    wheel: str
    wheel_order: int
    latest_draw: int
    latest_date: str
    completed_cycles: int
    synchronized: bool
    draws_in_cycle: int
    cycle_start_draw: int | None
    cycle_start_date: str | None
    covered_digits: tuple[int, ...]
    missing_digits: tuple[int, ...]
    digit_occurrences: tuple[int, ...]
    most_present_digits: tuple[int, ...]


@dataclass
class MutableWheelState:
    """Accumulatore interno durante la lettura storica."""

    wheel: str
    wheel_order: int
    latest_draw: int = 0
    latest_date: str = ""
    completed_cycles: int = 0
    synchronized: bool = False
    draws_in_cycle: int = 0
    cycle_start_draw: int | None = None
    cycle_start_date: str | None = None
    covered_digits: set[int] | None = None
    digit_occurrences: list[int] | None = None

    def __post_init__(self) -> None:
        if self.covered_digits is None:
            self.covered_digits = set()

        if self.digit_occurrences is None:
            self.digit_occurrences = [0] * 10


def previous_complete_year(
    current_year: int | None = None,
) -> int:
    """Restituisce l'ultimo anno completo precedente."""

    resolved = (
        date.today().year
        if current_year is None
        else current_year
    )

    if resolved <= 1871:
        raise ValueError(
            "L'anno corrente deve essere successivo al 1871."
        )

    return resolved - 1


def discover_archive_segments(
    data_directory: Path,
) -> tuple[ArchiveSegment, ...]:
    """Individua consolidati e database annuali disponibili."""

    segments: list[ArchiveSegment] = []

    for path in data_directory.glob(
        "lotto-*.sqlite3"
    ):
        consolidated = CONSOLIDATED_PATTERN.match(
            path.name
        )

        if consolidated is not None:
            first = int(consolidated.group(1))
            last = int(consolidated.group(2))

            if first <= last:
                segments.append(
                    ArchiveSegment(
                        first_year=first,
                        last_year=last,
                        path=path,
                    )
                )

            continue

        annual = ANNUAL_PATTERN.match(path.name)

        if annual is not None:
            year = int(annual.group(1))

            segments.append(
                ArchiveSegment(
                    first_year=year,
                    last_year=year,
                    path=path,
                )
            )

    return tuple(segments)


def resolve_archive_chain(
    segments: Sequence[ArchiveSegment],
    *,
    first_year: int,
    last_year: int,
) -> tuple[ArchiveSegment, ...]:
    """
    Costruisce una catena continua e non sovrapposta.

    A parità di anno iniziale preferisce il segmento con
    termine più vicino. In questo modo vengono concatenati
    i consolidati parziali invece di scegliere subito un
    eventuale archivio complessivo.
    """

    if first_year > last_year:
        raise ValueError(
            "L'anno iniziale deve precedere quello finale."
        )

    selected: list[ArchiveSegment] = []
    cursor = first_year

    while cursor <= last_year:
        candidates = [
            segment
            for segment in segments
            if (
                segment.first_year == cursor
                and segment.last_year <= last_year
            )
        ]

        if not candidates:
            raise FileNotFoundError(
                "Nessun archivio disponibile per iniziare "
                f"dall'anno {cursor}."
            )

        consolidated = [
            segment
            for segment in candidates
            if segment.last_year > segment.first_year
        ]

        pool = (
            consolidated
            if consolidated
            else candidates
        )

        chosen = min(
            pool,
            key=lambda segment: (
                segment.last_year,
                segment.path.name,
            ),
        )

        selected.append(chosen)
        cursor = chosen.last_year + 1

    return tuple(selected)


def sha256_file(path: Path) -> str:
    """Calcola SHA-256 senza caricare il file in memoria."""

    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def load_draws(
    database_path: Path,
) -> tuple[DrawSnapshot, ...]:
    """Carica tutte le estrazioni per ruota in ordine storico."""

    uri = (
        f"file:{database_path.resolve()}?mode=ro"
    )

    with sqlite3.connect(
        uri,
        uri=True,
    ) as connection:
        connection.row_factory = sqlite3.Row

        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        if (
            integrity is None
            or str(integrity[0]) != "ok"
        ):
            detail = (
                "nessun risultato"
                if integrity is None
                else str(integrity[0])
            )

            raise RuntimeError(
                f"Database non integro: {database_path}: "
                f"{detail}"
            )

        rows = connection.execute(
            """
            SELECT
                draw_number,
                draw_date,
                wheel,
                wheel_order,
                position,
                value
            FROM v_draw_numbers
            ORDER BY
                draw_date,
                draw_number,
                wheel_order,
                position
            """
        ).fetchall()

    grouped: dict[
        tuple[int, str, str, int],
        list[int],
    ] = {}

    for row in rows:
        key = (
            int(row["draw_number"]),
            str(row["draw_date"]),
            str(row["wheel"]),
            int(row["wheel_order"]),
        )

        grouped.setdefault(key, []).append(
            int(row["value"])
        )

    draws: list[DrawSnapshot] = []

    for (
        draw_number,
        draw_date,
        wheel,
        wheel_order,
    ), numbers in grouped.items():
        if len(numbers) != 5:
            raise RuntimeError(
                f"{database_path}: estrazione "
                f"{draw_number}, ruota {wheel}: "
                f"attesi 5 numeri, trovati {len(numbers)}."
            )

        draws.append(
            DrawSnapshot(
                draw_number=draw_number,
                draw_date=draw_date,
                wheel=wheel,
                wheel_order=wheel_order,
                numbers=tuple(numbers),
            )
        )

    return tuple(draws)


def apply_draw(
    state: MutableWheelState,
    draw: DrawSnapshot,
) -> None:
    """Applica una singola estrazione allo stato della ruota."""

    if draw.wheel != state.wheel:
        raise ValueError(
            "La ruota dell'estrazione non coincide "
            "con quella dello stato."
        )

    if draw.wheel_order != state.wheel_order:
        raise ValueError(
            "Ordine ruota incoerente."
        )

    if (
        state.latest_date
        and (
            draw.draw_date,
            draw.draw_number,
        )
        <= (
            state.latest_date,
            state.latest_draw,
        )
    ):
        raise ValueError(
            f"Estrazione non successiva per {draw.wheel}: "
            f"{draw.draw_date}, {draw.draw_number}."
        )

    if state.draws_in_cycle == 0:
        state.cycle_start_draw = draw.draw_number
        state.cycle_start_date = draw.draw_date

    assert state.covered_digits is not None
    assert state.digit_occurrences is not None

    state.covered_digits.update(
        digits_in_draw(draw)
    )

    for number in draw.numbers:
        for digit in split_digits(number):
            state.digit_occurrences[digit] += 1

    state.draws_in_cycle += 1
    state.latest_draw = draw.draw_number
    state.latest_date = draw.draw_date

    if state.covered_digits == ALL_DIGITS:
        state.completed_cycles += 1
        state.synchronized = True
        state.draws_in_cycle = 0
        state.cycle_start_draw = None
        state.cycle_start_date = None
        state.covered_digits.clear()
        state.digit_occurrences = [0] * 10


def apply_draws(
    states: dict[str, MutableWheelState],
    draws: Iterable[DrawSnapshot],
) -> None:
    """Applica una sequenza multi-ruota agli accumulatori."""

    for draw in draws:
        state = states.get(draw.wheel)

        if state is None:
            state = MutableWheelState(
                wheel=draw.wheel,
                wheel_order=draw.wheel_order,
            )
            states[draw.wheel] = state

        apply_draw(state, draw)


def freeze_state(
    state: MutableWheelState,
) -> WheelCheckpoint:
    """Converte l'accumulatore nello stato JSON stabile."""

    assert state.covered_digits is not None
    assert state.digit_occurrences is not None

    maximum = max(state.digit_occurrences)

    most_present = tuple(
        digit
        for digit, occurrences
        in enumerate(state.digit_occurrences)
        if (
            occurrences == maximum
            and occurrences > 0
        )
    )

    covered = tuple(
        sorted(state.covered_digits)
    )

    return WheelCheckpoint(
        wheel=state.wheel,
        wheel_order=state.wheel_order,
        latest_draw=state.latest_draw,
        latest_date=state.latest_date,
        completed_cycles=state.completed_cycles,
        synchronized=state.synchronized,
        draws_in_cycle=state.draws_in_cycle,
        cycle_start_draw=state.cycle_start_draw,
        cycle_start_date=state.cycle_start_date,
        covered_digits=covered,
        missing_digits=tuple(
            sorted(
                ALL_DIGITS.difference(
                    state.covered_digits
                )
            )
        ),
        digit_occurrences=tuple(
            state.digit_occurrences
        ),
        most_present_digits=most_present,
    )


def checkpoint_payload(
    *,
    current_year: int,
    checkpoint_year: int,
    checkpoint_date: str,
    chain: Sequence[ArchiveSegment],
    states: Sequence[WheelCheckpoint],
    total_draws: int,
) -> dict[str, object]:
    """Costruisce il documento JSON versionato."""

    return {
        "schema_version": 1,
        "artifact_family": (
            "historical-coverage-checkpoint"
        ),
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "current_year": current_year,
        "checkpoint_year": checkpoint_year,
        "checkpoint_date": checkpoint_date,
        "first_historical_year": (
            chain[0].first_year
        ),
        "total_draw_snapshots": total_draws,
        "source_archives": [
            {
                "path": str(segment.path),
                "first_year": segment.first_year,
                "last_year": segment.last_year,
                "bytes": segment.path.stat().st_size,
                "sha256": sha256_file(segment.path),
            }
            for segment in chain
        ],
        "wheels": [
            asdict(state)
            for state in sorted(
                states,
                key=lambda item: (
                    item.wheel_order,
                    item.wheel,
                ),
            )
        ],
    }


def write_checkpoint(
    payload: dict[str, object],
    destination: Path,
) -> None:
    """Scrive il checkpoint in modo atomico."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(destination)


def validate_checkpoint_payload(
    payload: object,
) -> dict[str, object]:
    """Valida la struttura essenziale del checkpoint."""

    if not isinstance(payload, dict):
        raise ValueError(
            "Il checkpoint deve essere un oggetto JSON."
        )

    if payload.get("schema_version") != 1:
        raise ValueError(
            "Versione schema checkpoint non supportata."
        )

    if payload.get("artifact_family") != (
        "historical-coverage-checkpoint"
    ):
        raise ValueError(
            "Famiglia artefatto checkpoint inattesa."
        )

    current_year = payload.get("current_year")
    checkpoint_year = payload.get("checkpoint_year")
    checkpoint_date = payload.get("checkpoint_date")
    sources = payload.get("source_archives")
    wheels = payload.get("wheels")

    if (
        not isinstance(current_year, int)
        or not isinstance(checkpoint_year, int)
        or checkpoint_year != current_year - 1
    ):
        raise ValueError(
            "Relazione tra anno corrente e checkpoint "
            "non valida."
        )

    if (
        not isinstance(checkpoint_date, str)
        or not checkpoint_date.startswith(
            f"{checkpoint_year}-"
        )
    ):
        raise ValueError(
            "Data checkpoint non appartenente "
            "all'ultimo anno completo."
        )

    if (
        not isinstance(sources, list)
        or not sources
    ):
        raise ValueError(
            "Archivi sorgente assenti."
        )

    if (
        not isinstance(wheels, list)
        or not wheels
    ):
        raise ValueError(
            "Stati delle ruote assenti."
        )

    seen_wheels: set[str] = set()
    seen_orders: set[int] = set()

    for item in wheels:
        if not isinstance(item, dict):
            raise ValueError(
                "Stato ruota non valido."
            )

        wheel = item.get("wheel")
        wheel_order = item.get("wheel_order")
        latest_draw = item.get("latest_draw")
        latest_date = item.get("latest_date")
        completed_cycles = item.get(
            "completed_cycles"
        )
        synchronized = item.get("synchronized")
        draws_in_cycle = item.get(
            "draws_in_cycle"
        )
        cycle_start_draw = item.get(
            "cycle_start_draw"
        )
        cycle_start_date = item.get(
            "cycle_start_date"
        )
        covered_raw = item.get(
            "covered_digits"
        )
        missing_raw = item.get(
            "missing_digits"
        )
        occurrences_raw = item.get(
            "digit_occurrences"
        )
        most_present_raw = item.get(
            "most_present_digits"
        )

        if not isinstance(wheel, str) or not wheel:
            raise ValueError(
                "Nome ruota non valido."
            )

        if wheel in seen_wheels:
            raise ValueError(
                f"Ruota duplicata: {wheel}."
            )

        if (
            not isinstance(wheel_order, int)
            or not 1 <= wheel_order <= 11
        ):
            raise ValueError(
                f"{wheel}: ordine ruota non valido."
            )

        if wheel_order in seen_orders:
            raise ValueError(
                f"Ordine ruota duplicato: {wheel_order}."
            )

        if (
            not isinstance(latest_draw, int)
            or latest_draw <= 0
        ):
            raise ValueError(
                f"{wheel}: ultima estrazione non valida."
            )

        if (
            not isinstance(latest_date, str)
            or latest_date > checkpoint_date
        ):
            raise ValueError(
                f"{wheel}: ultima data non valida."
            )

        if (
            not isinstance(completed_cycles, int)
            or completed_cycles < 0
        ):
            raise ValueError(
                f"{wheel}: cicli completati non validi."
            )

        if not isinstance(synchronized, bool):
            raise ValueError(
                f"{wheel}: sincronizzazione non valida."
            )

        if (
            not isinstance(draws_in_cycle, int)
            or draws_in_cycle < 0
        ):
            raise ValueError(
                f"{wheel}: lunghezza ciclo non valida."
            )

        if not isinstance(covered_raw, list):
            raise ValueError(
                f"{wheel}: cifre coperte non valide."
            )

        if not isinstance(missing_raw, list):
            raise ValueError(
                f"{wheel}: cifre mancanti non valide."
            )

        if not isinstance(
            occurrences_raw,
            list,
        ):
            raise ValueError(
                f"{wheel}: conteggi cifre non validi."
            )

        if not isinstance(
            most_present_raw,
            list,
        ):
            raise ValueError(
                f"{wheel}: cifre prevalenti non valide."
            )

        covered = set(covered_raw)
        missing = set(missing_raw)

        if (
            covered | missing != set(range(10))
            or covered & missing
        ):
            raise ValueError(
                f"{wheel}: partizione delle cifre "
                "non valida."
            )

        if (
            len(covered_raw) != len(covered)
            or len(missing_raw) != len(missing)
        ):
            raise ValueError(
                f"{wheel}: cifre duplicate."
            )

        if (
            len(occurrences_raw) != 10
            or any(
                not isinstance(value, int)
                or value < 0
                for value in occurrences_raw
            )
        ):
            raise ValueError(
                f"{wheel}: vettore delle occorrenze "
                "non valido."
            )

        most_present = set(most_present_raw)

        if (
            len(most_present_raw)
            != len(most_present)
            or not most_present.issubset(
                set(range(10))
            )
        ):
            raise ValueError(
                f"{wheel}: cifre prevalenti non valide."
            )

        maximum = max(occurrences_raw)

        expected_most_present = {
            digit
            for digit, occurrences
            in enumerate(occurrences_raw)
            if (
                occurrences == maximum
                and occurrences > 0
            )
        }

        if most_present != expected_most_present:
            raise ValueError(
                f"{wheel}: cifre prevalenti incoerenti."
            )

        if draws_in_cycle == 0:
            if (
                cycle_start_draw is not None
                or cycle_start_date is not None
                or covered
                or any(occurrences_raw)
            ):
                raise ValueError(
                    f"{wheel}: ciclo vuoto con stato "
                    "residuo."
                )
        else:
            if (
                not isinstance(cycle_start_draw, int)
                or cycle_start_draw <= 0
                or not isinstance(
                    cycle_start_date,
                    str,
                )
            ):
                raise ValueError(
                    f"{wheel}: inizio ciclo non valido."
                )

        seen_wheels.add(wheel)
        seen_orders.add(wheel_order)

    return payload


def read_checkpoint(
    path: Path,
) -> dict[str, object]:
    """Legge e valida un checkpoint JSON."""

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    return validate_checkpoint_payload(payload)


def thaw_wheel_checkpoint(
    checkpoint: WheelCheckpoint,
) -> MutableWheelState:
    """Ricostruisce lo stato mutabile riprendibile."""

    return MutableWheelState(
        wheel=checkpoint.wheel,
        wheel_order=checkpoint.wheel_order,
        latest_draw=checkpoint.latest_draw,
        latest_date=checkpoint.latest_date,
        completed_cycles=(
            checkpoint.completed_cycles
        ),
        synchronized=checkpoint.synchronized,
        draws_in_cycle=checkpoint.draws_in_cycle,
        cycle_start_draw=(
            checkpoint.cycle_start_draw
        ),
        cycle_start_date=(
            checkpoint.cycle_start_date
        ),
        covered_digits=set(
            checkpoint.covered_digits
        ),
        digit_occurrences=list(
            checkpoint.digit_occurrences
        ),
    )


def wheel_checkpoint_from_mapping(
    item: object,
) -> WheelCheckpoint:
    """Converte uno stato JSON già validato."""

    if not isinstance(item, dict):
        raise ValueError(
            "Stato ruota checkpoint non valido."
        )

    return WheelCheckpoint(
        wheel=str(item["wheel"]),
        wheel_order=int(item["wheel_order"]),
        latest_draw=int(item["latest_draw"]),
        latest_date=str(item["latest_date"]),
        completed_cycles=int(
            item["completed_cycles"]
        ),
        synchronized=bool(item["synchronized"]),
        draws_in_cycle=int(
            item["draws_in_cycle"]
        ),
        cycle_start_draw=(
            None
            if item["cycle_start_draw"] is None
            else int(item["cycle_start_draw"])
        ),
        cycle_start_date=(
            None
            if item["cycle_start_date"] is None
            else str(item["cycle_start_date"])
        ),
        covered_digits=tuple(
            int(value)
            for value in item["covered_digits"]
        ),
        missing_digits=tuple(
            int(value)
            for value in item["missing_digits"]
        ),
        digit_occurrences=tuple(
            int(value)
            for value
            in item["digit_occurrences"]
        ),
        most_present_digits=tuple(
            int(value)
            for value
            in item["most_present_digits"]
        ),
    )


def states_from_checkpoint(
    payload: object,
) -> dict[str, MutableWheelState]:
    """Ricostruisce tutti gli accumulatori dal JSON."""

    validated = validate_checkpoint_payload(
        payload
    )

    wheels = validated["wheels"]

    if not isinstance(wheels, list):
        raise ValueError(
            "Stati delle ruote assenti."
        )

    checkpoints = tuple(
        wheel_checkpoint_from_mapping(item)
        for item in wheels
    )

    return {
        checkpoint.wheel: thaw_wheel_checkpoint(
            checkpoint
        )
        for checkpoint in checkpoints
    }


def semantic_checkpoint_state(
    checkpoint: WheelCheckpoint,
) -> tuple[object, ...]:
    """
    Restituisce lo stato riprendibile indipendente
    dalla numerazione locale dell'archivio.

    I database annuali, consolidati parziali e complessivi
    possono assegnare progressivi diversi alla stessa data.
    La continuità cronologica usa quindi le date; i numeri
    di estrazione restano metadati descrittivi locali.
    """

    return (
        checkpoint.wheel,
        checkpoint.wheel_order,
        checkpoint.latest_date,
        checkpoint.completed_cycles,
        checkpoint.synchronized,
        checkpoint.draws_in_cycle,
        checkpoint.cycle_start_date,
        checkpoint.covered_digits,
        checkpoint.missing_digits,
        checkpoint.digit_occurrences,
        checkpoint.most_present_digits,
    )
