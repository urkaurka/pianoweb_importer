"""Migrate SQL Server tables to PostgreSQL."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from typing import Any, Protocol

from .types import postgres_type


TMP_SCHEMA = "tmp"
DESTINATION_SCHEMA = "dbo"
AUDIT_LOG_TABLE = "AUDIT_LOG"
AUDIT_METADATA_FIELDS = frozenset(
    {
        "InserimentoData",
        "InserimentoUtente",
        "ModificaData",
        "ModificaUtente",
        "CancellaUtente",
    }
)
AUDIT_DATE_FIELDS = frozenset({"InserimentoData", "ModificaData", "CancellaData"})


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
    keep_tmp: bool = False,
) -> tuple[TableDefinition, ...]:
    """Copy source tables through ``tmp`` into current-state tables in ``dbo``."""
    if batch_size < 1:
        raise ValueError("batch_size must be greater than zero")

    from psycopg import sql

    source_cursor = source_connection.cursor()
    definitions = load_table_definitions(source_cursor)
    fallback_date = _oldest_date_or_default(source_cursor, definitions)
    destination_cursor = destination_connection.cursor()
    try:
        if apply:
            destination_cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}\n").format(sql.Identifier(TMP_SCHEMA)))
            destination_cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}\n").format(sql.Identifier(DESTINATION_SCHEMA)))
            destination_cursor.execute(_create_audit_log_sql())
            for statement in _create_audit_log_indexes_sql():
                destination_cursor.execute(statement)

        for table in definitions:
            destination_columns = _destination_columns(table)
            create_tmp_table = _create_table_sql(sql, table, TMP_SCHEMA, table.columns)
            create_dbo_table = _create_table_sql(sql, table, DESTINATION_SCHEMA, destination_columns)
            if not apply:
                print(create_tmp_table.as_string(destination_connection))
                print(create_dbo_table.as_string(destination_connection))
                continue
            destination_cursor.execute(create_tmp_table)
            destination_cursor.execute(create_dbo_table)

        if apply:
            _truncate_tables(destination_cursor, sql, definitions, TMP_SCHEMA, DESTINATION_SCHEMA)

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
            insert_sql = _insert_table_sql(sql, table, TMP_SCHEMA, table.columns)
            while rows := source_cursor.fetchmany(batch_size):
                destination_cursor.executemany(insert_sql, _parameter_rows(rows))
            _copy_to_destination(destination_cursor, sql, table)
            _write_legacy_audit_events(destination_cursor, sql, table, fallback_date)
        if apply and not keep_tmp:
            destination_cursor.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(TMP_SCHEMA)))
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


def _truncate_tables(
    cursor: Any,
    sql: Any,
    tables: tuple[TableDefinition, ...],
    *schemas: str,
) -> None:
    """Remove existing rows from all temporary and destination tables."""
    if not tables:
        return
    if not schemas:
        schemas = tuple(dict.fromkeys(table.schema for table in tables))
    table_names = sql.SQL(", ").join(
        sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table.name))
        for schema in schemas
        for table in tables
    )
    cursor.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY").format(table_names))


def _parameter_rows(rows: list[Any]) -> tuple[tuple[Any, ...], ...]:
    """Convert pyodbc Row objects to psycopg-compatible parameter tuples."""
    return tuple(tuple(row) for row in rows)


def _create_table_sql(
    sql: Any,
    table: TableDefinition,
    schema: str,
    columns: tuple[ColumnDefinition, ...],
) -> Any:
    """Build a quoted CREATE TABLE statement for a destination schema."""
    definitions = [
        sql.SQL("{} {}{}").format(
            sql.Identifier(column.name),
            sql.SQL(column.postgres_type),
            sql.SQL("") if column.nullable else sql.SQL(" NOT NULL"),
        )
        for column in columns
    ]
    primary_key = tuple(
        name for name in table.primary_key if any(column.name == name for column in columns)
    )
    if primary_key:
        definitions.append(
            sql.SQL("PRIMARY KEY ({})").format(
                sql.SQL(", ").join(sql.Identifier(name) for name in primary_key)
            )
        )
    return sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table.name),
        sql.SQL(", ").join(definitions),
    )


def _insert_table_sql(
    sql: Any,
    table: TableDefinition,
    schema: str,
    columns: tuple[ColumnDefinition, ...],
) -> Any:
    """Build a parameterized INSERT statement."""
    column_sql = sql.SQL(", ").join(sql.Identifier(column.name) for column in columns)
    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in columns)
    return sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema), sql.Identifier(table.name), column_sql, placeholders
    )


def _destination_columns(table: TableDefinition) -> tuple[ColumnDefinition, ...]:
    """Return source columns retained in the current-state table."""
    excluded = {name.casefold() for name in AUDIT_METADATA_FIELDS}
    return tuple(column for column in table.columns if column.name.casefold() not in excluded)


def _copy_to_destination(cursor: Any, sql: Any, table: TableDefinition) -> None:
    """Copy a complete temporary table into its current-state counterpart."""
    columns = _destination_columns(table)
    if not columns:
        return
    column_sql = sql.SQL(", ").join(sql.Identifier(column.name) for column in columns)
    cursor.execute(
        sql.SQL("INSERT INTO {}.{} ({}) SELECT {} FROM {}.{}").format(
            sql.Identifier(DESTINATION_SCHEMA),
            sql.Identifier(table.name),
            column_sql,
            column_sql,
            sql.Identifier(TMP_SCHEMA),
            sql.Identifier(table.name),
        )
    )


def _create_audit_log_sql() -> str:
    """Build the audit table used by the current-state tables."""
    return f'''CREATE TABLE IF NOT EXISTS "{DESTINATION_SCHEMA}"."{AUDIT_LOG_TABLE}" (
        id BIGSERIAL PRIMARY KEY,
        table_name VARCHAR(255) NOT NULL,
        record_id VARCHAR(255) NOT NULL,
        operation VARCHAR(20) NOT NULL,
        occurred_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
        user_identifier VARCHAR(255),
        changed_fields JSONB NOT NULL DEFAULT '{{}}'::jsonb
    )'''


def _create_audit_log_indexes_sql() -> tuple[str, str]:
    """Build the indexes used to inspect audit history."""
    return (
        f'''CREATE INDEX IF NOT EXISTS "AUDIT_LOG_table_record_idx"
        ON "{DESTINATION_SCHEMA}"."{AUDIT_LOG_TABLE}" (table_name, record_id, id);
        ''',
        f'''CREATE INDEX IF NOT EXISTS "AUDIT_LOG_occurred_idx"
        ON "{DESTINATION_SCHEMA}"."{AUDIT_LOG_TABLE}" (occurred_at)''',
    )


def _oldest_date_or_default(cursor: SourceCursor, tables: tuple[TableDefinition, ...]) -> datetime:
    """Return January 1 of the oldest audit year, or January 1, 1900."""
    oldest: date | datetime | None = None
    audit_date_names = {name.casefold() for name in AUDIT_DATE_FIELDS}
    for table in tables:
        for column in table.columns:
            if column.name.casefold() not in audit_date_names:
                continue
            cursor.execute(
                f"SELECT MIN({_quote_sql_server_identifier(column.name)}) FROM "
                f"{_quote_sql_server_identifier(table.schema)}."
                f"{_quote_sql_server_identifier(table.name)}"
            )
            values = cursor.fetchall()
            value = values[0][0] if values and values[0] else None
            if value is not None and (oldest is None or value < oldest):
                oldest = value
    if oldest is None:
        return datetime(1900, 1, 1)
    return datetime(oldest.year, 1, 1)


def _write_legacy_audit_events(
    cursor: Any,
    sql: Any,
    table: TableDefinition,
    fallback_date: datetime,
) -> None:
    """Create best-effort audit events from legacy metadata columns."""
    metadata_columns = {column.name.casefold(): column.name for column in table.columns}
    if not table.primary_key or len(table.primary_key) != 1:
        return
    primary_key = table.primary_key[0]
    business_columns = _destination_columns(table)
    select_columns = [primary_key]
    for name in AUDIT_METADATA_FIELDS | AUDIT_DATE_FIELDS:
        actual_name = metadata_columns.get(name.casefold())
        if actual_name and actual_name not in select_columns:
            select_columns.append(actual_name)
    for column in business_columns:
        if column.name not in select_columns:
            select_columns.append(column.name)
    source_sql = sql.SQL(", ").join(sql.Identifier(name) for name in select_columns)
    cursor.execute(
        sql.SQL("SELECT {} FROM {}.{}").format(
            source_sql,
            sql.Identifier(TMP_SCHEMA),
            sql.Identifier(table.name),
        )
    )
    rows = cursor.fetchall()
    positions = {name.casefold(): index for index, name in enumerate(select_columns)}
    audit_rows = []
    for row in rows:
        record_id = row[positions[primary_key.casefold()]]
        modified_at = _row_value(row, positions, "ModificaData")
        audit_rows.append(
            _audit_row(
                table,
                record_id,
                "INSERT",
                _date_value(_row_value(row, positions, "InserimentoData"), fallback_date),
                _row_value(row, positions, "InserimentoUtente"),
                {
                    column.name: None if modified_at is not None else row[positions[column.name.casefold()]]
                    for column in business_columns
                },
            )
        )
        if modified_at is not None or _row_value(row, positions, "ModificaUtente") is not None:
            audit_rows.append(
                _audit_row(
                    table,
                    record_id,
                    "UPDATE",
                    _date_value(modified_at, fallback_date),
                    _row_value(row, positions, "ModificaUtente"),
                    {column.name: row[positions[column.name.casefold()]] for column in business_columns},
                )
            )
        deleted_at = _row_value(row, positions, "CancellaData")
        if deleted_at is not None:
            audit_rows.append(
                _audit_row(
                    table,
                    record_id,
                    "DELETE",
                    _date_value(deleted_at, fallback_date),
                    _row_value(row, positions, "CancellaUtente"),
                    {column.name: row[positions[column.name.casefold()]] for column in business_columns},
                )
            )
    if audit_rows:
        cursor.executemany(
            f'''INSERT INTO "{DESTINATION_SCHEMA}"."{AUDIT_LOG_TABLE}"
                (table_name, record_id, operation, occurred_at, user_identifier, changed_fields)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)''',
            audit_rows,
        )


def _audit_row(
    table: TableDefinition,
    record_id: Any,
    operation: str,
    occurred_at: datetime,
    user_identifier: Any,
    changed_fields: dict[str, Any],
) -> tuple[str, Any, str, datetime, Any, str]:
    return (
        table.name,
        str(record_id),
        operation,
        occurred_at,
        user_identifier,
        json.dumps(changed_fields, default=str),
    )


def _row_value(row: Any, positions: dict[str, int], field_name: str) -> Any:
    """Read an optional source field from a positional row."""
    position = positions.get(field_name.casefold())
    return row[position] if position is not None else None


def _date_value(value: Any, fallback: datetime) -> datetime:
    """Convert a source date to a timestamp, using the import fallback when absent."""
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return fallback


def _quote_sql_server_identifier(identifier: str) -> str:
    """Quote a SQL Server identifier, including closing brackets safely."""
    return f"[{identifier.replace(']', ']]')}]"
