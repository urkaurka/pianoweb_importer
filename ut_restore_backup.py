#!/usr/bin/env python3
"""Drop and restore a SQL Server database from a backup file."""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

from pianoweb_migration.config import load_env_file, mssql_connection_string


def _identifier(value: str) -> str:
    """Quote a SQL Server identifier."""
    return f"[{value.replace(']', ']]')}]"


def _master_connection_string(value: str) -> str:
    """Change the target database in an ODBC connection string to master."""
    pattern = r"(?i)(;\s*(?:DATABASE|INITIAL CATALOG)\s*=)[^;]*"
    if re.search(pattern, value):
        return re.sub(pattern, r"\1master", value)
    return f"{value};DATABASE=master"


def _consume_all_result_sets(cursor: object) -> None:
    """Wait for all result sets emitted by a long-running SQL Server command."""
    nextset = getattr(cursor, "nextset")
    while nextset():
        if getattr(cursor, "description", None):
            cursor.fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--backup-path", type=Path, required=True)
    parser.add_argument("--database", default="pianoweb_source")
    args = parser.parse_args()

    try:
        import pyodbc
    except ImportError as error:
        raise SystemExit(
            "Install migration dependencies with: pip install -r requirements.txt"
        ) from error

    if not args.backup_path.is_absolute():
        raise SystemExit("--backup-path must be an absolute path visible to SQL Server")

    env_values = load_env_file(args.env_file)
    connection_string = _master_connection_string(mssql_connection_string(env_values))
    connection = None
    last_error: Exception | None = None
    for attempt in range(1, 11):
        try:
            connection = pyodbc.connect(connection_string, timeout=3, autocommit=True)
            break
        except pyodbc.Error as error:
            last_error = error
            if attempt == 10:
                raise SystemExit(
                    "SQL Server did not become ready after 20 seconds. "
                    "Check the container logs with: docker logs pianoweb-sqlserver"
                ) from error
            print(f"Waiting for SQL Server ({attempt}/10)...")
            time.sleep(2)

    if connection is None:
        raise RuntimeError("SQL Server connection was not established") from last_error

    backup_path = str(args.backup_path).replace("'", "''")
    try:
        cursor = connection.cursor()
        file_rows = cursor.execute(
            f"RESTORE FILELISTONLY FROM DISK = N'{backup_path}'"
        ).fetchall()
        if not file_rows:
            raise SystemExit("The backup does not contain any database files")

        database_state = cursor.execute(
            "SELECT state_desc FROM sys.databases WHERE name = ?",
            (args.database,),
        ).fetchone()
        if database_state:
            if database_state[0] != "RESTORING":
                cursor.execute(
                    f"ALTER DATABASE {_identifier(args.database)} "
                    "SET SINGLE_USER WITH ROLLBACK IMMEDIATE"
                )
            cursor.execute(f"DROP DATABASE {_identifier(args.database)}")

        moves: list[str] = []
        data_index = 0
        log_index = 0
        for row in file_rows:
            logical_name = str(row[0]).replace("'", "''")
            file_type = row[2]
            if file_type == "L":
                log_index += 1
                destination = f"/var/opt/mssql/data/{args.database}_log{log_index}.ldf"
            else:
                data_index += 1
                extension = "mdf" if data_index == 1 else "ndf"
                destination = f"/var/opt/mssql/data/{args.database}_{data_index}.{extension}"
            moves.append(
                f"MOVE N'{logical_name}' TO N'{destination}'"
            )

        restore_sql = (
            f"RESTORE DATABASE {_identifier(args.database)} "
            f"FROM DISK = N'{backup_path}' WITH "
            + ", ".join(moves)
            + ", RECOVERY, STATS = 10"
        )
        cursor.execute(restore_sql)
        _consume_all_result_sets(cursor)
        restored_state = cursor.execute(
            "SELECT state_desc FROM sys.databases WHERE name = ?",
            (args.database,),
        ).fetchone()
        if not restored_state or restored_state[0] != "ONLINE":
            state = restored_state[0] if restored_state else "missing"
            raise RuntimeError(
                f"Restored database {args.database!r} is not ONLINE; current state: {state}"
            )
        print(f"Restored SQL Server database: {args.database}")
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
