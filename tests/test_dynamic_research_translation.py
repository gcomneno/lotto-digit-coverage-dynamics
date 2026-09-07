from __future__ import annotations

import unittest

from lotto_digit_coverage.interfaces.gui.research import RESEARCH_CATALOG
from lotto_digit_coverage.interfaces.gui.research_translation import (
    localize_research_catalog,
    localize_research_payload,
)


class RecordingTranslator:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.fail_on = fail_on

    def translate(self, text: str, *, source_locale: str, target_locale: str) -> str:
        self.calls.append((text, source_locale, target_locale))
        if self.fail_on is not None and self.fail_on in text:
            raise RuntimeError("translation failed")
        return f"IT:{text}"


PAYLOAD = {
    "id": "twins",
    "title": "Twin numbers 11–88",
    "interpretation": "Exploratory interpretation.",
    "source": "data/lotto.sqlite3",
    "metrics": [
        {"label": "Observations", "value": 42, "format": "integer"},
        {"label": "Candidate rate", "value": 0.25, "format": "percentage"},
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


class DynamicResearchTranslationTests(unittest.TestCase):
    def test_research_catalog_is_canonical_english(self) -> None:
        self.assertEqual(RESEARCH_CATALOG[0]["title"], "Cycle completion")
        self.assertEqual(
            RESEARCH_CATALOG[0]["summary"],
            "One-step probability and residual distance by coverage state.",
        )
        self.assertEqual(RESEARCH_CATALOG[3]["id"], "twins")
        self.assertEqual(RESEARCH_CATALOG[3]["interpretation"], "exploratory-screen")

    def test_english_short_circuits_without_translator_calls(self) -> None:
        translator = RecordingTranslator()
        result = localize_research_payload(PAYLOAD, locale="en", translator=translator)

        self.assertEqual(result.payload, PAYLOAD)
        self.assertEqual(result.resolved_locale, "en")
        self.assertFalse(result.fell_back)
        self.assertEqual(translator.calls, [])

    def test_italian_translates_only_eligible_dynamic_fields(self) -> None:
        translator = RecordingTranslator()
        result = localize_research_payload(PAYLOAD, locale="it", translator=translator)

        translated = result.payload
        self.assertEqual(translated["title"], "IT:Twin numbers 11–88")
        self.assertEqual(translated["interpretation"], "IT:Exploratory interpretation.")
        self.assertEqual(translated["metrics"][0]["label"], "IT:Observations")
        self.assertEqual(translated["tables"][0]["title"], "IT:Screen by condition and twin")
        self.assertEqual(translated["tables"][0]["columns"][0]["label"], "IT:Condition")
        self.assertEqual(translated["notes"], ["IT:Keep this meaning unchanged."])

        self.assertEqual(translated["id"], PAYLOAD["id"])
        self.assertEqual(translated["source"], PAYLOAD["source"])
        self.assertEqual(translated["metrics"][0]["value"], PAYLOAD["metrics"][0]["value"])
        self.assertEqual(translated["metrics"][0]["format"], PAYLOAD["metrics"][0]["format"])
        self.assertEqual(translated["tables"][0]["columns"][0]["key"], "condition")
        self.assertEqual(translated["tables"][0]["columns"][0]["format"], "text")
        self.assertEqual(translated["tables"][0]["rows"], PAYLOAD["tables"][0]["rows"])
        self.assertEqual(PAYLOAD["title"], "Twin numbers 11–88")
        self.assertFalse(result.fell_back)
        self.assertEqual(result.resolved_locale, "it")

    def test_catalog_translates_title_and_summary_not_id_or_interpretation_tag(self) -> None:
        translator = RecordingTranslator()
        result = localize_research_catalog(RESEARCH_CATALOG, locale="it", translator=translator)

        self.assertEqual(result.payload[0]["title"], "IT:Cycle completion")
        self.assertTrue(result.payload[0]["summary"].startswith("IT:"))
        self.assertEqual(result.payload[0]["id"], "completion")
        self.assertEqual(result.payload[0]["interpretation"], "descriptive")

    def test_translation_failure_falls_back_to_whole_canonical_payload(self) -> None:
        translator = RecordingTranslator(fail_on="Condition")
        result = localize_research_payload(PAYLOAD, locale="it", translator=translator)

        self.assertEqual(result.payload, PAYLOAD)
        self.assertTrue(result.fell_back)
        self.assertEqual(result.resolved_locale, "en")
        self.assertEqual(result.fallback_reason, "translation-failed")

    def test_missing_translator_and_unsupported_locale_fall_back_to_english(self) -> None:
        unavailable = localize_research_payload(PAYLOAD, locale="it")
        unsupported = localize_research_payload(PAYLOAD, locale="fr", translator=RecordingTranslator())

        self.assertEqual(unavailable.payload, PAYLOAD)
        self.assertEqual(unavailable.fallback_reason, "translator-unavailable")
        self.assertEqual(unsupported.payload, PAYLOAD)
        self.assertEqual(unsupported.fallback_reason, "unsupported-locale")


if __name__ == "__main__":
    unittest.main()
