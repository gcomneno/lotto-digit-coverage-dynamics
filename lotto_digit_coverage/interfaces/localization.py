"""Deterministic presentation localization contract.

Localization is an interface concern. Domain and application services must not
receive locale state or depend on translated presentation strings.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


CANONICAL_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "it")


_ENGLISH_CATALOG: Mapping[str, str] = {
    "common.error_prefix": "ERROR",
    "common.loading": "Loading…",
    "common.optional": "optional",
}

_ITALIAN_CATALOG: Mapping[str, str] = {
    "common.error_prefix": "ERRORE",
    "common.loading": "Caricamento…",
    "common.optional": "opzionale",
}


@dataclass(frozen=True)
class LocalizedText:
    """Resolved presentation text plus explicit fallback evidence."""

    key: str
    text: str
    requested_locale: str
    resolved_locale: str
    fell_back: bool
    fallback_reason: str | None = None


class PresentationCatalog:
    """Resolve deterministic static presentation strings.

    English is authoritative. Derived catalogs may omit keys; missing derived
    values fall back to the canonical English text with explicit metadata.
    Unsupported locale identifiers also fall back to English.
    """

    def __init__(
        self,
        *,
        canonical: Mapping[str, str],
        derived: Mapping[str, Mapping[str, str]],
    ) -> None:
        self._canonical = dict(canonical)
        self._derived = {locale: dict(values) for locale, values in derived.items()}

    def resolve(self, key: str, locale: str = CANONICAL_LOCALE) -> LocalizedText:
        try:
            canonical_text = self._canonical[key]
        except KeyError as error:
            raise KeyError(f"unknown canonical presentation key: {key}") from error

        if locale == CANONICAL_LOCALE:
            return LocalizedText(
                key=key,
                text=canonical_text,
                requested_locale=locale,
                resolved_locale=CANONICAL_LOCALE,
                fell_back=False,
            )

        if locale not in SUPPORTED_LOCALES:
            return LocalizedText(
                key=key,
                text=canonical_text,
                requested_locale=locale,
                resolved_locale=CANONICAL_LOCALE,
                fell_back=True,
                fallback_reason="unsupported-locale",
            )

        translated = self._derived.get(locale, {}).get(key)
        if translated is None:
            return LocalizedText(
                key=key,
                text=canonical_text,
                requested_locale=locale,
                resolved_locale=CANONICAL_LOCALE,
                fell_back=True,
                fallback_reason="missing-translation",
            )

        return LocalizedText(
            key=key,
            text=translated,
            requested_locale=locale,
            resolved_locale=locale,
            fell_back=False,
        )


DEFAULT_PRESENTATION_CATALOG = PresentationCatalog(
    canonical=_ENGLISH_CATALOG,
    derived={"it": _ITALIAN_CATALOG},
)


class DynamicPresentationTranslator(Protocol):
    """Provider-independent boundary for eligible dynamic human-readable text.

    Concrete GiadaWare AI integration is intentionally outside this module and
    outside the static catalog path.
    """

    def translate(
        self,
        text: str,
        *,
        source_locale: str,
        target_locale: str,
    ) -> str: ...
