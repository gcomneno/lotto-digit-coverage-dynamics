"""Backward-compatible imports for Lotto draw repository primitives.

Canonical ownership now lives under ``lotto_digit_coverage``. Existing scripts may
continue importing this module while the remaining verticals are migrated under
issue #9.
"""

from lotto_digit_coverage.application.repositories import (
    DrawRepository,
    RepositoryDataError,
    RepositoryError,
    RepositorySchemaError,
)
from lotto_digit_coverage.domain.draws import (
    DrawSnapshot,
    format_number,
    split_digits,
)
from lotto_digit_coverage.infrastructure.sqlite_lotto_repository import (
    SQLiteLottoRepository,
)


LottoRepository = SQLiteLottoRepository

__all__ = [
    "DrawRepository",
    "DrawSnapshot",
    "LottoRepository",
    "RepositoryDataError",
    "RepositoryError",
    "RepositorySchemaError",
    "SQLiteLottoRepository",
    "format_number",
    "split_digits",
]
