"""Backward-compatible import for legacy CLI table helpers.

New interface code should import from
``lotto_digit_coverage.interfaces.cli.table``. The compatibility module remains
in place while existing scripts are migrated incrementally under issue #9.
"""

from lotto_digit_coverage.interfaces.cli.table import Column

__all__ = ["Column"]
