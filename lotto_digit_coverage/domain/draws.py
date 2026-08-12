"""Domain values and number primitives for Lotto draws."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DrawSnapshot:
    """Five numbers drawn on one wheel at one draw."""

    draw_number: int
    draw_date: str
    wheel: str
    wheel_order: int
    numbers: tuple[int, ...]


def format_number(value: int) -> str:
    """Render a Lotto number as its two-digit decimal representation."""

    if not 1 <= value <= 90:
        raise ValueError(
            f"Numero del Lotto fuori intervallo 1–90: {value}"
        )

    return f"{value:02d}"


def split_digits(value: int) -> tuple[int, int]:
    """Split a Lotto number into its two digits, preserving a leading zero."""

    formatted = format_number(value)
    return int(formatted[0]), int(formatted[1])
