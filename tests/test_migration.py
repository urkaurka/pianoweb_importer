from types import SimpleNamespace

from pianoweb_migration.migration import (
    ColumnDefinition,
    TableDefinition,
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
