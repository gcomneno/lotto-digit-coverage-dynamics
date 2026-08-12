"""Presentation-neutral repository contracts used by application services."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from lotto_digit_coverage.domain.draws import DrawSnapshot


class RepositoryError(RuntimeError):
    """Base failure exposed by data repositories to application code."""


class RepositorySchemaError(RepositoryError):
    """The backing store does not provide the required read model."""


class RepositoryDataError(RepositoryError):
    """Stored draw data violate an application-facing repository invariant."""


@runtime_checkable
class DrawRepository(Protocol):
    """Read-only access required by draw-based analysis use cases."""

    def latest_draw(self) -> tuple[int, str]:
        """Return ``(draw_number, draw_date)`` for the latest dated draw."""

    def resolve_draw_number(self, draw_number: int) -> tuple[int, str]:
        """Resolve an unambiguous draw number to its dated draw key."""

    def latest_complete_draw(
        self,
        required_wheels: Sequence[str],
    ) -> tuple[int, str]:
        """Return the latest draw complete for every required wheel."""

    def draws_by_wheel(
        self,
        *,
        through: tuple[int, str] | None = None,
    ) -> dict[str, tuple[DrawSnapshot, ...]]:
        """Return complete wheel draws, optionally through an inclusive draw key."""
