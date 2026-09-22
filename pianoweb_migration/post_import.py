"""Apply PostgreSQL operations required after importing legacy data."""

from __future__ import annotations

from typing import Any

APPLICATION_TABLES_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'
  AND table_name NOT LIKE 'django\\_%' ESCAPE '\\'
  AND table_name NOT LIKE 'auth\\_%' ESCAPE '\\'
ORDER BY table_name
"""
APPLICATION_COLUMNS_SQL = """
SELECT table_name, column_name FROM information_schema.columns
WHERE table_schema = current_schema()
  AND table_name NOT LIKE 'django\\_%' ESCAPE '\\'
  AND table_name NOT LIKE 'auth\\_%' ESCAPE '\\'
ORDER BY table_name, ordinal_position
"""
AUDIT_TABLE_NAMES_SQL = """
UPDATE "audit_log" SET table_name = lower(table_name)
WHERE table_name <> lower(table_name)
"""
AREA_PURPOSE_ORPHANS_SQL = """
SELECT area."fk_finalita_progetto" FROM "aree" AS area
LEFT JOIN "tabella_finalita_progetto" AS purpose
    ON purpose."id" = area."fk_finalita_progetto"
WHERE area."fk_finalita_progetto" IS NOT NULL
  AND purpose."id" IS NULL
ORDER BY area."fk_finalita_progetto"
"""
AREA_FOREIGN_KEY_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'aree'
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND columns.column_name = 'fk_finalita_progetto'
"""
PERSON_TYPE_PURPOSE_ORPHANS_SQL = """
SELECT person_type."fk_finalita_progetto"
FROM "tabella_tipo_persona" AS person_type
LEFT JOIN "tabella_finalita_progetto" AS purpose
    ON purpose."id" = person_type."fk_finalita_progetto"
WHERE person_type."fk_finalita_progetto" IS NOT NULL
  AND purpose."id" IS NULL
ORDER BY person_type."fk_finalita_progetto"
"""
PERSON_TYPE_FOREIGN_KEY_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'tabella_tipo_persona'
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND columns.column_name = 'fk_finalita_progetto'
"""
ADD_AREA_FOREIGN_KEY_SQL = """
ALTER TABLE "aree"
ADD CONSTRAINT "aree_fk_finalita_progetto_fkey"
FOREIGN KEY ("fk_finalita_progetto")
REFERENCES "tabella_finalita_progetto" ("id") ON DELETE SET NULL
"""
ADD_PERSON_TYPE_FOREIGN_KEY_SQL = """
ALTER TABLE "tabella_tipo_persona"
ADD CONSTRAINT "tabella_tipo_persona_fk_finalita_progetto_fkey"
FOREIGN KEY ("fk_finalita_progetto")
REFERENCES "tabella_finalita_progetto" ("id") ON DELETE SET NULL
"""
DIVISION_DEPARTMENT_ORPHANS_SQL = """
SELECT division."id_dipartimento"
FROM "divisioni" AS division
LEFT JOIN "dipartimenti" AS department
    ON department."id" = division."id_dipartimento"
WHERE division."id_dipartimento" IS NOT NULL
  AND department."id" IS NULL
ORDER BY division."id_dipartimento"
"""
DIVISION_DEPARTMENT_FOREIGN_KEY_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'divisioni'
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND columns.column_name = 'id_dipartimento'
"""
ADD_DIVISION_DEPARTMENT_FOREIGN_KEY_SQL = """
ALTER TABLE "divisioni"
ADD CONSTRAINT "divisioni_id_dipartimento_fkey"
FOREIGN KEY ("id_dipartimento")
REFERENCES "dipartimenti" ("id") ON DELETE SET NULL
"""


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def rename_application_tables(cursor: Any) -> list[str]:
    cursor.execute(APPLICATION_TABLES_SQL)
    table_names = [row[0] for row in cursor.fetchall()]
    targets = [name.lower() for name in table_names]
    if len(targets) != len(set(targets)):
        raise RuntimeError("Cannot rename application tables; lowercase table names would collide")
    existing_names = set(table_names)
    for source_name, target_name in zip(table_names, targets):
        if source_name != target_name and target_name in existing_names:
            raise RuntimeError(f"Cannot rename {source_name}; table {target_name} already exists")
    renamed_tables = []
    for source_name, target_name in zip(table_names, targets):
        if source_name == target_name:
            continue
        cursor.execute(f"ALTER TABLE {_quote_identifier(source_name)} RENAME TO {_quote_identifier(target_name)}")
        renamed_tables.append(f"{source_name} -> {target_name}")
    return renamed_tables


def rename_application_columns(cursor: Any) -> list[str]:
    cursor.execute(APPLICATION_COLUMNS_SQL)
    columns_by_table: dict[str, list[str]] = {}
    for table_name, column_name in cursor.fetchall():
        columns_by_table.setdefault(table_name, []).append(column_name)
    renamed_columns = []
    for table_name, column_names in columns_by_table.items():
        targets = [name.lower() for name in column_names]
        if len(targets) != len(set(targets)):
            raise RuntimeError(f"Cannot rename columns in {table_name}; lowercase column names would collide")
        for source_name, target_name in zip(column_names, targets):
            if source_name == target_name:
                continue
            cursor.execute(
                f"ALTER TABLE {_quote_identifier(table_name)} "
                f"RENAME COLUMN {_quote_identifier(source_name)} TO {_quote_identifier(target_name)}"
            )
            renamed_columns.append(f"{table_name}.{source_name} -> {target_name}")
    return renamed_columns


def normalize_audit_table_names(cursor: Any) -> str:
    cursor.execute(AUDIT_TABLE_NAMES_SQL)
    return "Audit table names normalized"


def ensure_area_purpose_foreign_key(cursor: Any) -> str:
    cursor.execute(AREA_PURPOSE_ORPHANS_SQL)
    orphan_values = [row[0] for row in cursor.fetchall()]
    if orphan_values:
        values = ", ".join(str(value) for value in orphan_values)
        raise RuntimeError(f"Cannot create AREE foreign key; orphan values: {values}")
    cursor.execute(AREA_FOREIGN_KEY_SQL)
    if cursor.fetchone() is not None:
        return "Checked AREE foreign key: already exists"
    cursor.execute(ADD_AREA_FOREIGN_KEY_SQL)
    return "Checked AREE foreign key: created"


def ensure_person_type_purpose_foreign_key(cursor: Any) -> str:
    """Ensure person types reference an existing project purpose."""
    cursor.execute(PERSON_TYPE_PURPOSE_ORPHANS_SQL)
    orphan_values = [row[0] for row in cursor.fetchall()]
    if orphan_values:
        values = ", ".join(str(value) for value in orphan_values)
        raise RuntimeError(
            f"Cannot create TABELLA_TIPO_PERSONA foreign key; orphan values: {values}"
        )
    cursor.execute(PERSON_TYPE_FOREIGN_KEY_SQL)
    if cursor.fetchone() is not None:
        return "Checked TABELLA_TIPO_PERSONA foreign key: already exists"
    cursor.execute(ADD_PERSON_TYPE_FOREIGN_KEY_SQL)
    return "Checked TABELLA_TIPO_PERSONA foreign key: created"


def ensure_division_department_foreign_key(cursor: Any) -> str:
    """Ensure divisions reference an existing department."""
    cursor.execute(DIVISION_DEPARTMENT_ORPHANS_SQL)
    orphan_values = [row[0] for row in cursor.fetchall()]
    if orphan_values:
        values = ", ".join(str(value) for value in orphan_values)
        raise RuntimeError(
            f"Cannot create DIVISIONI foreign key; orphan values: {values}"
        )
    cursor.execute(DIVISION_DEPARTMENT_FOREIGN_KEY_SQL)
    if cursor.fetchone() is not None:
        return "Checked DIVISIONI foreign key: already exists"
    cursor.execute(ADD_DIVISION_DEPARTMENT_FOREIGN_KEY_SQL)
    return "Checked DIVISIONI foreign key: created"


def run_post_import_operations(connection: Any) -> list[str]:
    """Normalize imported objects and add required constraints atomically."""
    with connection.transaction():
        with connection.cursor() as cursor:
            renamed_tables = rename_application_tables(cursor)
            renamed_columns = rename_application_columns(cursor)
            normalize_audit_table_names(cursor)
            messages = [
                f"Renamed {len(renamed_tables)} application table(s)",
                f"Renamed {len(renamed_columns)} application column(s)",
            ]
            messages.append(ensure_area_purpose_foreign_key(cursor))
            messages.append(ensure_person_type_purpose_foreign_key(cursor))
            messages.append(ensure_division_department_foreign_key(cursor))
            return messages
