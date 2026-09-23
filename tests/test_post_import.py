from unittest.mock import Mock

from pianoweb_migration.post_import import (
    ensure_area_purpose_foreign_key,
    ensure_division_department_foreign_key,
    ensure_keyword_purpose_foreign_key,
    ensure_person_type_purpose_foreign_key,
    ensure_referent_department_foreign_key,
    ensure_referent_division_foreign_key,
    ensure_referent_person_type_foreign_key,
    SOURCE_FOREIGN_KEYS,
    PROJECT_PURPOSE_FOREIGN_KEYS,
    ensure_project_purpose_foreign_keys,
    ensure_project_foreign_keys,
    ensure_operator_permission_foreign_key,
    ensure_source_foreign_keys,
    rename_application_columns,
    rename_application_tables,
    remove_project_origin_reference,
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


def test_drops_project_origin_column_and_origin_table_without_other_references() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []

    assert remove_project_origin_reference(cursor) == [
        "Dropped progetti.id_origine",
        "Dropped tabella_origini",
    ]
    assert cursor.execute.call_count == 3
    assert 'DROP COLUMN IF EXISTS "id_origine"' in cursor.execute.call_args_list[1].args[0]
    assert cursor.execute.call_args_list[2].args[0] == 'DROP TABLE IF EXISTS "tabella_origini"'


def test_rejects_origin_references_in_other_tables() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [("attivita", "id_origine")]

    try:
        remove_project_origin_reference(cursor)
    except RuntimeError as error:
        assert "attivita.id_origine" in str(error)
    else:
        raise AssertionError("Expected external origin reference")

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


def test_creates_keyword_purpose_foreign_key_when_no_orphans_exist() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    assert ensure_keyword_purpose_foreign_key(cursor) == "Checked TABELLA_PAROLECHIAVE foreign key: created"
    assert cursor.execute.call_count == 3
    add_foreign_key_sql = cursor.execute.call_args_list[2].args[0]
    assert 'ALTER TABLE "tabella_parolechiave"' in add_foreign_key_sql
    assert 'REFERENCES "tabella_finalita_progetto" ("id")' in add_foreign_key_sql


def test_does_not_create_existing_keyword_purpose_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("tabella_parolechiave_fk_finalita_progetto_fkey",)

    assert ensure_keyword_purpose_foreign_key(cursor) == "Checked TABELLA_PAROLECHIAVE foreign key: already exists"
    assert cursor.execute.call_count == 2


def test_rejects_orphan_keyword_purpose_references() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [(99,)]

    try:
        ensure_keyword_purpose_foreign_key(cursor)
    except RuntimeError as error:
        assert "orphan values: 99" in str(error)
    else:
        raise AssertionError("Expected orphan keyword purpose reference")

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


def test_creates_restored_sqlserver_foreign_keys() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    messages = ensure_source_foreign_keys(cursor)

    assert len(messages) == 8
    assert all(message.endswith("foreign key: created") for message in messages)
    create_statements = [
        cursor.execute.call_args_list[index].args[0]
        for index in range(2, cursor.execute.call_count, 3)
    ]
    assert len(create_statements) == len(SOURCE_FOREIGN_KEYS)
    for foreign_key, statement in zip(SOURCE_FOREIGN_KEYS, create_statements):
        assert f'ADD CONSTRAINT "{foreign_key.name}"' in statement
        assert f'ALTER TABLE "{foreign_key.table}"' in statement
        assert f'FOREIGN KEY ("{foreign_key.column}")' in statement
        assert (
            f'REFERENCES "{foreign_key.referenced_table}" '
            f'("{foreign_key.referenced_column}")'
        ) in statement
        expected_delete_action = f"ON DELETE {foreign_key.on_delete}"
        assert expected_delete_action in statement


def test_does_not_duplicate_restored_sqlserver_foreign_keys() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("existing_constraint",)

    messages = ensure_source_foreign_keys(cursor)

    assert len(messages) == 8
    assert all(message.endswith("foreign key: already exists") for message in messages)
    assert cursor.execute.call_count == 2 * len(SOURCE_FOREIGN_KEYS)


def test_rejects_orphan_values_for_restored_sqlserver_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [(99,)]

    try:
        ensure_source_foreign_keys(cursor)
    except RuntimeError as error:
        assert "FK_Permessi_PermessiTipiOperatore" in str(error)
        assert "orphan values: 99" in str(error)
    else:
        raise AssertionError("Expected orphan source foreign key value")

    assert cursor.execute.call_count == 1


def test_creates_remaining_project_purpose_foreign_keys() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    messages = ensure_project_purpose_foreign_keys(cursor)

    assert len(PROJECT_PURPOSE_FOREIGN_KEYS) == 11
    assert all(message.endswith("foreign key: created") for message in messages)
    create_statements = [
        cursor.execute.call_args_list[index].args[0]
        for index in range(2, cursor.execute.call_count, 3)
    ]
    assert len(create_statements) == len(PROJECT_PURPOSE_FOREIGN_KEYS)
    for foreign_key, statement in zip(PROJECT_PURPOSE_FOREIGN_KEYS, create_statements):
        assert f'ALTER TABLE "{foreign_key.table}"' in statement
        assert f'ADD CONSTRAINT "{foreign_key.name}"' in statement
        assert 'FOREIGN KEY ("fk_finalita_progetto")' in statement
        assert 'REFERENCES "tabella_finalita_progetto" ("id")' in statement
        assert "ON DELETE SET NULL" in statement


def test_does_not_duplicate_project_purpose_foreign_keys() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("existing_constraint",)

    messages = ensure_project_purpose_foreign_keys(cursor)

    assert len(messages) == 11
    assert all(message.endswith("foreign key: already exists") for message in messages)
    assert cursor.execute.call_count == 2 * len(PROJECT_PURPOSE_FOREIGN_KEYS)


def test_rejects_orphan_project_purpose_values() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [(99,)]

    try:
        ensure_project_purpose_foreign_keys(cursor)
    except RuntimeError as error:
        assert "fase_controlli_risultato_fk_finalita_progetto_fkey" in str(error)
        assert "orphan values: 99" in str(error)
    else:
        raise AssertionError("Expected orphan project-purpose reference")

    assert cursor.execute.call_count == 1


def test_creates_project_foreign_keys_for_discovered_tables() -> None:
    tables = ("progetti_agenda", "progetti_allegati", "progetti_aree")
    cursor = Mock()
    cursor.fetchall.side_effect = [
        [(table,) for table in tables],
        *[[] for _ in tables],
    ]
    cursor.fetchone.return_value = None

    messages = ensure_project_foreign_keys(cursor)

    assert len(messages) == len(tables)
    assert all(message.endswith("foreign key: created") for message in messages)
    assert "id_progetto" in cursor.execute.call_args_list[0].args[0]
    create_statements = [
        cursor.execute.call_args_list[index].args[0]
        for index in range(3, cursor.execute.call_count, 3)
    ]
    assert len(create_statements) == len(tables)
    for table, statement in zip(tables, create_statements):
        assert f'ALTER TABLE "{table}"' in statement
        assert f'ADD CONSTRAINT "{table}_id_progetto_fkey"' in statement
        assert 'FOREIGN KEY ("id_progetto")' in statement
        assert 'REFERENCES "progetti" ("id")' in statement


def test_does_not_duplicate_project_foreign_keys() -> None:
    tables = ("progetti_agenda", "progetti_allegati")
    cursor = Mock()
    cursor.fetchall.side_effect = [
        [(table,) for table in tables],
        *[[] for _ in tables],
    ]
    cursor.fetchone.return_value = ("existing_constraint",)

    messages = ensure_project_foreign_keys(cursor)

    assert len(messages) == len(tables)
    assert all(message.endswith("foreign key: already exists") for message in messages)
    assert cursor.execute.call_count == 1 + 2 * len(tables)


def test_rejects_orphan_project_ids() -> None:
    cursor = Mock()
    cursor.fetchall.side_effect = [[("progetti_agenda",)], [(999,)]]

    try:
        ensure_project_foreign_keys(cursor)
    except RuntimeError as error:
        assert "progetti_agenda_id_progetto_fkey" in str(error)
        assert "orphan values: 999" in str(error)
    else:
        raise AssertionError("Expected orphan project reference")

    assert cursor.execute.call_count == 2


def test_creates_operator_permission_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    message = ensure_operator_permission_foreign_key(cursor)

    assert message == "Checked operatoripermessi_idpermesso_fkey foreign key: created"
    assert cursor.execute.call_count == 3
    statement = cursor.execute.call_args_list[2].args[0]
    assert 'ALTER TABLE "operatoripermessi"' in statement
    assert 'ADD CONSTRAINT "operatoripermessi_idpermesso_fkey"' in statement
    assert 'FOREIGN KEY ("idpermesso")' in statement
    assert 'REFERENCES "permessi" ("id")' in statement


def test_does_not_duplicate_operator_permission_foreign_key() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = ("existing_constraint",)

    message = ensure_operator_permission_foreign_key(cursor)

    assert message == "Checked operatoripermessi_idpermesso_fkey foreign key: already exists"
    assert cursor.execute.call_count == 2


def test_rejects_orphan_operator_permission_ids() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [("missing-permission",)]

    try:
        ensure_operator_permission_foreign_key(cursor)
    except RuntimeError as error:
        assert "operatoripermessi_idpermesso_fkey" in str(error)
        assert "orphan values: missing-permission" in str(error)
    else:
        raise AssertionError("Expected orphan operator permission reference")

    assert cursor.execute.call_count == 1
