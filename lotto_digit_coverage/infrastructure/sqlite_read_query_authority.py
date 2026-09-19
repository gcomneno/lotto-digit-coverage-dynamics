"""Consumer-owned authority boundary for untrusted SQLite read queries."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType


ReadQueryScalar = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class SqliteReadQueryPolicy:
    """Declared execution surface for a read-query authority."""

    relations: Mapping[str, frozenset[str]]
    functions: frozenset[str]
    max_result_rows: int

    def __post_init__(self) -> None:
        if not self.relations:
            raise ValueError("relations must not be empty")
        if self.max_result_rows <= 0:
            raise ValueError("max_result_rows must be positive")


@dataclass(frozen=True, slots=True)
class AuthorizedReadQuery:
    """Query data that has crossed the consumer authority boundary."""

    sql: str
    parameters: Mapping[str, ReadQueryScalar]


class SqliteReadQueryAuthority:
    """Authorize untrusted candidate queries against a declared policy."""

    def __init__(self, policy: SqliteReadQueryPolicy) -> None:
        self._policy = policy

    @property
    def policy(self) -> SqliteReadQueryPolicy:
        return self._policy

    def authorize(
        self,
        sql: str,
        parameters: Mapping[str, ReadQueryScalar],
    ) -> AuthorizedReadQuery:
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("sql must be a non-empty string")

        normalized_parameters = dict(parameters)

        self._validate_structure(
            sql,
            normalized_parameters,
        )

        return AuthorizedReadQuery(
            sql=sql,
            parameters=MappingProxyType(normalized_parameters),
        )

    def _validate_structure(
        self,
        sql: str,
        parameters: Mapping[str, ReadQueryScalar],
    ) -> None:
        """Prepare the candidate with SQLite's parser against a shadow schema."""

        connection = sqlite3.connect(":memory:")

        try:
            self._create_shadow_schema(connection)

            declared_relation_reads: set[str] = set()

            connection.set_authorizer(
                _build_read_query_authorizer(
                    self._policy,
                    declared_relation_reads=declared_relation_reads,
                )
            )

            tracked_parameters = _TrackingParameters(parameters)

            connection.execute(
                "EXPLAIN QUERY PLAN " + sql,
                tracked_parameters,
            ).fetchall()

            if tracked_parameters.used_keys != set(tracked_parameters):
                raise ValueError(
                    "candidate parameters do not exactly match SQL placeholders"
                )

            if not declared_relation_reads:
                raise ValueError(
                    "candidate query must read at least one declared relation"
                )

        except sqlite3.Error as error:
            raise ValueError(
                f"candidate query is not structurally valid: {error}"
            ) from error
        finally:
            connection.close()

    def _create_shadow_schema(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        for relation, columns in self._policy.relations.items():
            quoted_relation = _quote_identifier(relation)
            ordered_columns = sorted(columns)

            column_sql = ", ".join(
                _quote_identifier(column)
                for column in ordered_columns
            )

            connection.execute(
                f"CREATE TABLE {quoted_relation} ({column_sql})"
            )

            probe_index = _quote_identifier(
                f"__authority_probe_{relation}"
            )
            probe_column = _quote_identifier(
                ordered_columns[0]
            )

            connection.execute(
                f"CREATE INDEX {probe_index} "
                f"ON {quoted_relation} ({probe_column})"
            )


class _TrackingParameters(dict[str, ReadQueryScalar]):
    """Record the named parameters SQLite actually binds."""

    def __init__(
        self,
        parameters: Mapping[str, ReadQueryScalar],
    ) -> None:
        super().__init__(parameters)
        self.used_keys: set[str] = set()

    def __getitem__(self, key: str) -> ReadQueryScalar:
        self.used_keys.add(key)
        return super().__getitem__(key)


def _build_read_query_authorizer(
    policy: SqliteReadQueryPolicy,
    *,
    allow_view_expansion: bool = False,
    declared_relation_reads: set[str] | None = None,
) -> Callable[
    [int, str | None, str | None, str | None, str | None],
    int,
]:
    """Build a structural SQLite authorizer from the consumer policy."""

    denied_actions = {
        sqlite3.SQLITE_ALTER_TABLE,
        sqlite3.SQLITE_ANALYZE,
        sqlite3.SQLITE_ATTACH,
        sqlite3.SQLITE_CREATE_INDEX,
        sqlite3.SQLITE_CREATE_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_INDEX,
        sqlite3.SQLITE_CREATE_TEMP_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
        sqlite3.SQLITE_CREATE_TEMP_VIEW,
        sqlite3.SQLITE_CREATE_TRIGGER,
        sqlite3.SQLITE_CREATE_VIEW,
        sqlite3.SQLITE_CREATE_VTABLE,
        sqlite3.SQLITE_DELETE,
        sqlite3.SQLITE_DETACH,
        sqlite3.SQLITE_DROP_INDEX,
        sqlite3.SQLITE_DROP_TABLE,
        sqlite3.SQLITE_DROP_TEMP_INDEX,
        sqlite3.SQLITE_DROP_TEMP_TABLE,
        sqlite3.SQLITE_DROP_TEMP_TRIGGER,
        sqlite3.SQLITE_DROP_TEMP_VIEW,
        sqlite3.SQLITE_DROP_TRIGGER,
        sqlite3.SQLITE_DROP_VIEW,
        sqlite3.SQLITE_DROP_VTABLE,
        sqlite3.SQLITE_INSERT,
        sqlite3.SQLITE_PRAGMA,
        sqlite3.SQLITE_REINDEX,
        sqlite3.SQLITE_SAVEPOINT,
        sqlite3.SQLITE_TRANSACTION,
        sqlite3.SQLITE_UPDATE,
    }

    allowed_relations = {
        relation.casefold(): frozenset(
            column.casefold()
            for column in columns
        )
        for relation, columns in policy.relations.items()
    }

    allowed_functions = {
        function.casefold()
        for function in policy.functions
    }

    def is_trusted_view_expansion(
        source_name: str | None,
    ) -> bool:
        return (
            allow_view_expansion
            and source_name is not None
            and source_name.casefold() in allowed_relations
        )

    def authorize(
        action: int,
        arg1: str | None,
        arg2: str | None,
        database_name: str | None,
        trigger_name: str | None,
    ) -> int:
        del database_name

        trusted_view_expansion = is_trusted_view_expansion(
            trigger_name
        )

        if action in denied_actions:
            return sqlite3.SQLITE_DENY

        if action == sqlite3.SQLITE_READ:
            relation_name = (
                arg1.casefold()
                if arg1 is not None
                else None
            )

            if relation_name in allowed_relations:
                if declared_relation_reads is not None:
                    declared_relation_reads.add(relation_name)

                allowed_columns = allowed_relations[relation_name]

                if (
                    arg2
                    and arg2.casefold() not in allowed_columns
                ):
                    return sqlite3.SQLITE_DENY
            elif not trusted_view_expansion:
                return sqlite3.SQLITE_DENY

        if action == sqlite3.SQLITE_FUNCTION:
            if (
                arg2 is None
                or (
                    arg2.casefold() not in allowed_functions
                    and not trusted_view_expansion
                )
            ):
                return sqlite3.SQLITE_DENY

        return sqlite3.SQLITE_OK

    return authorize


def _quote_identifier(identifier: str) -> str:
    """Quote a trusted policy identifier for the SQLite shadow schema."""

    return '"' + identifier.replace('"', '""') + '"'
