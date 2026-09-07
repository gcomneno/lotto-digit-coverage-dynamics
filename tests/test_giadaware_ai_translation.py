from __future__ import annotations

import sys
import types
import unittest
from dataclasses import dataclass
from unittest.mock import Mock, patch

from lotto_digit_coverage.infrastructure.giadaware_ai_translation import (
    GiadaWareAIDynamicPresentationTranslator,
    build_default_dynamic_presentation_translator,
)


@dataclass(frozen=True)
class FakeTranslationResult:
    translated_text: str


class RecordingCapabilities:
    def __init__(self, translated_text: str = "Traduzione") -> None:
        self.translated_text = translated_text
        self.calls: list[tuple[str, str, str]] = []

    def translate_text(
        self,
        text: str,
        *,
        source_language: str,
        target_language: str,
    ) -> FakeTranslationResult:
        self.calls.append((text, source_language, target_language))
        return FakeTranslationResult(self.translated_text)


class GiadaWareAITranslationAdapterTests(unittest.TestCase):
    def test_adapter_maps_product_locales_to_giadaware_language_labels(self) -> None:
        capabilities = RecordingCapabilities("Completamento dei cicli")
        translator = GiadaWareAIDynamicPresentationTranslator(capabilities)

        translated = translator.translate(
            "Cycle completion",
            source_locale="en",
            target_locale="it",
        )

        self.assertEqual(translated, "Completamento dei cicli")
        self.assertEqual(
            capabilities.calls,
            [("Cycle completion", "English", "Italian")],
        )

    def test_adapter_rejects_unknown_locale_before_semantic_call(self) -> None:
        capabilities = RecordingCapabilities()
        translator = GiadaWareAIDynamicPresentationTranslator(capabilities)

        with self.assertRaisesRegex(ValueError, "unsupported translation locale"):
            translator.translate(
                "Cycle completion",
                source_locale="en",
                target_locale="fr",
            )

        self.assertEqual(capabilities.calls, [])

    def test_adapter_rejects_empty_translation_result(self) -> None:
        translator = GiadaWareAIDynamicPresentationTranslator(RecordingCapabilities("   "))

        with self.assertRaisesRegex(ValueError, "empty translation"):
            translator.translate(
                "Cycle completion",
                source_locale="en",
                target_locale="it",
            )

    def test_default_builder_wraps_giadaware_capabilities_over_fake_backend(self) -> None:
        fake_backend = object()
        capability_instances: list[object] = []

        class FakeAICapabilities:
            def __init__(self, backend: object) -> None:
                self.backend = backend
                capability_instances.append(self)

            def translate_text(
                self,
                text: str,
                *,
                source_language: str,
                target_language: str,
            ) -> FakeTranslationResult:
                return FakeTranslationResult(
                    f"{source_language}->{target_language}:{text}"
                )

        fake_module = types.ModuleType("giadaware_ai")
        fake_module.AICapabilities = FakeAICapabilities

        with patch.dict(sys.modules, {"giadaware_ai": fake_module}):
            with patch(
                "lotto_digit_coverage.infrastructure.giadaware_ai_translation."
                "build_default_giadaware_backend",
                Mock(return_value=fake_backend),
            ) as backend_builder:
                translator = build_default_dynamic_presentation_translator()

        self.assertEqual(len(capability_instances), 1)
        self.assertIs(capability_instances[0].backend, fake_backend)
        backend_builder.assert_called_once_with()
        self.assertEqual(
            translator.translate(
                "Cycle completion",
                source_locale="en",
                target_locale="it",
            ),
            "English->Italian:Cycle completion",
        )


if __name__ == "__main__":
    unittest.main()
