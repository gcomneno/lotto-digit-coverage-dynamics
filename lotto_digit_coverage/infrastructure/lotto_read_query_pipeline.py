"""Consumer-owned semantic read-query pipeline for Cifrolotto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from giadaware_ai import ReadQueryStatus

from lotto_digit_coverage.infrastructure.giadaware_ai_read_query import (
    DEFAULT_CONTEXT_PATH,
    JsonBackend,
    LottoSemanticReadQueryCapability,
)
from lotto_digit_coverage.infrastructure.sqlite_read_query_authority import (
    SqliteReadQueryAuthority,
    SqliteReadQueryPolicy,
)
from lotto_digit_coverage.infrastructure.sqlite_read_query_executor import (
    SqliteReadQueryExecutor,
    SqliteReadQueryResult,
)


AUTHORIZED_SQL_FUNCTIONS = frozenset(
    {
        "count",
        "min",
        "max",
        "strftime",
    }
)


@dataclass(frozen=True, slots=True)
class LottoReadQueryOutcome:
    """Result of semantic interpretation plus consumer authorization/execution."""

    status: str
    normalized_interpretation: str
    validated_query: str | None
    reason: str | None
    result: SqliteReadQueryResult | None
    context_id: str
    context_revision: str
    language: str

    @property
    def accepted(self) -> bool:
        return self.status == ReadQueryStatus.ACCEPTED.value


def policy_from_context(context) -> SqliteReadQueryPolicy:
    """Derive the SQL authority surface from the validated semantic context."""

    return SqliteReadQueryPolicy(
        relations={
            relation.name: frozenset(
                column.name
                for column in relation.columns
            )
            for relation in context.relations
        },
        functions=AUTHORIZED_SQL_FUNCTIONS,
        max_result_rows=context.limits.max_result_rows,
    )


class LottoReadQueryPipeline:
    """Run semantic, authority and execution gates in strict sequence."""

    def __init__(
        self,
        backend: JsonBackend,
        *,
        database: Path,
        context_path: Path = DEFAULT_CONTEXT_PATH,
        current_date: date | None = None,
    ) -> None:
        self._semantic = LottoSemanticReadQueryCapability(
            backend,
            context_path=context_path,
            current_date=current_date,
        )

        self._policy = policy_from_context(
            self._semantic.context
        )
        self._authority = SqliteReadQueryAuthority(
            self._policy
        )
        self._executor = SqliteReadQueryExecutor(
            database=database,
            policy=self._policy,
        )

    @property
    def context(self):
        return self._semantic.context

    def execute(
        self,
        request: str,
        *,
        language: str,
    ) -> LottoReadQueryOutcome:
        interpretation = self._semantic.execute(
            request,
            language=language,
        )

        if interpretation.status is not ReadQueryStatus.ACCEPTED:
            return LottoReadQueryOutcome(
                status=interpretation.status.value,
                normalized_interpretation="",
                validated_query=None,
                reason=interpretation.reason,
                result=None,
                context_id=interpretation.context_id,
                context_revision=interpretation.context_revision,
                language=interpretation.language,
            )

        if interpretation.candidate_query is None:
            raise ValueError(
                "accepted interpretation has no candidate query"
            )

        parameters = {
            parameter.name: parameter.value
            for parameter in interpretation.parameters
        }

        authorized = self._authority.authorize(
            interpretation.candidate_query,
            parameters,
        )

        result = self._executor.execute(authorized)

        return LottoReadQueryOutcome(
            status=interpretation.status.value,
            normalized_interpretation=(
                interpretation.normalized_interpretation
            ),
            validated_query=authorized.sql,
            reason=None,
            result=result,
            context_id=interpretation.context_id,
            context_revision=interpretation.context_revision,
            language=interpretation.language,
        )
