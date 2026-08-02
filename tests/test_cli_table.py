from __future__ import annotations

import unittest
from dataclasses import dataclass

from strategies.cli_table import Column


@dataclass(frozen=True)
class ExampleRow:
    value: int


class ColumnTests(unittest.TestCase):
    def test_describes_and_reads_a_column(
        self,
    ) -> None:
        column = Column[ExampleRow](
            key="value",
            label="Valore",
            getter=lambda row: row.value,
        )

        self.assertEqual(column.key, "value")
        self.assertEqual(column.label, "Valore")
        self.assertEqual(
            column.getter(ExampleRow(value=42)),
            42,
        )

    def test_is_immutable(
        self,
    ) -> None:
        column = Column[ExampleRow](
            key="value",
            label="Valore",
            getter=lambda row: row.value,
        )

        with self.assertRaises(
            AttributeError
        ):
            column.key = "other"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
