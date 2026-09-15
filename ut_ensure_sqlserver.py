#!/usr/bin/env python3
"""Create or start the SQL Server Docker container from .env settings."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from pianoweb_migration.config import load_env_file, mssql_connection_string


def _parse_connection_string(value: str) -> dict[str, str]:
    """Parse the simple ODBC key/value syntax used by the project."""
    settings: dict[str, str] = {}
    for item in value.split(";"):
        key, separator, raw_value = item.partition("=")
        if not separator:
            continue
        parsed_value = raw_value.strip()
        if parsed_value.startswith("{") and parsed_value.endswith("}"):
            parsed_value = parsed_value[1:-1].replace("}}", "}")
        settings[key.strip().upper()] = parsed_value
    return settings


def _valid_sa_password(password: str) -> bool:
    """Check the SQL Server minimum password complexity policy."""
    character_groups = (
        any(character.islower() for character in password),
        any(character.isupper() for character in password),
        any(character.isdigit() for character in password),
        any(not character.isalnum() for character in password),
    )
    return len(password) >= 8 and sum(character_groups) >= 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--container", default="pianoweb-sqlserver")
    parser.add_argument("--image", default="mcr.microsoft.com/mssql/server:2022-latest")
    parser.add_argument("--volume", default="pianoweb_sqlserver_data")
    args = parser.parse_args()

    connection_settings = _parse_connection_string(
        mssql_connection_string(load_env_file(args.env_file))
    )
    if connection_settings.get("UID", "").lower() != "sa":
        raise SystemExit("MSSQL_CONNECTION_STRING must use UID=sa to create SQL Server")
    password = connection_settings.get("PWD") or connection_settings.get("PASSWORD")
    if not password:
        raise SystemExit("MSSQL_CONNECTION_STRING must define PWD for the SQL Server container")
    if not _valid_sa_password(password):
        raise SystemExit(
            "The SQL Server SA password must be at least 8 characters and use at least "
            "three character groups: lowercase, uppercase, digits, and symbols"
        )

    inspect = subprocess.run(
        ["docker", "inspect", args.container], capture_output=True, text=True
    )
    if inspect.returncode != 0:
        subprocess.run(
            [
                "docker", "run", "-d", "--name", args.container,
                "-e", "ACCEPT_EULA=Y",
                "-e", f"MSSQL_SA_PASSWORD={password}",
                "-p", "1433:1433",
                "-v", f"{args.volume}:/var/opt/mssql",
                args.image,
            ],
            check=True,
        )
        print(f"Created SQL Server container: {args.container}")
        return 0

    running = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if running != "true":
        subprocess.run(["docker", "start", args.container], check=True, capture_output=True)
        print(f"Started SQL Server container: {args.container}")
    else:
        print(f"SQL Server container is already running: {args.container}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
