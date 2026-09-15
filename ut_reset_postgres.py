#!/usr/bin/env python3
"""Drop and recreate the PostgreSQL destination database."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()

    try:
        import psycopg
        from psycopg import sql
    except ImportError as error:
        raise SystemExit(
            "Install migration dependencies with: pip install -r requirements.txt"
        ) from error

    from pianoweb_migration.config import load_env_file, postgres_config

    config = postgres_config(load_env_file(args.env_file))
    if config.database == "postgres":
        raise SystemExit("Refusing to reset the PostgreSQL maintenance database")

    connection = psycopg.connect(
        host=config.host,
        port=config.port,
        dbname="postgres",
        user=config.user,
        password=config.password,
        autocommit=True,
    )
    try:
        privileges = connection.execute(
            "SELECT rolcreatedb OR rolsuper FROM pg_roles WHERE rolname = current_user"
        ).fetchone()
        if not privileges or not privileges[0]:
            _recreate_database_with_sudo(config.database, config.user)
            return 0
        connection.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            (config.database,),
        )
        connection.execute(sql.SQL("DROP DATABASE IF EXISTS {}\n").format(sql.Identifier(config.database)))
        connection.execute(sql.SQL("CREATE DATABASE {}\n").format(sql.Identifier(config.database)))
        print(f"Recreated PostgreSQL database: {config.database}")
    finally:
        connection.close()
    return 0


def _recreate_database_with_sudo(database: str, owner: str) -> None:
    """Recreate a local PostgreSQL database through the system postgres user."""
    quoted_database = _quote_identifier(database)
    quoted_owner = _quote_identifier(owner)
    database_literal = _quote_literal(database)
    commands = (
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = {database_literal} AND pid <> pg_backend_pid()",
        f"DROP DATABASE IF EXISTS {quoted_database}",
        f"CREATE DATABASE {quoted_database} OWNER {quoted_owner}",
    )
    print("Using sudo to recreate the PostgreSQL destination database.")
    for command in commands:
        subprocess.run(
            ["sudo", "-u", "postgres", "psql", "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-c", command],
            check=True,
        )
    print(f"Recreated PostgreSQL database: {database}")


def _quote_identifier(value: str) -> str:
    """Quote a PostgreSQL identifier."""
    return '"' + value.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    """Quote a PostgreSQL string literal."""
    return "'" + value.replace("'", "''") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
