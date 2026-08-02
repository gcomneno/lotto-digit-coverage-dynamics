"""Primitive riusabili per le interfacce tabellari CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar


RowT = TypeVar("RowT")


@dataclass(frozen=True)
class Column(Generic[RowT]):
    """Descrive una colonna esposta da un report tabellare."""

    key: str
    label: str
    getter: Callable[[RowT], object]
