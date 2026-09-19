from __future__ import annotations

import unittest

from lotto_digit_coverage.infrastructure.sqlite_read_query_authority import (
    SqliteReadQueryAuthority,
    SqliteReadQueryPolicy,
)


class SqliteReadQueryAuthorityTests(unittest.TestCase):
    def test_authorizes_parameterized_select_on_declared_view(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        sql = (
            "SELECT draw_number, draw_date, wheel, value "
            "FROM v_draw_numbers "
            "WHERE wheel = :wheel "
            "ORDER BY draw_date DESC, draw_number DESC, position ASC "
            "LIMIT 10"
        )
        parameters = {"wheel": "Napoli"}

        authorized = authority.authorize(
            sql,
            parameters,
        )

        self.assertEqual(authorized.sql, sql)
        self.assertEqual(
            dict(authorized.parameters),
            parameters,
        )

    def test_rejects_queries_without_declared_relation(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        candidates = (
            "SELECT 1",
            "VALUES (1)",
            (
                "WITH constants AS (SELECT 1 AS value) "
                "SELECT value FROM constants"
            ),
        )

        for sql in candidates:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    authority.authorize(sql, {})

    def test_declared_identifiers_follow_sqlite_case_insensitivity(
        self,
    ) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        sql = (
            "SELECT DRAW_NUMBER, WHEEL, VALUE "
            "FROM V_DRAW_NUMBERS "
            "WHERE WHEEL = :wheel "
            "LIMIT 10"
        )

        authorized = authority.authorize(
            sql,
            {"wheel": "Napoli"},
        )

        self.assertEqual(authorized.sql, sql)

    def test_initial_functional_envelope_query_shapes_are_authorized(
        self,
    ) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(
                {
                    "count",
                    "min",
                    "max",
                    "strftime",
                }
            ),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        candidates = (
            (
                "latest",
                (
                    "SELECT draw_number, draw_date, wheel, position, value "
                    "FROM v_draw_numbers "
                    "ORDER BY draw_date DESC, draw_number DESC "
                    "LIMIT 5"
                ),
                {},
            ),
            (
                "current-date",
                (
                    "SELECT draw_number, draw_date, wheel, position, value "
                    "FROM v_draw_numbers "
                    "WHERE draw_date = :draw_date "
                    "ORDER BY wheel_order, position "
                    "LIMIT 500"
                ),
                {"draw_date": "2026-09-19"},
            ),
            (
                "yesterday",
                (
                    "SELECT draw_number, draw_date, wheel, position, value "
                    "FROM v_draw_numbers "
                    "WHERE draw_date = :draw_date "
                    "ORDER BY wheel_order, position "
                    "LIMIT 500"
                ),
                {"draw_date": "2026-09-18"},
            ),
            (
                "date-range",
                (
                    "SELECT draw_number, draw_date, wheel, position, value "
                    "FROM v_draw_numbers "
                    "WHERE draw_date BETWEEN :start_date AND :end_date "
                    "ORDER BY draw_date, draw_number, wheel_order, position "
                    "LIMIT 500"
                ),
                {
                    "start_date": "2026-01-01",
                    "end_date": "2026-09-19",
                },
            ),
            (
                "all-numbers",
                (
                    "SELECT draw_number, draw_date, wheel "
                    "FROM v_draw_numbers "
                    "WHERE wheel = :wheel "
                    "GROUP BY draw_number, draw_date, wheel "
                    "HAVING count("
                    "DISTINCT CASE "
                    "WHEN value IN (:first_value, :second_value) "
                    "THEN value END"
                    ") = 2 "
                    "ORDER BY draw_date DESC "
                    "LIMIT 500"
                ),
                {
                    "wheel": "Roma",
                    "first_value": 18,
                    "second_value": 81,
                },
            ),
            (
                "any-number",
                (
                    "SELECT DISTINCT draw_number, draw_date, wheel "
                    "FROM v_draw_numbers "
                    "WHERE wheel = :wheel "
                    "AND value IN (:first_value, :second_value) "
                    "ORDER BY draw_date DESC "
                    "LIMIT 500"
                ),
                {
                    "wheel": "Roma",
                    "first_value": 18,
                    "second_value": 81,
                },
            ),
            (
                "include-and-exclude",
                (
                    "SELECT draw_number, draw_date, wheel "
                    "FROM v_draw_numbers "
                    "WHERE wheel = :wheel "
                    "GROUP BY draw_number, draw_date, wheel "
                    "HAVING count("
                    "CASE WHEN value = :required_value THEN 1 END"
                    ") > 0 "
                    "AND count("
                    "CASE WHEN value = :excluded_value THEN 1 END"
                    ") = 0 "
                    "ORDER BY draw_date DESC "
                    "LIMIT 500"
                ),
                {
                    "wheel": "Napoli",
                    "required_value": 18,
                    "excluded_value": 81,
                },
            ),
            (
                "group-by-year",
                (
                    "SELECT strftime('%Y', draw_date) AS draw_year, "
                    "count(*) AS occurrences "
                    "FROM v_draw_numbers "
                    "WHERE value = :value "
                    "GROUP BY strftime('%Y', draw_date) "
                    "ORDER BY draw_year "
                    "LIMIT 500"
                ),
                {"value": 18},
            ),
            (
                "wheel-comparison",
                (
                    "SELECT wheel, count(*) AS occurrences "
                    "FROM v_draw_numbers "
                    "WHERE wheel IN (:first_wheel, :second_wheel) "
                    "AND value = :value "
                    "GROUP BY wheel "
                    "ORDER BY wheel "
                    "LIMIT 500"
                ),
                {
                    "first_wheel": "Napoli",
                    "second_wheel": "Milano",
                    "value": 18,
                },
            ),
        )

        for name, sql, parameters in candidates:
            with self.subTest(name=name):
                authorized = authority.authorize(
                    sql,
                    parameters,
                )
                self.assertEqual(authorized.sql, sql)
                self.assertEqual(
                    dict(authorized.parameters),
                    parameters,
                )

    def test_rejects_multiple_statements(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        sql = (
            "SELECT draw_number "
            "FROM v_draw_numbers "
            "LIMIT 1; "
            "SELECT draw_number "
            "FROM v_draw_numbers "
            "LIMIT 1"
        )

        with self.assertRaises(ValueError):
            authority.authorize(sql, {})



    def test_rejects_delete_statement(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        sql = (
            "DELETE FROM v_draw_numbers "
            "WHERE wheel = :wheel"
        )

        with self.assertRaises(ValueError):
            authority.authorize(
                sql,
                {"wheel": "Napoli"},
            )

    def test_rejects_insert_and_update_statements(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        candidates = (
            (
                "INSERT INTO v_draw_numbers "
                "(draw_number, draw_date, wheel, wheel_order, position, value) "
                "VALUES (:draw_number, :draw_date, :wheel, :wheel_order, "
                ":position, :value)",
                {
                    "draw_number": 151,
                    "draw_date": "2026-09-19",
                    "wheel": "Napoli",
                    "wheel_order": 6,
                    "position": 1,
                    "value": 18,
                },
            ),
            (
                "UPDATE v_draw_numbers "
                "SET value = :value "
                "WHERE wheel = :wheel",
                {
                    "value": 18,
                    "wheel": "Napoli",
                },
            ),
        )

        for sql, parameters in candidates:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    authority.authorize(
                        sql,
                        parameters,
                    )

    def test_rejects_ddl_admin_and_transaction_statements(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        candidates = (
            "CREATE TABLE unauthorized_table (value INTEGER)",
            "DROP TABLE v_draw_numbers",
            "ALTER TABLE v_draw_numbers ADD COLUMN unauthorized INTEGER",
            "PRAGMA user_version",
            "ATTACH DATABASE ':memory:' AS unauthorized",
            "DETACH DATABASE unauthorized",
            "BEGIN",
            "COMMIT",
            "REINDEX",
            "ANALYZE",
        )

        for sql in candidates:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    authority.authorize(sql, {})

    def test_rejects_undeclared_relation(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        with self.assertRaises(ValueError):
            authority.authorize(
                "SELECT name FROM sqlite_schema LIMIT 1",
                {},
            )

    def test_rejects_undeclared_column(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        with self.assertRaises(ValueError):
            authority.authorize(
                "SELECT source_url "
                "FROM v_draw_numbers "
                "LIMIT 1",
                {},
            )

    def test_rejects_unallowed_function(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset({"count"}),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        with self.assertRaises(ValueError):
            authority.authorize(
                "SELECT abs(value) "
                "FROM v_draw_numbers "
                "LIMIT 1",
                {},
            )

    def test_authorizes_declared_function(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset({"count"}),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        sql = (
            "SELECT count(*) "
            "FROM v_draw_numbers "
            "LIMIT 1"
        )

        authorized = authority.authorize(sql, {})

        self.assertEqual(authorized.sql, sql)

    def test_rejects_extra_parameters(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        with self.assertRaises(ValueError):
            authority.authorize(
                "SELECT draw_number "
                "FROM v_draw_numbers "
                "WHERE wheel = :wheel "
                "LIMIT 1",
                {
                    "wheel": "Napoli",
                    "invented": 81,
                },
            )

    def test_rejects_missing_parameters(self) -> None:
        policy = SqliteReadQueryPolicy(
            relations={
                "v_draw_numbers": frozenset(
                    {
                        "draw_number",
                        "draw_date",
                        "wheel",
                        "wheel_order",
                        "position",
                        "value",
                    }
                )
            },
            functions=frozenset(),
            max_result_rows=500,
        )

        authority = SqliteReadQueryAuthority(policy)

        with self.assertRaises(ValueError):
            authority.authorize(
                "SELECT draw_number "
                "FROM v_draw_numbers "
                "WHERE wheel = :wheel "
                "LIMIT 1",
                {},
            )

if __name__ == "__main__":
    unittest.main()
