"""Validated application contract for natural-language Lotto exploration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol


WHEELS = (
    "Bari",
    "Cagliari",
    "Firenze",
    "Genova",
    "Milano",
    "Napoli",
    "Palermo",
    "Roma",
    "Torino",
    "Venezia",
    "Nazionale",
)
_ALLOWED_FIELDS = frozenset(
    {
        "operation",
        "wheel",
        "numbers",
        "digits",
        "order",
        "highlight",
        "limit",
        "from_draw",
        "to_draw",
    }
)


class NaturalQueryError(ValueError):
    """Raised when an AI-produced intent is unsupported or invalid."""


@dataclass(frozen=True)
class DrawHistoryIntent:
    operation: str
    wheel: str
    numbers: tuple[int, ...]
    digits: tuple[int, ...]
    order: str
    highlight: bool
    limit: int | None
    from_draw: int | None
    to_draw: int | None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "DrawHistoryIntent":
        extras = set(raw) - _ALLOWED_FIELDS
        missing = _ALLOWED_FIELDS - set(raw)
        if extras or missing:
            details = []
            if missing:
                details.append("campi mancanti: " + ", ".join(sorted(missing)))
            if extras:
                details.append("campi non supportati: " + ", ".join(sorted(extras)))
            raise NaturalQueryError("intent non valido: " + "; ".join(details))

        operation = raw["operation"]
        if operation != "draw_history":
            raise NaturalQueryError(
                f"operazione non supportata: {operation!r}; attesa 'draw_history'."
            )

        wheel = raw["wheel"]
        if not isinstance(wheel, str) or wheel not in WHEELS:
            raise NaturalQueryError(f"ruota non valida: {wheel!r}.")

        numbers = _bounded_integer_sequence(raw["numbers"], "numbers", 1, 90)
        digits = _bounded_integer_sequence(raw["digits"], "digits", 0, 9)

        order = raw["order"]
        if order not in {"ascending", "descending"}:
            raise NaturalQueryError(
                "order deve essere 'ascending' oppure 'descending'."
            )

        highlight = raw["highlight"]
        if not isinstance(highlight, bool):
            raise NaturalQueryError("highlight deve essere booleano.")

        limit = _optional_positive_integer(raw["limit"], "limit")
        from_draw = _optional_positive_integer(raw["from_draw"], "from_draw")
        to_draw = _optional_positive_integer(raw["to_draw"], "to_draw")
        if from_draw is not None and to_draw is not None and from_draw > to_draw:
            raise NaturalQueryError("from_draw non può essere maggiore di to_draw.")

        return cls(
            operation="draw_history",
            wheel=wheel,
            numbers=numbers,
            digits=digits,
            order=order,
            highlight=highlight,
            limit=limit,
            from_draw=from_draw,
            to_draw=to_draw,
        )


@dataclass(frozen=True)
class DrawHistoryRow:
    draw_number: int
    draw_date: str
    numbers: tuple[int, ...]


class DrawHistoryRepository(Protocol):
    def load_wheel_history(
        self,
        wheel: str,
        *,
        from_draw: int | None,
        to_draw: int | None,
    ) -> Sequence[DrawHistoryRow]: ...


def execute_draw_history(
    intent: DrawHistoryIntent,
    repository: DrawHistoryRepository,
) -> tuple[DrawHistoryRow, ...]:
    rows = list(
        repository.load_wheel_history(
            intent.wheel,
            from_draw=intent.from_draw,
            to_draw=intent.to_draw,
        )
    )
    rows.sort(key=lambda row: row.draw_number, reverse=intent.order == "descending")
    if intent.limit is not None:
        rows = rows[: intent.limit]
    return tuple(rows)


def _bounded_integer_sequence(
    value: object,
    field: str,
    minimum: int,
    maximum: int,
) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise NaturalQueryError(f"{field} deve essere una lista.")

    normalized: set[int] = set()
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            raise NaturalQueryError(f"{field} deve contenere solo interi.")
        if not minimum <= item <= maximum:
            raise NaturalQueryError(
                f"{field} contiene {item}, fuori dall'intervallo {minimum}–{maximum}."
            )
        normalized.add(item)
    return tuple(sorted(normalized))


def _optional_positive_integer(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise NaturalQueryError(f"{field} deve essere un intero positivo o null.")
    return value
