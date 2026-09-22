from unittest.mock import Mock

from pianoweb_migration.post_import import (
    ensure_area_purpose_foreign_key,
    ensure_division_department_foreign_key,
    ensure_person_type_purpose_foreign_key,
    ensure_referent_department_foreign_key,
    ensure_referent_division_foreign_key,
    ensure_referent_person_type_foreign_key,
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

    assert ensure_area_purpose_foreign_key(cursor) == "Checked AREE foreign key: created"
    assert cursor.execute.call_count == 3


def test_does_not_create_existing_area_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("AREE_FK_FINALITA_PROGETTO_fkey",)

    assert ensure_area_purpose_foreign_key(cursor) == "Checked AREE foreign key: already exists"
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


def test_creates_person_type_purpose_foreign_key_when_no_orphans_exist() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    assert ensure_person_type_purpose_foreign_key(cursor) == "Checked TABELLA_TIPO_PERSONA foreign key: created"
    assert cursor.execute.call_count == 3
    assert 'ALTER TABLE "tabella_tipo_persona"' in cursor.execute.call_args_list[2].args[0]


def test_does_not_create_existing_person_type_purpose_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("tabella_tipo_persona_fk_finalita_progetto_fkey",)

    assert ensure_person_type_purpose_foreign_key(cursor) == "Checked TABELLA_TIPO_PERSONA foreign key: already exists"
    assert cursor.execute.call_count == 2


def test_rejects_orphan_person_type_purpose_references() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [(99,)]

    try:
        ensure_person_type_purpose_foreign_key(cursor)
    except RuntimeError as error:
        assert "orphan values: 99" in str(error)
    else:
        raise AssertionError("Expected orphan person type purpose reference")

    assert cursor.execute.call_count == 1


def test_creates_division_department_foreign_key_when_no_orphans_exist() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    assert ensure_division_department_foreign_key(cursor) == "Checked DIVISIONI foreign key: created"
    assert cursor.execute.call_count == 3
    assert 'ALTER TABLE "divisioni"' in cursor.execute.call_args_list[2].args[0]


def test_does_not_create_existing_division_department_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("divisioni_id_dipartimento_fkey",)

    assert ensure_division_department_foreign_key(cursor) == "Checked DIVISIONI foreign key: already exists"
    assert cursor.execute.call_count == 2


def test_rejects_orphan_division_department_references() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [(99,)]

    try:
        ensure_division_department_foreign_key(cursor)
    except RuntimeError as error:
        assert "orphan values: 99" in str(error)
    else:
        raise AssertionError("Expected orphan division department reference")

    assert cursor.execute.call_count == 1


def test_creates_referent_foreign_keys_when_no_orphans_exist() -> None:
    for ensure_foreign_key, table_name in (
        (ensure_referent_department_foreign_key, "dipartimenti"),
        (ensure_referent_division_foreign_key, "divisioni"),
        (ensure_referent_person_type_foreign_key, "tabella_tipo_persona"),
    ):
        cursor = Mock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None

        assert ensure_foreign_key(cursor).endswith("foreign key: created")
        assert cursor.execute.call_count == 3
        assert table_name in cursor.execute.call_args_list[2].args[0]


def test_does_not_create_existing_referent_foreign_keys() -> None:
    for ensure_foreign_key in (
        ensure_referent_department_foreign_key,
        ensure_referent_division_foreign_key,
        ensure_referent_person_type_foreign_key,
    ):
        cursor = Mock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = ("existing_constraint",)

        assert ensure_foreign_key(cursor).endswith("foreign key: already exists")
        assert cursor.execute.call_count == 2


def test_rejects_orphan_referent_foreign_key_values() -> None:
    for ensure_foreign_key in (
        ensure_referent_department_foreign_key,
        ensure_referent_division_foreign_key,
        ensure_referent_person_type_foreign_key,
    ):
        cursor = Mock()
        cursor.fetchall.return_value = [(99,)]

        try:
            ensure_foreign_key(cursor)
        except RuntimeError as error:
            assert "orphan values: 99" in str(error)
        else:
            raise AssertionError("Expected orphan referent foreign key value")

        assert cursor.execute.call_count == 1
