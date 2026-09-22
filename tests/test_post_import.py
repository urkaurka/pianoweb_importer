from unittest.mock import Mock

from pianoweb_migration.post_import import (
    ensure_area_purpose_foreign_key,
    rename_application_columns,
    rename_application_tables,
)


def test_renames_mixed_case_application_columns() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [("aree", "FK_FINALITA_PROGETTO"), ("aree", "descrizione")]

    result = rename_application_columns(cursor)

    assert result == ["aree.FK_FINALITA_PROGETTO -> fk_finalita_progetto"]
    assert cursor.execute.call_count == 2
    assert 'RENAME COLUMN "FK_FINALITA_PROGETTO" TO "fk_finalita_progetto"' in cursor.execute.call_args_list[1].args[0]


def test_rejects_lowercase_column_name_collisions() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [("aree", "Id"), ("aree", "ID")]

    try:
        rename_application_columns(cursor)
    except RuntimeError as error:
        assert "would collide" in str(error)
    else:
        raise AssertionError("Expected lowercase column name collision")

    assert cursor.execute.call_count == 1


def test_renames_mixed_case_application_tables() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [("AREE",), ("audit_log",)]

    result = rename_application_tables(cursor)

    assert result == ["AREE -> aree"]
    assert cursor.execute.call_count == 2
    assert 'RENAME TO "aree"' in cursor.execute.call_args_list[1].args[0]


def test_rejects_lowercase_table_name_collisions() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [("AREE",), ("aree",)]

    try:
        rename_application_tables(cursor)
    except RuntimeError as error:
        assert "would collide" in str(error)
    else:
        raise AssertionError("Expected lowercase table name collision")

    assert cursor.execute.call_count == 1


def test_creates_area_foreign_key_when_no_orphans_exist() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    assert ensure_area_purpose_foreign_key(cursor) == "AREE foreign key created"
    assert cursor.execute.call_count == 3


def test_does_not_create_existing_area_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("AREE_FK_FINALITA_PROGETTO_fkey",)

    assert ensure_area_purpose_foreign_key(cursor) == "AREE foreign key already exists"
    assert cursor.execute.call_count == 2


def test_rejects_orphan_area_references() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [(99,)]

    try:
        ensure_area_purpose_foreign_key(cursor)
    except RuntimeError as error:
        assert "orphan values: 99" in str(error)
    else:
        raise AssertionError("Expected orphan area reference")

    assert cursor.execute.call_count == 1
