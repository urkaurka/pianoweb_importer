"""Configuration loading for the database migration tools."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: Path) -> dict[str, str]:
    """Load simple KEY=VALUE and export KEY=VALUE assignments."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if not separator or not key.strip():
            continue
        parsed = shlex.split(value, comments=True)
        values[key.strip()] = parsed[0] if parsed else ""
    return values


def read_setting(name: str, env_values: dict[str, str]) -> str | None:
    """Read a setting from the process environment, then from the env file."""
    return os.environ.get(name) or env_values.get(name)


@dataclass(frozen=True, slots=True)
class PostgresConfig:
    """PostgreSQL connection settings."""

    host: str
    port: int
    database: str
    user: str
    password: str


def postgres_config(env_values: dict[str, str]) -> PostgresConfig:
    """Build PostgreSQL settings from PG* variables."""
    required = {name: read_setting(name, env_values) for name in (
        "PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"
    )}
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(f"Missing PostgreSQL settings: {', '.join(missing)}")
    return PostgresConfig(
        host=required["PGHOST"],
        port=int(required["PGPORT"]),
        database=required["PGDATABASE"],
        user=required["PGUSER"],
        password=required["PGPASSWORD"],
    )


def mssql_connection_string(env_values: dict[str, str]) -> str:
    """Return the SQL Server connection string used as migration source."""
    value = read_setting("MSSQL_CONNECTION_STRING", env_values)
    if not value:
        raise ValueError(
            "Missing MSSQL_CONNECTION_STRING; restore the backup and configure "
            "the SQL Server connection first."
        )
    return value

