"""SQL Server to PostgreSQL type mapping."""

from __future__ import annotations


def postgres_type(sql_server_type: str, max_length: int | None, precision: int | None,
                  scale: int | None) -> str:
    """Map common SQL Server types to PostgreSQL types."""
    source = sql_server_type.lower()
    if source in {"bigint"}:
        return "bigint"
    if source in {"int"}:
        return "integer"
    if source in {"smallint"}:
        return "smallint"
    if source in {"tinyint"}:
        return "smallint"
    if source in {"bit"}:
        return "boolean"
    if source in {"decimal", "numeric"}:
        return f"numeric({precision}, {scale})" if precision else "numeric"
    if source in {"float", "real"}:
        return "double precision" if source == "float" else "real"
    if source in {"money", "smallmoney"}:
        return "numeric(19, 4)"
    if source in {"date"}:
        return "date"
    if source in {"datetime", "datetime2", "smalldatetime"}:
        return "timestamp without time zone"
    if source in {"datetimeoffset"}:
        return "timestamp with time zone"
    if source in {"time"}:
        return "time"
    if source in {"uniqueidentifier"}:
        return "uuid"
    if source in {"binary", "varbinary", "image", "rowversion", "timestamp"}:
        return "bytea"
    if source in {"text", "ntext", "xml"}:
        return "text"
    if source in {"char", "nchar", "varchar", "nvarchar"}:
        if max_length is None or max_length < 0:
            return "text"
        return f"varchar({max_length})"
    return "text"

