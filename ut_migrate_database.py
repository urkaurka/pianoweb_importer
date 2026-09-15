#!/usr/bin/env python3
"""Migrate SQL Server tables to PostgreSQL in batches."""

from __future__ import annotations

import argparse
from pathlib import Path

from pianoweb_migration.config import load_env_file, postgres_config, mssql_connection_string
from pianoweb_migration.migration import migrate_tables


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Truncate matching PostgreSQL tables and import the source data",
    )
    args = parser.parse_args()
    try:
        import psycopg
        import pyodbc
    except ImportError as error:
        raise SystemExit(
            "Install migration dependencies with: pip install -r requirements-migration.txt"
        ) from error

    env_values = load_env_file(args.env_file)
    source_connection = pyodbc.connect(mssql_connection_string(env_values), timeout=10)
    destination = postgres_config(env_values)
    destination_connection = psycopg.connect(
        host=destination.host,
        port=destination.port,
        dbname=destination.database,
        user=destination.user,
        password=destination.password,
    )
    try:
        mode = "apply" if args.apply else "dry-run"
        print(f"Starting migration in {mode} mode.")
        tables = migrate_tables(
            source_connection,
            destination_connection,
            batch_size=args.batch_size,
            apply=args.apply,
        )
        print(f"Processed {len(tables)} table(s).")
    finally:
        destination_connection.close()
        source_connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
