#!/usr/bin/env python3
"""Apply PostgreSQL operations that must run after the import."""

from __future__ import annotations

import argparse
from pathlib import Path

from pianoweb_migration.config import load_env_file, postgres_config
from pianoweb_migration.post_import import run_post_import_operations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    try:
        import psycopg
    except ImportError as error:
        raise SystemExit(
            "Install migration dependencies with: pip install -r requirements.txt"
        ) from error
    config = postgres_config(load_env_file(args.env_file))
    connection = psycopg.connect(
        host=config.host, port=config.port, dbname=config.database,
        user=config.user, password=config.password,
        options="-c search_path=dbo,public",
    )
    try:
        for message in run_post_import_operations(connection):
            print(message)
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
