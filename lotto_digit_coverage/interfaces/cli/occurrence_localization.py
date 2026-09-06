"""Deterministic localization catalog for occurrence-group CLI presentation."""

from __future__ import annotations

from lotto_digit_coverage.interfaces.localization import PresentationCatalog


OCCURRENCE_PRESENTATION_CATALOG = PresentationCatalog(
    canonical={
        "database_label": "Database",
        "draws_label": "Draws",
        "range_label": "Range",
        "reference_label": "Reference",
        "groups_label": "Groups",
        "limit_label": "Limit",
        "draw": "draw",
        "of": "of",
        "groups_description": (
            "{group_size} analyzed draws per group; each group also has its own "
            "reference draw, excluded from counts."
        ),
        "global_limit": "{limit} global draws; ",
        "no_global_limit": "no global limit; ",
        "examined_draws": "{count} draws examined.",
        "usage_header": "Use",
        "draw_header": "Draw",
        "date_header": "Date",
        "group_summary": (
            "Group: reference {reference_draw} of {reference_date}; analysis "
            "{newest}–{oldest} ({size} counted draws)"
        ),
        "reference_usage": "Ref.",
        "count_usage": "Count",
        "total_usage": "Tot",
        "grand_total": "Grand total occurrences",
        "help_title": "Occurrence groups extension:",
        "help_occurrence_limit": (
            "  --occurrence-limit N  Limit the global range to N consecutive draws, "
            "including reference rows."
        ),
        "occurrence_limit_missing": "--occurrence-limit requires a draw count.",
        "occurrence_limit_duplicate": "--occurrence-limit may be specified only once.",
        "occurrence_limit_requires_groups": "--occurrence-limit requires --occurrence-groups.",
        "database_missing": "database not found",
    },
    derived={
        "it": {
            "database_label": "Database",
            "draws_label": "Estrazioni",
            "range_label": "Intervallo",
            "reference_label": "Riferimento",
            "groups_label": "Gruppi",
            "limit_label": "Limite",
            "draw": "estrazione",
            "of": "del",
            "groups_description": (
                "{group_size} estrazioni analizzate per gruppo; ogni gruppo ha inoltre "
                "una propria estrazione di riferimento, esclusa dai conteggi."
            ),
            "global_limit": "{limit} concorsi globali; ",
            "no_global_limit": "nessun limite globale; ",
            "examined_draws": "{count} concorsi esaminati.",
            "usage_header": "Uso",
            "draw_header": "Estr",
            "date_header": "Data",
            "group_summary": (
                "Gruppo: riferimento {reference_draw} del {reference_date}; analisi "
                "{newest}–{oldest} ({size} estrazioni conteggiate)"
            ),
            "reference_usage": "Rif.",
            "count_usage": "Conta",
            "total_usage": "Tot",
            "grand_total": "Somma globale delle occorrenze",
            "help_title": "Estensione occurrence groups:",
            "help_occurrence_limit": (
                "  --occurrence-limit N  Limita il range globale a N concorsi consecutivi, "
                "incluse le righe di riferimento."
            ),
            "occurrence_limit_missing": "--occurrence-limit richiede un numero di estrazioni.",
            "occurrence_limit_duplicate": "--occurrence-limit può essere specificato una sola volta.",
            "occurrence_limit_requires_groups": "--occurrence-limit richiede --occurrence-groups.",
            "database_missing": "database assente",
        }
    },
)


def occurrence_text(key: str, locale: str) -> str:
    """Resolve one occurrence-group presentation key through the shared contract."""

    return OCCURRENCE_PRESENTATION_CATALOG.resolve(key, locale).text
