"""Apply PostgreSQL operations required after importing legacy data."""

from __future__ import annotations

from dataclasses import dataclass
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
KEYWORD_PURPOSE_ORPHANS_SQL = """
SELECT keyword."fk_finalita_progetto"
FROM "tabella_parolechiave" AS keyword
LEFT JOIN "tabella_finalita_progetto" AS purpose
    ON purpose."id" = keyword."fk_finalita_progetto"
WHERE keyword."fk_finalita_progetto" IS NOT NULL
  AND purpose."id" IS NULL
ORDER BY keyword."fk_finalita_progetto"
"""
KEYWORD_FOREIGN_KEY_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'tabella_parolechiave'
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND columns.column_name = 'fk_finalita_progetto'
"""
ADD_KEYWORD_FOREIGN_KEY_SQL = """
ALTER TABLE "tabella_parolechiave"
ADD CONSTRAINT "tabella_parolechiave_fk_finalita_progetto_fkey"
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
REFERENT_DEPARTMENT_ORPHANS_SQL = """
SELECT referent."id_dipartimento"
FROM "referenti" AS referent
LEFT JOIN "dipartimenti" AS department
    ON department."id" = referent."id_dipartimento"
WHERE referent."id_dipartimento" IS NOT NULL
  AND department."id" IS NULL
ORDER BY referent."id_dipartimento"
"""
REFERENT_DEPARTMENT_FOREIGN_KEY_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'referenti'
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND columns.column_name = 'id_dipartimento'
"""
ADD_REFERENT_DEPARTMENT_FOREIGN_KEY_SQL = """
ALTER TABLE "referenti"
ADD CONSTRAINT "referenti_id_dipartimento_fkey"
FOREIGN KEY ("id_dipartimento")
REFERENCES "dipartimenti" ("id") ON DELETE SET NULL
"""
REFERENT_DIVISION_ORPHANS_SQL = """
SELECT referent."id_divisione"
FROM "referenti" AS referent
LEFT JOIN "divisioni" AS division
    ON division."id" = referent."id_divisione"
WHERE referent."id_divisione" IS NOT NULL
  AND division."id" IS NULL
ORDER BY referent."id_divisione"
"""
REFERENT_DIVISION_FOREIGN_KEY_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'referenti'
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND columns.column_name = 'id_divisione'
"""
ADD_REFERENT_DIVISION_FOREIGN_KEY_SQL = """
ALTER TABLE "referenti"
ADD CONSTRAINT "referenti_id_divisione_fkey"
FOREIGN KEY ("id_divisione")
REFERENCES "divisioni" ("id") ON DELETE SET NULL
"""
REFERENT_PERSON_TYPE_ORPHANS_SQL = """
SELECT referent."fk_tipo_persona"
FROM "referenti" AS referent
LEFT JOIN "tabella_tipo_persona" AS person_type
    ON person_type."id" = referent."fk_tipo_persona"
WHERE referent."fk_tipo_persona" IS NOT NULL
  AND person_type."id" IS NULL
ORDER BY referent."fk_tipo_persona"
"""
REFERENT_PERSON_TYPE_FOREIGN_KEY_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'referenti'
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND columns.column_name = 'fk_tipo_persona'
"""
ADD_REFERENT_PERSON_TYPE_FOREIGN_KEY_SQL = """
ALTER TABLE "referenti"
ADD CONSTRAINT "referenti_fk_tipo_persona_fkey"
FOREIGN KEY ("fk_tipo_persona")
REFERENCES "tabella_tipo_persona" ("id") ON DELETE SET NULL
"""
ORIGIN_REFERENCE_COLUMNS_SQL = """
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = current_schema()
  AND lower(column_name) = 'id_origine'
  AND table_name <> 'progetti'
UNION
SELECT key_column_usage.table_name, key_column_usage.column_name
FROM information_schema.key_column_usage
JOIN information_schema.referential_constraints
  USING (constraint_catalog, constraint_schema, constraint_name)
JOIN information_schema.constraint_column_usage
  ON constraint_column_usage.constraint_catalog =
       referential_constraints.unique_constraint_catalog
 AND constraint_column_usage.constraint_schema =
       referential_constraints.unique_constraint_schema
 AND constraint_column_usage.constraint_name =
       referential_constraints.unique_constraint_name
WHERE key_column_usage.table_schema = current_schema()
  AND constraint_column_usage.table_schema = current_schema()
  AND constraint_column_usage.table_name = 'tabella_origini'
  AND key_column_usage.table_name <> 'progetti'
ORDER BY table_name, column_name
"""
DROP_PROJECT_ORIGIN_COLUMN_SQL = """
ALTER TABLE IF EXISTS "progetti" DROP COLUMN IF EXISTS "id_origine"
"""
DROP_ORIGIN_TABLE_SQL = 'DROP TABLE IF EXISTS "tabella_origini"'


@dataclass(frozen=True, slots=True)
class ForeignKeyDefinition:
    """A foreign key found in the restored SQL Server database."""

    name: str
    table: str
    column: str
    referenced_table: str
    referenced_column: str
    on_delete: str = "NO ACTION"


SOURCE_FOREIGN_KEYS = (
    ForeignKeyDefinition(
        "FK_Permessi_PermessiTipiOperatore",
        "operatoripermessi",
        "idtipooperatore",
        "permessitipioperatore",
        "id",
    ),
    ForeignKeyDefinition(
        "FK_Permessi_PermessiTipiPermessi",
        "operatoripermessi",
        "idtipopermesso",
        "permessitipipermessi",
        "id",
    ),
    ForeignKeyDefinition(
        "fkTipoProgetto", "progetti", "tipoid", "progetti_tipo", "id"
    ),
    ForeignKeyDefinition(
        "FK_ReportLayouts_ReportDataSources",
        "reportlayouts",
        "datasourceid",
        "reportdatasources",
        "id",
    ),
    ForeignKeyDefinition(
        "FK_ReportLayouts_ReportType",
        "reportlayouts",
        "typeid",
        "reporttype",
        "id",
    ),
    ForeignKeyDefinition(
        "FK_ReportLog_ReportLayouts",
        "reportlog",
        "layoutid",
        "reportlayouts",
        "id",
    ),
    ForeignKeyDefinition(
        "FK_ReportSettings_ReportLayouts",
        "reportsettings",
        "layoutid",
        "reportlayouts",
        "id",
        on_delete="CASCADE",
    ),
    ForeignKeyDefinition(
        "FK_ReportSettings_ReportSettings",
        "reportsettings",
        "referenceid",
        "reportsettings",
        "id",
    ),
)
PROJECT_PURPOSE_FOREIGN_KEYS = tuple(
    ForeignKeyDefinition(
        f"{table}_fk_finalita_progetto_fkey",
        table,
        "fk_finalita_progetto",
        "tabella_finalita_progetto",
        "id",
        on_delete="SET NULL",
    )
    for table in (
        "fase_controlli_risultato",
        "fase_rischio_gravita",
        "gruppi",
        "indicatore_tipologia",
        "progetti",
        "progetti_tipo",
        "referenti_responsabilita",
        "tabella_frequenzecontrolli",
        "tabella_op_aritm_soglia",
        "tabella_operatori_aritmetici",
        "tabella_statoavanzamento",
    )
)
SOURCE_FOREIGN_KEY_EXISTS_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_catalog = constraints.constraint_catalog
   AND columns.constraint_schema = constraints.constraint_schema
   AND columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
JOIN information_schema.constraint_column_usage AS referenced_columns
    ON referenced_columns.constraint_catalog = constraints.constraint_catalog
   AND referenced_columns.constraint_schema = constraints.constraint_schema
   AND referenced_columns.constraint_name = constraints.constraint_name
WHERE constraints.table_schema = current_schema()
  AND constraints.constraint_type = 'FOREIGN KEY'
  AND constraints.table_name = %s
  AND columns.column_name = %s
  AND referenced_columns.table_schema = current_schema()
  AND referenced_columns.table_name = %s
  AND referenced_columns.column_name = %s
"""


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def _ensure_source_foreign_key(cursor: Any, foreign_key: ForeignKeyDefinition) -> str:
    table = _quote_identifier(foreign_key.table)
    column = _quote_identifier(foreign_key.column)
    referenced_table = _quote_identifier(foreign_key.referenced_table)
    referenced_column = _quote_identifier(foreign_key.referenced_column)

    cursor.execute(
        f"""
        SELECT child.{column}
        FROM {table} AS child
        LEFT JOIN {referenced_table} AS parent
            ON parent.{referenced_column} = child.{column}
        WHERE child.{column} IS NOT NULL
          AND parent.{referenced_column} IS NULL
        ORDER BY child.{column}
        """
    )
    orphan_values = [row[0] for row in cursor.fetchall()]
    if orphan_values:
        values = ", ".join(str(value) for value in orphan_values)
        raise RuntimeError(
            f"Cannot create {foreign_key.name} foreign key; orphan values: {values}"
        )

    cursor.execute(
        SOURCE_FOREIGN_KEY_EXISTS_SQL,
        (
            foreign_key.table,
            foreign_key.column,
            foreign_key.referenced_table,
            foreign_key.referenced_column,
        ),
    )
    if cursor.fetchone() is not None:
        return f"Checked {foreign_key.name} foreign key: already exists"

    cursor.execute(
        f"""
        ALTER TABLE {table}
        ADD CONSTRAINT {_quote_identifier(foreign_key.name)}
        FOREIGN KEY ({column})
        REFERENCES {referenced_table} ({referenced_column})
        ON DELETE {foreign_key.on_delete}
        ON UPDATE NO ACTION
        """
    )
    return f"Checked {foreign_key.name} foreign key: created"


def ensure_source_foreign_keys(cursor: Any) -> list[str]:
    """Ensure the foreign keys found in the restored SQL Server database exist."""
    return [
        _ensure_source_foreign_key(cursor, foreign_key)
        for foreign_key in SOURCE_FOREIGN_KEYS
    ]


def ensure_project_purpose_foreign_keys(cursor: Any) -> list[str]:
    """Ensure remaining project-purpose references use foreign keys."""
    return [
        _ensure_source_foreign_key(cursor, foreign_key)
        for foreign_key in PROJECT_PURPOSE_FOREIGN_KEYS
    ]


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


def remove_project_origin_reference(cursor: Any) -> list[str]:
    """Drop the project origin column and lookup table when no other references exist."""
    cursor.execute(ORIGIN_REFERENCE_COLUMNS_SQL)
    references = cursor.fetchall()
    if references:
        descriptions = ", ".join(f"{table}.{column}" for table, column in references)
        raise RuntimeError(
            "Cannot drop tabella_origini; references exist outside progetti: "
            f"{descriptions}"
        )

    cursor.execute(DROP_PROJECT_ORIGIN_COLUMN_SQL)
    cursor.execute(DROP_ORIGIN_TABLE_SQL)
    return [
        "Dropped progetti.id_origine",
        "Dropped tabella_origini",
    ]


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


def ensure_keyword_purpose_foreign_key(cursor: Any) -> str:
    """Ensure keywords reference an existing project purpose."""
    cursor.execute(KEYWORD_PURPOSE_ORPHANS_SQL)
    orphan_values = [row[0] for row in cursor.fetchall()]
    if orphan_values:
        values = ", ".join(str(value) for value in orphan_values)
        raise RuntimeError(
            f"Cannot create TABELLA_PAROLECHIAVE foreign key; orphan values: {values}"
        )
    cursor.execute(KEYWORD_FOREIGN_KEY_SQL)
    if cursor.fetchone() is not None:
        return "Checked TABELLA_PAROLECHIAVE foreign key: already exists"
    cursor.execute(ADD_KEYWORD_FOREIGN_KEY_SQL)
    return "Checked TABELLA_PAROLECHIAVE foreign key: created"


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


def _ensure_referent_foreign_key(
    cursor: Any,
    *,
    orphan_sql: str,
    foreign_key_sql: str,
    add_foreign_key_sql: str,
    label: str,
) -> str:
    cursor.execute(orphan_sql)
    orphan_values = [row[0] for row in cursor.fetchall()]
    if orphan_values:
        values = ", ".join(str(value) for value in orphan_values)
        raise RuntimeError(f"Cannot create {label} foreign key; orphan values: {values}")
    cursor.execute(foreign_key_sql)
    if cursor.fetchone() is not None:
        return f"Checked {label} foreign key: already exists"
    cursor.execute(add_foreign_key_sql)
    return f"Checked {label} foreign key: created"


def ensure_referent_department_foreign_key(cursor: Any) -> str:
    return _ensure_referent_foreign_key(
        cursor,
        orphan_sql=REFERENT_DEPARTMENT_ORPHANS_SQL,
        foreign_key_sql=REFERENT_DEPARTMENT_FOREIGN_KEY_SQL,
        add_foreign_key_sql=ADD_REFERENT_DEPARTMENT_FOREIGN_KEY_SQL,
        label="REFERENTI.id_dipartimento",
    )


def ensure_referent_division_foreign_key(cursor: Any) -> str:
    return _ensure_referent_foreign_key(
        cursor,
        orphan_sql=REFERENT_DIVISION_ORPHANS_SQL,
        foreign_key_sql=REFERENT_DIVISION_FOREIGN_KEY_SQL,
        add_foreign_key_sql=ADD_REFERENT_DIVISION_FOREIGN_KEY_SQL,
        label="REFERENTI.id_divisione",
    )


def ensure_referent_person_type_foreign_key(cursor: Any) -> str:
    return _ensure_referent_foreign_key(
        cursor,
        orphan_sql=REFERENT_PERSON_TYPE_ORPHANS_SQL,
        foreign_key_sql=REFERENT_PERSON_TYPE_FOREIGN_KEY_SQL,
        add_foreign_key_sql=ADD_REFERENT_PERSON_TYPE_FOREIGN_KEY_SQL,
        label="REFERENTI.fk_tipo_persona",
    )


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
            messages.extend(remove_project_origin_reference(cursor))
            messages.append(ensure_area_purpose_foreign_key(cursor))
            messages.append(ensure_person_type_purpose_foreign_key(cursor))
            messages.append(ensure_keyword_purpose_foreign_key(cursor))
            messages.extend(ensure_project_purpose_foreign_keys(cursor))
            messages.append(ensure_division_department_foreign_key(cursor))
            messages.append(ensure_referent_department_foreign_key(cursor))
            messages.append(ensure_referent_division_foreign_key(cursor))
            messages.append(ensure_referent_person_type_foreign_key(cursor))
            messages.extend(ensure_source_foreign_keys(cursor))
            return messages
