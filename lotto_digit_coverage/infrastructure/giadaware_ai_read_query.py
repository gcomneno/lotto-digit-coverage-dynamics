"""GiadaWare AI semantic read-query adapter for Cifrolotto."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Protocol

from giadaware_ai import (
    ReadQueryInterpretation,
    SemanticQueryContext,
    SemanticReadQueryInterpreter,
    SemanticReadQueryRequest,
    semantic_query_context_from_mapping,
)


DEFAULT_CONTEXT_PATH = Path(
    "config/giadaware-ai/lotto-read-query-context.json"
)


class JsonBackend(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]: ...


def load_lotto_read_query_context(
    path: Path = DEFAULT_CONTEXT_PATH,
    *,
    current_date: date | None = None,
) -> SemanticQueryContext:
    """Load the versioned context and optionally add runtime civil-date evidence."""

    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream)

    context = semantic_query_context_from_mapping(raw)

    if current_date is None:
        return context

    iso_date = current_date.isoformat()
    previous_iso_date = (
        current_date - timedelta(days=1)
    ).isoformat()

    current_date_rule = (
        "The current civil date supplied by Cifrolotto is "
        f"{iso_date}."
    )
    previous_date_rule = (
        "The previous civil date supplied by Cifrolotto is "
        f"{previous_iso_date}."
    )

    return replace(
        context,
        revision=f"{context.revision}+date-{iso_date}",
        semantic_rules=(
            *context.semantic_rules,
            current_date_rule,
            previous_date_rule,
        ),
    )


class LottoSemanticReadQueryCapability:
    """Interpret Lotto requests through the generic GiadaWare AI capability."""

    def __init__(
        self,
        backend: JsonBackend,
        *,
        context_path: Path = DEFAULT_CONTEXT_PATH,
        current_date: date | None = None,
    ) -> None:
        self._context = load_lotto_read_query_context(
            context_path,
            current_date=current_date,
        )
        self._interpreter = SemanticReadQueryInterpreter(
            backend=backend,
            context=self._context,
        )

    @property
    def context(self) -> SemanticQueryContext:
        return self._context

    def execute(
        self,
        request: str,
        *,
        language: str,
    ) -> ReadQueryInterpretation:
        return self._interpreter.execute(
            SemanticReadQueryRequest(
                text=request,
                language=language,
            )
        )


def build_default_giadaware_backend() -> JsonBackend:
    """Build the local provider adapter without leaking it into core semantics."""

    try:
        from giadaware_ai.backends import OllamaBackend
    except ImportError as error:
        raise RuntimeError(
            "GiadaWare AI non è disponibile. "
            "Installa requirements-ai.txt nell'ambiente Python "
            "usato da lotto.py."
        ) from error

    return OllamaBackend(
        model=os.environ.get(
            "GIADAWARE_AI_MODEL",
            "qwen2.5:1.5b-instruct",
        ),
        base_url=os.environ.get(
            "GIADAWARE_AI_BASE_URL",
            "http://localhost:11434",
        ),
    )
