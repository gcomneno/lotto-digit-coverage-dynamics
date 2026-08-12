#!/usr/bin/env python3

"""Compatibility entry point for the direct database CLI adapter."""

from lotto_digit_coverage.interfaces.cli.database_command import main


if __name__ == "__main__":
    raise SystemExit(main())
