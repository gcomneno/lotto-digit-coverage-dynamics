"""GiadaWare AI adapter for presentation-only dynamic translation."""

from __future__ import annotations

from typing import Protocol

from lotto_digit_coverage.infrastructure.giadaware_ai_query import (
    build_default_giadaware_backend,
)


_LANGUAGE_NAMES = {
    "en": "English",
    "it": "Italian",
}


class TranslationResultLike(Protocol):
    translated_text: str


class TranslationCapabilities(Protocol):
    def translate_text(
        self,
        text: str,
        *,
        source_language: str,
        target_language: str,
    ) -> TranslationResultLike: ...


class GiadaWareAIDynamicPresentationTranslator:
    """Adapt GiadaWare AI semantic translation to the product presentation port."""

    def __init__(self, capabilities: TranslationCapabilities) -> None:
        self._capabilities = capabilities

    def translate(
        self,
        text: str,
        *,
        source_locale: str,
        target_locale: str,
    ) -> str:
        try:
            source_language = _LANGUAGE_NAMES[source_locale]
            target_language = _LANGUAGE_NAMES[target_locale]
        except KeyError as error:
            raise ValueError(f"unsupported translation locale: {error.args[0]}") from error

        result = self._capabilities.translate_text(
            text,
            source_language=source_language,
            target_language=target_language,
        )
        translated = result.translated_text
        if not isinstance(translated, str) or not translated.strip():
            raise ValueError("GiadaWare AI returned an empty translation")
        return translated


def build_default_dynamic_presentation_translator() -> GiadaWareAIDynamicPresentationTranslator:
    """Build the default GiadaWare AI semantic translation adapter lazily."""

    try:
        from giadaware_ai import AICapabilities
    except ImportError as error:
        raise RuntimeError(
            "GiadaWare AI is unavailable in the Python environment used by the GUI."
        ) from error

    return GiadaWareAIDynamicPresentationTranslator(
        AICapabilities(build_default_giadaware_backend())
    )
