from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock

from lotto_digit_coverage.domain.draws import DrawSnapshot
from lotto_digit_coverage.interfaces.gui.bridge import (
    LottoGuiApi,
    _occurrence_input,
)


class GuiBridgeTests(unittest.TestCase):
    def test_capabilities_expose_versioned_application_contracts(self) -> None:
        catalog_loader = Mock(
            return_value=[
                {"id": "completion", "title": "Completion"},
                {"id": "twins", "title": "Twins"},
            ]
        )
        api = LottoGuiApi(Path("/tmp/project"), catalog_loader=catalog_loader)

        response = api.get_capabilities()

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["bridge_version"], 2)
        self.assertEqual(
            response["data"]["contracts"],
            [
                {"schema": "lotto.current", "version": 1},
                {"schema": "lotto.occurrence-groups", "version": 1},
            ],
        )
        self.assertEqual(
            response["data"]["research_reports"],
            ["completion", "twins"],
        )
        catalog_loader.assert_called_once_with()

    def test_current_forwards_structured_arguments_and_wraps_payload(self) -> None:
        loader = Mock(
            return_value={
                "schema": "lotto.current",
                "schema_version": 1,
            }
        )
        root = Path("/tmp/project")
        api = LottoGuiApi(root, current_loader=loader)

        response = api.get_current(
            "data/test.sqlite3",
            127,
            None,
            False,
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["schema"], "lotto.current")
        loader.assert_called_once_with(
            root=root,
            database="data/test.sqlite3",
            to_draw_number=127,
            to_date=None,
            use_checkpoint=False,
        )

    def test_occurrence_bridge_uses_default_database_when_js_passes_none(self) -> None:
        loader = Mock(
            return_value={
                "schema": "lotto.occurrence-groups",
                "schema_version": 1,
            }
        )
        root = Path("/tmp/project")
        api = LottoGuiApi(root, occurrence_loader=loader)

        response = api.get_occurrence_groups(None, 6, 128)

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["schema"], "lotto.occurrence-groups")
        loader.assert_called_once_with(
            root=root,
            database="data/lotto-current.sqlite3",
            group_size=6,
            requested_draw_number=128,
        )

    def test_bridge_normalizes_errors_without_terminal_output(self) -> None:
        loader = Mock(side_effect=ValueError("cutoff non valido"))
        api = LottoGuiApi(Path("/tmp/project"), current_loader=loader)

        response = api.get_current()

        self.assertFalse(response["ok"])
        self.assertIsNone(response["data"])
        self.assertEqual(response["error"]["type"], "ValueError")
        self.assertEqual(response["error"]["message"], "cutoff non valido")

    def test_occurrence_input_preserves_wheel_order_and_integer_numbers(self) -> None:
        draws_by_wheel = {
            "Roma": (
                DrawSnapshot(1, "2026-01-01", "Roma", 8, (1, 2, 3, 4, 5)),
            ),
            "Bari": (
                DrawSnapshot(1, "2026-01-01", "Bari", 1, (6, 7, 8, 9, 10)),
            ),
        }

        draws, wheels = _occurrence_input(draws_by_wheel)

        self.assertEqual(wheels, ("Bari", "Roma"))
        self.assertEqual(
            draws[(1, "2026-01-01")],
            {
                "Bari": (6, 7, 8, 9, 10),
                "Roma": (1, 2, 3, 4, 5),
            },
        )


if __name__ == "__main__":
    unittest.main()
