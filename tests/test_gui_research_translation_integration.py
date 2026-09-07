from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

from lotto_digit_coverage.interfaces.gui.bridge import LottoGuiApi


CATALOG = [
    {
        "id": "twins",
        "title": "Twin numbers 11–88",
        "summary": "One-step exploratory screen.",
        "interpretation": "exploratory-screen",
    }
]

REPORT = {
    "id": "twins",
    "title": "Twin numbers 11–88",
    "interpretation": "Exploratory interpretation.",
    "source": "data/lotto.sqlite3",
    "metrics": [
        {"label": "Observations", "value": 42, "format": "integer"},
    ],
    "tables": [
        {
            "title": "Screen by condition and twin",
            "columns": [
                {"key": "condition", "label": "Condition", "format": "text"},
                {"key": "candidate", "label": "Outcome", "format": "candidate"},
            ],
            "rows": [
                {"condition": "missing", "candidate": True},
                {"condition": "baseline", "candidate": False},
            ],
        }
    ],
    "notes": ["Keep this meaning unchanged."],
}


class PrefixTranslator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def translate(self, text: str, *, source_locale: str, target_locale: str) -> str:
        self.calls.append((text, source_locale, target_locale))
        return f"IT:{text}"


class GuiResearchTranslationIntegrationTests(unittest.TestCase):
    def test_italian_is_applied_after_canonical_loaders_without_changing_structured_data(self) -> None:
        root = Path("/tmp/project")
        catalog_loader = Mock(return_value=deepcopy(CATALOG))
        research_loader = Mock(return_value=deepcopy(REPORT))
        translator = PrefixTranslator()
        translator_factory = Mock(return_value=translator)
        api = LottoGuiApi(
            root,
            catalog_loader=catalog_loader,
            research_loader=research_loader,
            dynamic_translator_factory=translator_factory,
        )

        catalog_response = api.get_research_catalog("it")
        report_response = api.get_research_report("twins", "it")

        self.assertTrue(catalog_response["ok"])
        self.assertTrue(report_response["ok"])
        self.assertEqual(catalog_response["data"]["reports"][0]["title"], "IT:Twin numbers 11–88")
        self.assertEqual(report_response["data"]["title"], "IT:Twin numbers 11–88")
        self.assertEqual(report_response["data"]["metrics"][0]["label"], "IT:Observations")

        self.assertEqual(report_response["data"]["id"], REPORT["id"])
        self.assertEqual(report_response["data"]["source"], REPORT["source"])
        self.assertEqual(report_response["data"]["metrics"][0]["value"], 42)
        self.assertEqual(report_response["data"]["metrics"][0]["format"], "integer")
        self.assertEqual(report_response["data"]["tables"][0]["columns"][0]["key"], "condition")
        self.assertEqual(report_response["data"]["tables"][0]["rows"], REPORT["tables"][0]["rows"])
        self.assertEqual(catalog_response["data"]["reports"][0]["id"], "twins")
        self.assertEqual(catalog_response["data"]["reports"][0]["interpretation"], "exploratory-screen")

        catalog_loader.assert_called_once_with()
        research_loader.assert_called_once_with(root, "twins")
        self.assertEqual(translator_factory.call_count, 2)
        self.assertEqual(catalog_response["presentation"]["requested_locale"], "it")
        self.assertEqual(catalog_response["presentation"]["resolved_locale"], "it")
        self.assertFalse(catalog_response["presentation"]["fell_back"])
        self.assertEqual(report_response["presentation"]["resolved_locale"], "it")

    def test_english_short_circuits_without_building_giadaware_translator(self) -> None:
        translator_factory = Mock(side_effect=AssertionError("must not be built"))
        api = LottoGuiApi(
            Path("/tmp/project"),
            catalog_loader=Mock(return_value=deepcopy(CATALOG)),
            research_loader=Mock(return_value=deepcopy(REPORT)),
            dynamic_translator_factory=translator_factory,
        )

        catalog_response = api.get_research_catalog("en")
        report_response = api.get_research_report("twins", "en")

        self.assertEqual(catalog_response["data"]["reports"], CATALOG)
        self.assertEqual(report_response["data"], REPORT)
        self.assertEqual(catalog_response["presentation"]["resolved_locale"], "en")
        self.assertFalse(catalog_response["presentation"]["fell_back"])
        self.assertEqual(report_response["presentation"]["resolved_locale"], "en")
        translator_factory.assert_not_called()

    def test_unavailable_giadaware_translator_is_visible_fallback_not_application_error(self) -> None:
        catalog_loader = Mock(return_value=deepcopy(CATALOG))
        research_loader = Mock(return_value=deepcopy(REPORT))
        translator_factory = Mock(side_effect=RuntimeError("GiadaWare AI unavailable"))
        api = LottoGuiApi(
            Path("/tmp/project"),
            catalog_loader=catalog_loader,
            research_loader=research_loader,
            dynamic_translator_factory=translator_factory,
        )

        response = api.get_research_report("twins", "it")

        self.assertTrue(response["ok"])
        self.assertIsNone(response["error"])
        self.assertEqual(response["data"], REPORT)
        self.assertEqual(
            response["presentation"],
            {
                "requested_locale": "it",
                "resolved_locale": "en",
                "fell_back": True,
                "fallback_reason": "translator-unavailable",
            },
        )
        research_loader.assert_called_once_with(Path("/tmp/project"), "twins")

    def test_unsupported_locale_does_not_build_translator_or_change_loader_inputs(self) -> None:
        research_loader = Mock(return_value=deepcopy(REPORT))
        translator_factory = Mock(side_effect=AssertionError("must not be built"))
        api = LottoGuiApi(
            Path("/tmp/project"),
            research_loader=research_loader,
            dynamic_translator_factory=translator_factory,
        )

        response = api.get_research_report("twins", "fr")

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"], REPORT)
        self.assertEqual(response["presentation"]["fallback_reason"], "unsupported-locale")
        research_loader.assert_called_once_with(Path("/tmp/project"), "twins")
        translator_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
