from pathlib import Path

from pianoweb_migration.config import load_env_file, postgres_config


def test_load_env_file_supports_export_and_quotes(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text('export PGHOST=localhost\nPGPASSWORD="secret value"\n', encoding="utf-8")

    values = load_env_file(env_file)

    assert values == {"PGHOST": "localhost", "PGPASSWORD": "secret value"}


def test_postgres_config_reads_expected_settings() -> None:
    config = postgres_config({
        "PGHOST": "localhost",
        "PGPORT": "5432",
        "PGDATABASE": "pianoweb",
        "PGUSER": "testuser",
        "PGPASSWORD": "secret",
    })

    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "pianoweb"

