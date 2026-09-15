"""Migrate SQL Server tables to PostgreSQL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .types import postgres_type


class SourceCursor(Protocol):
    """Subset of a DB-API cursor used by the migration code."""

    description: Any

    def execute(self, operation: str, *parameters: Any) -> Any: ...

    def fetchall(self) -> list[Any]: ...

    def fetchmany(self, size: int) -> list[Any]: ...


@dataclass(frozen=True, slots=True)
class ColumnDefinition:
    """A source column and its PostgreSQL representation."""

    name: str
    postgres_type: str
    nullable: bool


@dataclass(frozen=True, slots=True)
class TableDefinition:
    """A SQL Server table definition."""

    schema: str
    name: str
    columns: tuple[ColumnDefinition, ...]
    primary_key: tuple[str, ...] = ()


def _value(row: Any, name: str, index: int) -> Any:
    """Read a DB-API row by attribute, mapping key, or position."""
    try:
        return getattr(row, name)
    except AttributeError:
        try:
            return row[name]
        except (IndexError, KeyError, TypeError):
            return row[index]


def load_table_definitions(cursor: SourceCursor) -> tuple[TableDefinition, ...]:
    """Read SQL Server table and column metadata, including primary keys."""
    column_rows = cursor.execute(
        """
        SELECT c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE,
               c.CHARACTER_MAXIMUM_LENGTH, c.NUMERIC_PRECISION, c.NUMERIC_SCALE,
               c.IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS AS c
        JOIN INFORMATION_SCHEMA.TABLES AS t
          ON t.TABLE_SCHEMA = c.TABLE_SCHEMA
         AND t.TABLE_NAME = c.TABLE_NAME
         AND t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION
        """
    ).fetchall()
    primary_key_rows = cursor.execute(
        """
        SELECT kcu.TABLE_SCHEMA, kcu.TABLE_NAME, kcu.COLUMN_NAME,
               kcu.ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu
          ON tc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
         AND tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
         AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
         AND tc.TABLE_NAME = kcu.TABLE_NAME
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ORDER BY kcu.TABLE_SCHEMA, kcu.TABLE_NAME, kcu.ORDINAL_POSITION
        """
    ).fetchall()

    definitions: dict[tuple[str, str], list[ColumnDefinition]] = {}
    for row in column_rows:
        schema = _value(row, "TABLE_SCHEMA", 0)
        table = _value(row, "TABLE_NAME", 1)
        data_type = _value(row, "DATA_TYPE", 3)
        definitions.setdefault((schema, table), []).append(
            ColumnDefinition(
                name=_value(row, "COLUMN_NAME", 2),
                postgres_type=postgres_type(
                    data_type,
                    _value(row, "CHARACTER_MAXIMUM_LENGTH", 4),
                    _value(row, "NUMERIC_PRECISION", 5),
                    _value(row, "NUMERIC_SCALE", 6),
                ),
                nullable=_value(row, "IS_NULLABLE", 7) == "YES",
            )
        )

    primary_keys: dict[tuple[str, str], list[str]] = {}
    for row in primary_key_rows:
        key = (_value(row, "TABLE_SCHEMA", 0), _value(row, "TABLE_NAME", 1))
        primary_keys.setdefault(key, []).append(_value(row, "COLUMN_NAME", 2))

    return tuple(
        TableDefinition(schema, table, tuple(columns), tuple(primary_keys.get((schema, table), ())))
        for (schema, table), columns in definitions.items()
    )


def migrate_tables(
    source_connection: Any,
    destination_connection: Any,
    *,
    batch_size: int = 1000,
    apply: bool = True,
) -> tuple[TableDefinition, ...]:
    """Create destination tables and copy source rows in batches."""
    if batch_size < 1:
        raise ValueError("batch_size must be greater than zero")

    from psycopg import sql

    source_cursor = source_connection.cursor()
    definitions = load_table_definitions(source_cursor)
    destination_cursor = destination_connection.cursor()
    try:
        for table in definitions:
            create_table = _create_table_sql(sql, table)
            if not apply:
                print(create_table.as_string(destination_connection))
                continue

            destination_cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}\n").format(sql.Identifier(table.schema))
            )
            destination_cursor.execute(create_table)

        if apply:
            _truncate_tables(destination_cursor, sql, definitions)

        for table in definitions:
            if not apply:
                continue
            source_columns = ", ".join(
                _quote_sql_server_identifier(column.name) for column in table.columns
            )
            source_cursor.execute(
                f"SELECT {source_columns} FROM "
                f"{_quote_sql_server_identifier(table.schema)}."
                f"{_quote_sql_server_identifier(table.name)}"
            )
            insert_sql = _insert_table_sql(sql, table)
            while rows := source_cursor.fetchmany(batch_size):
                destination_cursor.executemany(insert_sql, _parameter_rows(rows))
        if apply:
            destination_connection.commit()
    except Exception:
        if apply:
            destination_connection.rollback()
        raise
    finally:
        destination_cursor.close()
        source_cursor.close()
    return definitions


def _truncate_tables(cursor: Any, sql: Any, tables: tuple[TableDefinition, ...]) -> None:
    """Remove existing rows from all destination tables before importing."""
    if not tables:
        return
    cursor.execute(
        sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY").format(
            sql.SQL(", ").join(
                sql.SQL("{}.{}").format(sql.Identifier(table.schema), sql.Identifier(table.name))
                for table in tables
            )
        )
    )


def _parameter_rows(rows: list[Any]) -> tuple[tuple[Any, ...], ...]:
    """Convert pyodbc Row objects to psycopg-compatible parameter tuples."""
    return tuple(tuple(row) for row in rows)


def _create_table_sql(sql: Any, table: TableDefinition) -> Any:
    """Build a quoted CREATE TABLE statement."""
    definitions = [
        sql.SQL("{} {}{}").format(
            sql.Identifier(column.name),
            sql.SQL(column.postgres_type),
            sql.SQL("") if column.nullable else sql.SQL(" NOT NULL"),
        )
        for column in table.columns
    ]
    if table.primary_key:
        definitions.append(
            sql.SQL("PRIMARY KEY ({})").format(
                sql.SQL(", ").join(sql.Identifier(name) for name in table.primary_key)
            )
        )
    return sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({})").format(
        sql.Identifier(table.schema),
        sql.Identifier(table.name),
        sql.SQL(", ").join(definitions),
    )


def _insert_table_sql(sql: Any, table: TableDefinition) -> Any:
    """Build a parameterized INSERT statement."""
    columns = sql.SQL(", ").join(sql.Identifier(column.name) for column in table.columns)
    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in table.columns)
    return sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(table.schema), sql.Identifier(table.name), columns, placeholders
    )


def _quote_sql_server_identifier(identifier: str) -> str:
    """Quote a SQL Server identifier, including closing brackets safely."""
    return f"[{identifier.replace(']', ']]')}]"
