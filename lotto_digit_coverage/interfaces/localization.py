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
    "cli.ask.description": (
        "Interpret a natural-language request through GiadaWare AI and execute "
        "it as a deterministic, read-only Lotto query."
    ),
    "cli.ask.database_help": "SQLite database to query.",
    "cli.ask.language_help": "Presentation language.",
    "cli.ask.request_help": "Natural-language request.",
    "cli.ask.database_label": "Database",
    "cli.ask.wheel_label": "Wheel",
    "cli.ask.order_label": "Order",
    "cli.ask.draw_header": "Draw",
    "cli.ask.date_header": "Date",
    "cli.ask.numbers_header": "Numbers",
    "cli.current.description": (
        "Compute current coverage state, Markov maturity and A1-A4 anomalies "
        "for natural coverage cycles."
    ),
    "cli.current.checkpoint_help": (
        "Explicit historical checkpoint. When omitted, select the checkpoint "
        "compatible with the database year automatically."
    ),
    "cli.current.without_checkpoint_help": (
        "Disable historical resume and rebuild state only from the selected database."
    ),
    "cli.current.database_help": "SQLite database to analyze.",
    "cli.current.language_help": "Presentation language.",
    "cli.current.to_help": "Stop at the latest draw not later than the given date.",
    "cli.current.to_num_help": "Stop at the latest draw whose number is not greater than N.",
    "cli.current.checkpoint_label": "Historical checkpoint",
    "cli.current.disabled": "disabled",
    "cli.current.until": "through",
    "cli.current.time_limit": "Time limit",
    "cli.current.draw_limit": "Draw limit",
    "cli.current.inclusive": "inclusive",
    "cli.current.latest_draw": "Latest draw",
    "cli.current.of": "of",
    "cli.current.markov_title": "===== COVERAGE MARKOV METER =====",
    "cli.current.markov_state": "State: digits still missing in the current natural cycle.",
    "cli.current.markov_ranking": (
        "Ranking: increasing expected residual waiting time; it does not represent a gambling advantage."
    ),
    "cli.current.markov_top": (
        "Most present: digits with the highest occurrence count in the current cycle."
    ),
    "cli.current.pos": "Pos",
    "cli.current.wheel": "Wheel",
    "cli.current.last": "Last",
    "cli.current.cycles": "Cycles",
    "cli.current.age": "Age",
    "cli.current.most_present": "Most present",
    "cli.current.missing": "Missing",
    "cli.current.within1": "Within 1",
    "cli.current.within2": "Within 2",
    "cli.current.within3": "Within 3",
    "cli.current.within5": "Within 5",
    "cli.current.expected": "Expected",
    "cli.current.coverage_hits_title": "===== COVERAGE-HITS OPERATIONAL SIGNAL =====",
    "cli.current.historical_source": "Historical source",
    "cli.current.coverage_hits_event": (
        "Event: at least max(1, N-1) of the N missing digits on the next draw."
    ),
    "cli.current.coverage_hits_estimate": (
        "Estimate95-: current probability corrected with the Wilson lower bound "
        "of the historical excess."
    ),
    "cli.current.coverage_hits_age_note": "Age is descriptive and does not increase probability.",
    "cli.current.coverage_hits_empty": "No current class is present in the historical summary.",
    "cli.current.class": "Class",
    "cli.current.cases": "Cases",
    "cli.current.historical": "Historical",
    "cli.current.event_probability": "P event",
    "cli.current.estimate95": "Estimate95-",
    "cli.current.first_signal": "First signal",
    "cli.current.at_least": "at least",
    "cli.current.among": "among",
    "cli.current.coverage_hits_note": (
        "Note: a negative lift does not indicate a historical advantage; the ranking "
        "describes the most robust operational signal available."
    ),
    "cli.current.next_draw_title": "===== NEXT DRAW IN DATABASE =====",
    "cli.current.next_draw_note": "Not used in the historical-framework calculations.",
    "cli.current.draw": "Draw",
    "cli.current.digit_legend": "Digit legend",
    "cli.current.top": "TOP",
    "cli.current.numbers": "Numbers",
    "cli.current.anomaly_history_title": "===== A1-A4 ANOMALIES IN DATABASE =====",
    "cli.current.valid_transitions": "Valid transitions",
    "cli.current.observed_events": "Observed events",
    "cli.current.categories": "Categories",
    "cli.current.no_historical_anomalies": "No historical anomaly detected.",
    "cli.current.date": "Date",
    "cli.current.event_probability_header": "P(event)",
    "cli.current.level": "Level",
    "cli.current.signature": "Signature",
    "cli.current.active_anomalies_title": "===== ACTIVE ANOMALIES AT {draw} ({date}) =====",
    "cli.current.no_active_anomalies": "No A1-A4 anomaly is active.",
    "cli.current.active_since": "Active/observed since",
    "cli.consensus.title": "===== CROSS-WHEEL DIGIT CONSENSUS =====",
    "cli.consensus.description": (
        "Descriptive: for each digit, count how many active-cycle wheels still miss it "
        "and how many rank it among the most present digits in the current cycle."
    ),
    "cli.consensus.warning": "It does not combine digits into numbers and does not represent a gambling advantage.",
    "cli.consensus.digit": "Digit",
    "cli.consensus.missing_wheels": "Wheels missing",
    "cli.consensus.top_wheels": "Wheels top",
    "cli.consensus.where_missing": "Missing on",
    "cli.consensus.where_top": "Top on",
    "cli.consensus.empty": "No wheel has an active cycle.",
}

_ITALIAN_CATALOG: Mapping[str, str] = {
    "common.error_prefix": "ERRORE",
    "common.loading": "Caricamento…",
    "common.optional": "opzionale",
    "cli.ask.description": (
        "Interpreta una richiesta naturale tramite GiadaWare AI e la esegue "
        "come query Lotto deterministica e read-only."
    ),
    "cli.ask.database_help": "Database SQLite da consultare.",
    "cli.ask.language_help": "Lingua di presentazione.",
    "cli.ask.request_help": "Richiesta in linguaggio naturale.",
    "cli.ask.database_label": "Database",
    "cli.ask.wheel_label": "Ruota",
    "cli.ask.order_label": "Ordine",
    "cli.ask.draw_header": "Estr",
    "cli.ask.date_header": "Data",
    "cli.ask.numbers_header": "Numeri",
    "cli.current.description": (
        "Calcola lo stato corrente, la maturità Markov e le anomalie A1-A4 "
        "dei cicli naturali di copertura."
    ),
    "cli.current.checkpoint_help": (
        "Checkpoint storico esplicito. In assenza viene selezionato automaticamente "
        "quello compatibile con l'anno del database."
    ),
    "cli.current.without_checkpoint_help": (
        "Disabilita la ripresa storica e ricostruisce lo stato soltanto dal database indicato."
    ),
    "cli.current.database_help": "Database SQLite da analizzare.",
    "cli.current.language_help": "Lingua di presentazione.",
    "cli.current.to_help": "Ferma l'analisi all'ultima estrazione non successiva alla data indicata.",
    "cli.current.to_num_help": "Ferma l'analisi all'ultima estrazione con numero non superiore a N.",
    "cli.current.checkpoint_label": "Checkpoint storico",
    "cli.current.disabled": "disabilitato",
    "cli.current.until": "fino al",
    "cli.current.time_limit": "Limite temporale",
    "cli.current.draw_limit": "Limite estrazione",
    "cli.current.inclusive": "inclusivo",
    "cli.current.latest_draw": "Ultima estrazione",
    "cli.current.of": "del",
    "cli.current.markov_title": "===== MISURATORE MARKOV DELLA COPERTURA =====",
    "cli.current.markov_state": "Stato: cifre ancora mancanti nel ciclo naturale corrente.",
    "cli.current.markov_ranking": (
        "Classifica: attesa residua crescente; non rappresenta un vantaggio sul gioco."
    ),
    "cli.current.markov_top": (
        "Più presenti: cifre con il massimo numero di occorrenze nel ciclo corrente."
    ),
    "cli.current.pos": "Pos",
    "cli.current.wheel": "Ruota",
    "cli.current.last": "Ultimo",
    "cli.current.cycles": "Cicli",
    "cli.current.age": "Età",
    "cli.current.most_present": "Più presenti",
    "cli.current.missing": "Mancanti",
    "cli.current.within1": "Entro 1",
    "cli.current.within2": "Entro 2",
    "cli.current.within3": "Entro 3",
    "cli.current.within5": "Entro 5",
    "cli.current.expected": "Attesa",
    "cli.current.coverage_hits_title": "===== SEGNALE OPERATIVO COVERAGE-HITS =====",
    "cli.current.historical_source": "Fonte storica",
    "cli.current.coverage_hits_event": (
        "Evento: almeno max(1, N-1) delle N cifre mancanti alla prossima estrazione."
    ),
    "cli.current.coverage_hits_estimate": (
        "Stima95-: probabilità corrente corretta con il limite inferiore Wilson "
        "dello scarto storico."
    ),
    "cli.current.coverage_hits_age_note": "Età è descrittiva e non incrementa la probabilità.",
    "cli.current.coverage_hits_empty": "Nessuna classe corrente presente nel riepilogo storico.",
    "cli.current.class": "Classe",
    "cli.current.cases": "Casi",
    "cli.current.historical": "Storico",
    "cli.current.event_probability": "P evento",
    "cli.current.estimate95": "Stima95-",
    "cli.current.first_signal": "Primo segnale",
    "cli.current.at_least": "almeno",
    "cli.current.among": "tra",
    "cli.current.coverage_hits_note": (
        "Nota: un lift negativo non indica un vantaggio storico; la classifica "
        "descrive il segnale operativo più robusto disponibile."
    ),
    "cli.current.next_draw_title": "===== ESTRAZIONE SUCCESSIVA NEL DATABASE =====",
    "cli.current.next_draw_note": "Non utilizzata nei calcoli del quadro storico.",
    "cli.current.draw": "Estrazione",
    "cli.current.digit_legend": "Legenda cifre",
    "cli.current.top": "TOP",
    "cli.current.numbers": "Numeri",
    "cli.current.anomaly_history_title": "===== ANOMALIE A1-A4 NEL DATABASE =====",
    "cli.current.valid_transitions": "Transizioni valide",
    "cli.current.observed_events": "Eventi osservati",
    "cli.current.categories": "Categorie",
    "cli.current.no_historical_anomalies": "Nessuna anomalia storica rilevata.",
    "cli.current.date": "Data",
    "cli.current.event_probability_header": "P(evento)",
    "cli.current.level": "Livello",
    "cli.current.signature": "Firma",
    "cli.current.active_anomalies_title": "===== ANOMALIE ATTIVE ALLA {draw} ({date}) =====",
    "cli.current.no_active_anomalies": "Nessuna anomalia A1-A4 attiva.",
    "cli.current.active_since": "Attiva/osservata da",
    "cli.consensus.title": "===== CONSENSUS TRASVERSALE DELLE CIFRE =====",
    "cli.consensus.description": (
        "Descrittivo: per ogni cifra conta in quante ruote con ciclo attivo è ancora assente "
        "e in quante è tra le più presenti nel ciclo corrente."
    ),
    "cli.consensus.warning": "Non combina cifre in numeri e non rappresenta un vantaggio sul gioco.",
    "cli.consensus.digit": "Cifra",
    "cli.consensus.missing_wheels": "Ruote in deficit",
    "cli.consensus.top_wheels": "Ruote in predominanza",
    "cli.consensus.where_missing": "Dove in deficit",
    "cli.consensus.where_top": "Dove predominante",
    "cli.consensus.empty": "Nessuna ruota con ciclo attivo.",
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
