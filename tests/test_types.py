from pianoweb_migration.types import postgres_type


def test_common_sql_server_types_are_mapped() -> None:
    assert postgres_type("int", None, None, None) == "integer"
    assert postgres_type("nvarchar", 80, None, None) == "varchar(80)"
    assert postgres_type("decimal", None, 12, 2) == "numeric(12, 2)"
    assert postgres_type("uniqueidentifier", None, None, None) == "uuid"

