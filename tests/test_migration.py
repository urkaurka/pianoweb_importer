from types import SimpleNamespace
from datetime import datetime

from ut_ensure_sqlserver import _parse_connection_string, _valid_sa_password
from ut_restore_backup import _consume_all_result_sets
from ut_reset_postgres import _quote_identifier, _quote_literal
from pianoweb_migration.migration import (
    AUDIT_METADATA_FIELDS,
    ColumnDefinition,
    TableDefinition,
    _date_value,
    _destination_columns,
    _parameter_rows,
    _truncate_tables,
    load_table_definitions,
)


class FakeResult:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def fetchall(self) -> list[object]:
        return self.rows


class FakeCursor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _query: str) -> FakeResult:
        self.calls += 1
        return FakeResult(
            [
                SimpleNamespace(
                    TABLE_SCHEMA="dbo",
                    TABLE_NAME="Users",
                    COLUMN_NAME="Id",
                    DATA_TYPE="int",
                    CHARACTER_MAXIMUM_LENGTH=None,
                    NUMERIC_PRECISION=None,
                    NUMERIC_SCALE=None,
                    IS_NULLABLE="NO",
                )]
            if self.calls == 1
            else [SimpleNamespace(TABLE_SCHEMA="dbo", TABLE_NAME="Users", COLUMN_NAME="Id")]
        )


def test_load_table_definitions_maps_columns_and_primary_key() -> None:
    tables = load_table_definitions(FakeCursor())

    assert tables[0].schema == "dbo"
    assert tables[0].columns[0].postgres_type == "integer"
    assert tables[0].columns[0].nullable is False
    assert tables[0].primary_key == ("Id",)


class FakeComposable:
    def __init__(self, value: str) -> None:
        self.value = value

    def format(self, *values: "FakeComposable") -> "FakeComposable":
        value = self.value
        for item in values:
            value = value.replace("{}", item.value, 1)
        return FakeComposable(value)

    def join(self, values: object) -> "FakeComposable":
        return FakeComposable(self.value.join(item.value for item in values))


class FakeSql:
    @staticmethod
    def SQL(value: str) -> FakeComposable:
        return FakeComposable(value)

    @staticmethod
    def Identifier(value: str) -> FakeComposable:
        return FakeComposable(f'"{value}"')


class RecordingCursor:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement: FakeComposable) -> None:
        self.statements.append(statement.value)


def test_truncate_tables_builds_statement_for_source_tables() -> None:
    cursor = RecordingCursor()
    table = TableDefinition("dbo", "Users", (ColumnDefinition("Id", "integer", False),))

    _truncate_tables(cursor, FakeSql, (table,))

    assert cursor.statements == ['TRUNCATE TABLE "dbo"."Users" RESTART IDENTITY']


def test_source_rows_are_converted_to_tuples() -> None:
    source_rows = [["value", 42], ("other", 7)]

    assert _parameter_rows(source_rows) == (("value", 42), ("other", 7))


def test_destination_columns_remove_only_legacy_audit_metadata() -> None:
    table = TableDefinition(
        "dbo",
        "Users",
        tuple(ColumnDefinition(name, "text", True) for name in (
            "Id",
            "InserimentoData",
            "InserimentoUtente",
            "ModificaData",
            "ModificaUtente",
            "CancellaData",
            "CancellaUtente",
            "Name",
        )),
    )

    assert [column.name for column in _destination_columns(table)] == [
        "Id",
        "CancellaData",
        "Name",
    ]
    assert "CancellaData" not in AUDIT_METADATA_FIELDS


def test_missing_audit_date_uses_import_fallback() -> None:
    fallback = _date_value(None, datetime(2010, 1, 1))

    assert fallback == datetime(2010, 1, 1)


def test_audit_record_ids_support_textual_primary_keys() -> None:
    from pianoweb_migration.migration import _audit_row

    row = _audit_row(
        TableDefinition("dbo", "Config", ()),
        "GSTPERM.Config.ImportaUtentiNtAllAvvio",
        "INSERT",
        datetime(2010, 1, 1),
        None,
        {},
    )

    assert row[1] == "GSTPERM.Config.ImportaUtentiNtAllAvvio"


def test_parse_connection_string_reads_credentials() -> None:
    settings = _parse_connection_string(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;"
        "DATABASE=pianoweb_source;UID=sa;PWD=secret"
    )

    assert settings["UID"] == "sa"
    assert settings["PWD"] == "secret"


def test_sql_server_sa_password_requires_length_and_complexity() -> None:
    assert _valid_sa_password("PianoWeb2026!") is True
    assert _valid_sa_password("short") is False
    assert _valid_sa_password("onlylowercase") is False


def test_consume_all_result_sets_reads_each_select_result() -> None:
    class FakeCursor:
        description: tuple[str] | None = None

        def __init__(self) -> None:
            self.remaining = [(True, ("column",)), (True, None), (False, None)]
            self.fetches = 0

        def nextset(self) -> bool:
            has_next, self.description = self.remaining.pop(0)
            return has_next

        def fetchall(self) -> list[object]:
            self.fetches += 1
            return []

    cursor = FakeCursor()

    _consume_all_result_sets(cursor)

    assert cursor.fetches == 1


def test_postgres_sql_quoting_escapes_identifiers_and_literals() -> None:
    assert _quote_identifier('project"db') == '"project""db"'
    assert _quote_literal("project's db") == "'project''s db'"
