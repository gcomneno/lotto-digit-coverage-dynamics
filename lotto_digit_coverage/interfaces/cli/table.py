"""Reusable primitives for tabular CLI interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar


RowT = TypeVar("RowT")


@dataclass(frozen=True)
class Column(Generic[RowT]):
    """Describe one column exposed by a tabular CLI report."""

    key: str
    label: str
    getter: Callable[[RowT], object]
