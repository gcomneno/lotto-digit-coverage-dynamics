from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock

from lotto_digit_coverage.interfaces.gui.bridge import LottoGuiApi
from lotto_digit_coverage.interfaces.gui.research import (
    load_research_payload,
    research_catalog,
)


class GuiResearchTests(unittest.TestCase):
    def test_catalog_declares_descriptive_and_exploratory_reports(self) -> None:
        catalog = research_catalog()

        self.assertEqual(
            [item["id"] for item in catalog],
            ["completion", "validation", "residuals", "twins"],
        )
        self.assertEqual(
            catalog[-1]["interpretation"],
            "exploratory-screen",
        )

    def test_bridge_loads_catalog_and_report_only_on_request(self) -> None:
        root = Path("/tmp/project")
        research_loader = Mock(
            return_value={
                "id": "validation",
                "title": "Calibrazione Markov",
                "interpretation": "descrittivo",
                "source": "data/lotto-2025.sqlite3",
                "metrics": [],
                "tables": [],
                "notes": [],
            }
        )
        catalog_loader = Mock(
            return_value=[
                {
                    "id": "validation",
                    "title": "Calibrazione Markov",
                    "summary": "Confronto descrittivo.",
                    "interpretation": "descriptive-calibration",
                }
            ]
        )
        api = LottoGuiApi(
            root,
            research_loader=research_loader,
            catalog_loader=catalog_loader,
        )

        catalog_response = api.get_research_catalog()
        self.assertTrue(catalog_response["ok"])
        self.assertEqual(
            catalog_response["data"]["reports"][0]["id"],
            "validation",
        )
        research_loader.assert_not_called()

        report_response = api.get_research_report("validation")
        self.assertTrue(report_response["ok"])
        self.assertEqual(report_response["data"]["id"], "validation")
        research_loader.assert_called_once_with(root, "validation")

    def test_unknown_report_is_rejected_before_any_cli_boundary(self) -> None:
        with self.assertRaisesRegex(ValueError, "sconosciuto"):
            load_research_payload(Path("/tmp/project"), "banana-radioattiva")

    def test_research_error_uses_same_stable_bridge_envelope(self) -> None:
        api = LottoGuiApi(
            Path("/tmp/project"),
            research_loader=Mock(side_effect=FileNotFoundError("archivio assente")),
        )

        response = api.get_research_report("twins")

        self.assertFalse(response["ok"])
        self.assertIsNone(response["data"])
        self.assertEqual(response["error"]["type"], "FileNotFoundError")
        self.assertEqual(response["error"]["message"], "archivio assente")


if __name__ == "__main__":
    unittest.main()
