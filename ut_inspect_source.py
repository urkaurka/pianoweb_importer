#!/usr/bin/env python3
"""Inspect SQL Server tables without reading table data."""

from __future__ import annotations

import argparse
from pathlib import Path

from pianoweb_migration.config import load_env_file, mssql_connection_string


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()

    try:
        import pyodbc
    except ImportError as error:
        raise SystemExit("Install the SQL Server driver with: pip install pyodbc") from error

    env_values = load_env_file(args.env_file)
    connection = pyodbc.connect(mssql_connection_string(env_values), timeout=10)
    try:
        cursor = connection.cursor()
        rows = cursor.execute(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
        )
        for row in rows:
            print(f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}")
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

