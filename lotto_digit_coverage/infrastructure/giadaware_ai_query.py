"""GiadaWare AI adapter that translates natural language into Lotto intents."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Protocol

from lotto_digit_coverage.application.natural_query import DrawHistoryIntent


class JsonBackend(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]: ...


INTENT_SCHEMA: Mapping[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "operation",
        "wheel",
        "numbers",
        "digits",
        "order",
        "highlight",
        "limit",
        "from_draw",
        "to_draw",
    ],
    "properties": {
        "operation": {"type": "string", "enum": ["draw_history"]},
        "wheel": {
            "type": "string",
            "enum": [
                "Bari",
                "Cagliari",
                "Firenze",
                "Genova",
                "Milano",
                "Napoli",
                "Palermo",
                "Roma",
                "Torino",
                "Venezia",
                "Nazionale",
            ],
        },
        "numbers": {
            "type": "array",
            "items": {"type": "integer", "minimum": 1, "maximum": 90},
            "uniqueItems": True,
        },
        "digits": {
            "type": "array",
            "items": {"type": "integer", "minimum": 0, "maximum": 9},
            "uniqueItems": True,
        },
        "order": {"type": "string", "enum": ["ascending", "descending"]},
        "highlight": {"type": "boolean"},
        "limit": {"type": ["integer", "null"], "minimum": 1},
        "from_draw": {"type": ["integer", "null"], "minimum": 1},
        "to_draw": {"type": ["integer", "null"], "minimum": 1},
    },
}

_SYSTEM_PROMPT = """You are a narrow intent translator for an Italian Lotto archive.
Return only a JSON object matching the supplied schema.
Supported operation: draw_history only.
Never return SQL, code, prose, predictions, betting advice, or additional fields.
Interpret 'ultima/più recente verso il passato' as order='descending'.
Interpret 'accendi/evidenzia' as highlight=true.
If no limit or draw range is requested, use null.
If no digits are requested, use an empty digits array.
Use canonical Italian wheel names exactly as allowed by the schema.
"""


class LottoNaturalQueryCapability:
    """Consumer-owned semantic capability over a GiadaWare AI JSON backend."""

    def __init__(self, backend: JsonBackend) -> None:
        self._backend = backend

    def execute(self, request: str) -> DrawHistoryIntent:
        if not request.strip():
            raise ValueError("la richiesta naturale non può essere vuota.")
        raw = self._backend.generate_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=request,
            response_schema=INTENT_SCHEMA,
        )
        return DrawHistoryIntent.from_mapping(raw)


def build_default_giadaware_backend() -> JsonBackend:
    """Build the local reference backend without making it a core dependency."""

    try:
        from giadaware_ai.backends import OllamaBackend
    except ImportError as error:
        raise RuntimeError(
            "GiadaWare AI non è disponibile. Installa il package giadaware_ai "
            "nell'ambiente Python usato da lotto.py."
        ) from error

    return OllamaBackend(
        model=os.environ.get("GIADAWARE_AI_MODEL", "qwen2.5:1.5b-instruct"),
        base_url=os.environ.get("GIADAWARE_AI_BASE_URL", "http://localhost:11434"),
    )
