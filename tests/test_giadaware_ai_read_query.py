from __future__ import annotations

import unittest
from pathlib import Path

from giadaware_ai import ReadQueryStatus

from lotto_digit_coverage.infrastructure.giadaware_ai_read_query import (
    LottoSemanticReadQueryCapability,
    load_lotto_read_query_context,
)


CONTEXT = Path(
    "config/giadaware-ai/lotto-read-query-context.json"
)

WHEEL_MAPPING_RULE = (
    "English wheel names map to canonical database values as follows: "
    "Bari=Bari, Cagliari=Cagliari, Florence=Firenze, Genoa=Genova, "
    "Milan=Milano, Naples=Napoli, Palermo=Palermo, Rome=Roma, "
    "Turin=Torino, Venice=Venezia, National=Nazionale."
)


class ControlledBackend:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema=None,
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": response_schema,
            }
        )
        return self.response


def accepted_italian_response() -> dict[str, object]:
    return {
        "status": "accepted",
        "normalized_interpretation": (
            "Conta le occorrenze storiche del numero 18 "
            "sulla ruota di Napoli."
        ),
        "candidate_query": (
            "SELECT count(*) AS occurrence_count "
            "FROM v_draw_numbers "
            "WHERE wheel = :wheel AND value = :value "
            "LIMIT 500"
        ),
        "parameters": [
            {"name": "wheel", "value": "Napoli"},
            {"name": "value", "value": 18},
        ],
        "grounding": [
            {
                "query_fragment": "count(*)",
                "field": "aggregation",
                "source_kind": "request",
                "source_reference": "Quante volte",
            },
            {
                "query_fragment": "wheel = :wheel",
                "field": "wheel",
                "source_kind": "request",
                "source_reference": "Napoli",
            },
            {
                "query_fragment": "value = :value",
                "field": "value",
                "source_kind": "request",
                "source_reference": "18",
            },
        ],
        "reason": None,
    }


def accepted_english_response() -> dict[str, object]:
    return {
        "status": "accepted",
        "normalized_interpretation": (
            "Return Milan draws containing number 81."
        ),
        "candidate_query": (
            "SELECT DISTINCT draw_number, draw_date "
            "FROM v_draw_numbers "
            "WHERE wheel = :wheel AND value = :value "
            "LIMIT 500"
        ),
        "parameters": [
            {"name": "wheel", "value": "Milano"},
            {"name": "value", "value": 81},
        ],
        "grounding": [
            {
                "query_fragment": "wheel = :wheel",
                "field": "wheel",
                "source_kind": "context_rule",
                "source_reference": WHEEL_MAPPING_RULE,
            },
            {
                "query_fragment": "value = :value",
                "field": "value",
                "source_kind": "request",
                "source_reference": "81",
            },
        ],
        "reason": None,
    }


def rejected_response(
    status: str,
    reason: str,
) -> dict[str, object]:
    return {
        "status": status,
        "normalized_interpretation": "",
        "candidate_query": None,
        "parameters": [],
        "grounding": [],
        "reason": reason,
    }


class LottoSemanticReadQueryTests(unittest.TestCase):
    def test_loads_versioned_consumer_context(self) -> None:
        context = load_lotto_read_query_context(CONTEXT)

        self.assertEqual(
            context.context_id,
            "cifrolotto.lotto.read-query",
        )
        self.assertEqual(context.revision, "2026-09-19.1")
        self.assertEqual(context.languages, ("it", "en"))
        self.assertEqual(
            tuple(relation.name for relation in context.relations),
            ("v_draw_numbers",),
        )

    def test_accepts_controlled_italian_read_request(self) -> None:
        backend = ControlledBackend(
            accepted_italian_response()
        )
        capability = LottoSemanticReadQueryCapability(
            backend,
            context_path=CONTEXT,
        )

        result = capability.execute(
            "Quante volte è uscito il 18 a Napoli?",
            language="it",
        )

        self.assertIs(result.status, ReadQueryStatus.ACCEPTED)
        self.assertEqual(result.context_id, capability.context.context_id)
        self.assertEqual(
            result.context_revision,
            capability.context.revision,
        )
        self.assertEqual(result.language, "it")
        self.assertEqual(len(backend.calls), 1)

    def test_accepts_controlled_english_read_request(self) -> None:
        backend = ControlledBackend(
            accepted_english_response()
        )
        capability = LottoSemanticReadQueryCapability(
            backend,
            context_path=CONTEXT,
        )

        result = capability.execute(
            "Show Milan draws containing 81.",
            language="en",
        )

        self.assertIs(result.status, ReadQueryStatus.ACCEPTED)
        self.assertEqual(
            {parameter.name: parameter.value for parameter in result.parameters},
            {
                "wheel": "Milano",
                "value": 81,
            },
        )

    def test_preserves_unsupported_status(self) -> None:
        backend = ControlledBackend(
            rejected_response(
                "unsupported",
                "Predictive betting advice is outside the context.",
            )
        )
        capability = LottoSemanticReadQueryCapability(
            backend,
            context_path=CONTEXT,
        )

        result = capability.execute(
            "Quali numeri devo giocare domani?",
            language="it",
        )

        self.assertIs(result.status, ReadQueryStatus.UNSUPPORTED)
        self.assertIsNone(result.candidate_query)
        self.assertEqual(result.parameters, ())
        self.assertEqual(result.grounding, ())

    def test_preserves_ambiguous_status(self) -> None:
        backend = ControlledBackend(
            rejected_response(
                "ambiguous",
                "A material selector cannot be resolved.",
            )
        )
        capability = LottoSemanticReadQueryCapability(
            backend,
            context_path=CONTEXT,
        )

        result = capability.execute(
            "Fammi vedere quella estrazione.",
            language="it",
        )

        self.assertIs(result.status, ReadQueryStatus.AMBIGUOUS)
        self.assertIsNone(result.candidate_query)
        self.assertEqual(result.parameters, ())
        self.assertEqual(result.grounding, ())


if __name__ == "__main__":
    unittest.main()
