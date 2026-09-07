"""Presentation-only translation of dynamic research payloads."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Sequence

from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    SUPPORTED_LOCALES,
    DynamicPresentationTranslator,
)


@dataclass(frozen=True)
class DynamicResearchPresentation:
    payload: Any
    requested_locale: str
    resolved_locale: str
    fell_back: bool
    fallback_reason: str | None = None


def localize_research_catalog(
    catalog: Sequence[dict[str, str]],
    *,
    locale: str,
    translator: DynamicPresentationTranslator | None = None,
) -> DynamicResearchPresentation:
    canonical = deepcopy(list(catalog))
    if locale == CANONICAL_LOCALE:
        return DynamicResearchPresentation(canonical, locale, CANONICAL_LOCALE, False)
    if locale not in SUPPORTED_LOCALES:
        return DynamicResearchPresentation(
            canonical,
            locale,
            CANONICAL_LOCALE,
            True,
            "unsupported-locale",
        )
    if translator is None:
        return DynamicResearchPresentation(
            canonical,
            locale,
            CANONICAL_LOCALE,
            True,
            "translator-unavailable",
        )

    translated = deepcopy(canonical)
    try:
        for item in translated:
            item["title"] = _translate(item["title"], locale, translator)
            item["summary"] = _translate(item["summary"], locale, translator)
    except Exception:
        return DynamicResearchPresentation(
            canonical,
            locale,
            CANONICAL_LOCALE,
            True,
            "translation-failed",
        )
    return DynamicResearchPresentation(translated, locale, locale, False)


def localize_research_payload(
    payload: dict[str, Any],
    *,
    locale: str,
    translator: DynamicPresentationTranslator | None = None,
) -> DynamicResearchPresentation:
    canonical = deepcopy(payload)
    if locale == CANONICAL_LOCALE:
        return DynamicResearchPresentation(canonical, locale, CANONICAL_LOCALE, False)
    if locale not in SUPPORTED_LOCALES:
        return DynamicResearchPresentation(
            canonical,
            locale,
            CANONICAL_LOCALE,
            True,
            "unsupported-locale",
        )
    if translator is None:
        return DynamicResearchPresentation(
            canonical,
            locale,
            CANONICAL_LOCALE,
            True,
            "translator-unavailable",
        )

    translated = deepcopy(canonical)
    try:
        translated["title"] = _translate(translated["title"], locale, translator)
        translated["interpretation"] = _translate(
            translated["interpretation"], locale, translator
        )
        for metric in translated.get("metrics", []):
            metric["label"] = _translate(metric["label"], locale, translator)
        for table in translated.get("tables", []):
            table["title"] = _translate(table["title"], locale, translator)
            for column in table.get("columns", []):
                column["label"] = _translate(column["label"], locale, translator)
        translated["notes"] = [
            _translate(note, locale, translator) for note in translated.get("notes", [])
        ]
    except Exception:
        return DynamicResearchPresentation(
            canonical,
            locale,
            CANONICAL_LOCALE,
            True,
            "translation-failed",
        )
    return DynamicResearchPresentation(translated, locale, locale, False)


def _translate(
    text: str,
    locale: str,
    translator: DynamicPresentationTranslator,
) -> str:
    translated = translator.translate(
        text,
        source_locale=CANONICAL_LOCALE,
        target_locale=locale,
    )
    if not isinstance(translated, str) or not translated.strip():
        raise ValueError("dynamic translation must return non-empty text")
    return translated
