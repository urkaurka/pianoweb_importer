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
PROJECT_FOREIGN_KEY_TABLES_SQL = """
SELECT columns.table_name
FROM information_schema.columns AS columns
JOIN information_schema.tables AS tables
  ON tables.table_schema = columns.table_schema
 AND tables.table_name = columns.table_name
 AND tables.table_type = 'BASE TABLE'
WHERE columns.table_schema = current_schema()
  AND columns.column_name = 'id_progetto'
ORDER BY columns.table_name
"""
PROJECT_GROUP_ORPHANS_SQL = """
SELECT child."id", child."id_progetto", child."id_gruppo"
FROM "progetti_gruppi" AS child
LEFT JOIN "gruppi" AS parent ON parent."id" = child."id_gruppo"
WHERE parent."id" IS NULL
ORDER BY child."id"
"""
DELETE_PROJECT_GROUP_ORPHANS_SQL = """
DELETE FROM "progetti_gruppi" AS child
WHERE child."id" = ANY(%s)
  AND NOT EXISTS (
      SELECT 1 FROM "gruppi" AS parent
      WHERE parent."id" = child."id_gruppo"
  )
RETURNING child."id"
"""
PROJECT_DIVISION_ORPHANS_SQL = """
SELECT child."id", child."id_progetto", child."id_divisione"
FROM "progetti_divisioni" AS child
LEFT JOIN "divisioni" AS parent ON parent."id" = child."id_divisione"
WHERE parent."id" IS NULL
ORDER BY child."id"
"""
PROJECT_DIVISION_ROW_COUNT_SQL = 'SELECT count(*) FROM "progetti_divisioni"'
DELETE_PROJECT_DIVISION_ORPHANS_SQL = """
DELETE FROM "progetti_divisioni" AS child
WHERE child."id" = ANY(%s)
  AND NOT EXISTS (
      SELECT 1 FROM "divisioni" AS parent
      WHERE parent."id" = child."id_divisione"
  )
RETURNING child."id"
"""
PROJECT_MACROPHASE_ORPHANS_SQL = """
SELECT child."id_progetto", child."id_macrofase"
FROM "progetti_macrofasi_fasi" AS child
LEFT JOIN "progetti_macrofasi" AS parent
  ON parent."id_progetto" = child."id_progetto"
 AND parent."id_macrofase" = child."id_macrofase"
WHERE parent."id_progetto" IS NULL
ORDER BY child."id_progetto", child."id_macrofase"
"""
PROJECT_MACROPHASE_FOREIGN_KEY_SQL = """
SELECT constraint_name
FROM information_schema.table_constraints
WHERE table_schema = current_schema()
  AND table_name = 'progetti_macrofasi_fasi'
  AND constraint_name = 'progetti_macrofasi_fasi_id_progetto_id_macrofase_fkey'
  AND constraint_type = 'FOREIGN KEY'
"""
ADD_PROJECT_MACROPHASE_FOREIGN_KEY_SQL = """
ALTER TABLE "progetti_macrofasi_fasi"
ADD CONSTRAINT "progetti_macrofasi_fasi_id_progetto_id_macrofase_fkey"
FOREIGN KEY ("id_progetto", "id_macrofase")
REFERENCES "progetti_macrofasi" ("id_progetto", "id_macrofase")
"""
STATO_AVANZAMENTO_ID_UNIQUE_EXISTS_SQL = """
SELECT constraints.constraint_name
FROM information_schema.table_constraints AS constraints
JOIN information_schema.key_column_usage AS columns
    ON columns.constraint_catalog = constraints.constraint_catalog
   AND columns.constraint_schema = constraints.constraint_schema
   AND columns.constraint_name = constraints.constraint_name
   AND columns.table_schema = constraints.table_schema
WHERE constraints.table_schema = current_schema()
  AND constraints.table_name = 'tabella_statoavanzamento'
  AND constraints.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
GROUP BY constraints.constraint_name
HAVING count(*) = 1 AND bool_or(columns.column_name = 'id')
"""
STATO_AVANZAMENTO_ID_DUPLICATES_SQL = """
SELECT "id", count(*)
FROM "tabella_statoavanzamento"
GROUP BY "id"
HAVING "id" IS NULL OR count(*) > 1
ORDER BY "id"
"""
ADD_STATO_AVANZAMENTO_ID_UNIQUE_SQL = """
ALTER TABLE "tabella_statoavanzamento"
ADD CONSTRAINT "tabella_statoavanzamento_id_key" UNIQUE ("id")
"""
PROJECT_AREA_ORPHANS_SQL = """
SELECT child."id", child."id_area"
FROM "progetti_aree" AS child
LEFT JOIN "aree" AS parent ON parent."id" = child."id_area"
WHERE child."id_area" IS NOT NULL AND parent."id" IS NULL
ORDER BY child."id"
"""
PROJECT_AREA_ROW_COUNT_SQL = 'SELECT count(*) FROM "progetti_aree"'
DELETE_PROJECT_AREA_ORPHANS_SQL = """
DELETE FROM "progetti_aree" AS child
WHERE child."id" = ANY(%s)
  AND NOT EXISTS (
      SELECT 1 FROM "aree" AS parent WHERE parent."id" = child."id_area"
  )
RETURNING child."id"
"""
PROJECT_IMPORTANCE_ORPHANS_SQL = """
SELECT project."id", project."id_classe_importanza"
FROM "progetti" AS project
LEFT JOIN "tabella_classiimportanza" AS importance
    ON importance."id" = project."id_classe_importanza"
WHERE project."id_classe_importanza" IS NOT NULL
  AND importance."id" IS NULL
ORDER BY project."id"
"""
PROJECT_ROW_COUNT_SQL = 'SELECT count(*) FROM "progetti"'
NULL_PROJECT_IMPORTANCE_ORPHANS_SQL = """
UPDATE "progetti" AS project
SET "id_classe_importanza" = NULL
WHERE project."id" = ANY(%s)
  AND NOT EXISTS (
      SELECT 1 FROM "tabella_classiimportanza" AS importance
      WHERE importance."id" = project."id_classe_importanza"
  )
RETURNING project."id"
"""
COMPOSITE_FOREIGN_KEY_EXISTS_SQL = """
SELECT constraint_name
FROM information_schema.table_constraints
WHERE table_schema = current_schema()
  AND table_name = %s
  AND constraint_name = %s
  AND constraint_type = 'FOREIGN KEY'
"""


@dataclass(frozen=True, slots=True)
class ForeignKeyDefinition:
    """A foreign key found in the restored SQL Server database."""

    name: str
    table: str
    column: str
    referenced_table: str
    referenced_column: str
    on_delete: str = "NO ACTION"


@dataclass(frozen=True, slots=True)
class CompositeForeignKeyDefinition:
    """A composite foreign key inferred from related project columns."""

    name: str
    table: str
    columns: tuple[str, ...]
    referenced_table: str
    referenced_columns: tuple[str, ...]


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
INFERRED_FOREIGN_KEYS = tuple(
    ForeignKeyDefinition(
        f"{table}_{column}_fkey", table, column, referenced_table, referenced_column
    )
    for table, column, referenced_table, referenced_column in (
        ("fase", "fk_fase", "fase", "pk"),
        ("fase", "fk_progetto", "progetti", "id"),
        ("fase_controlli", "fk_fase", "fase", "pk"),
        ("fase_controlli", "fk_controllo_periodicita", "tabella_frequenzecontrolli", "id"),
        ("fase_controlli", "fk_controllo_risultato", "fase_controlli_risultato", "id"),
        ("fase_costo", "fk_fase", "fase", "pk"),
        ("fase_persona", "fk_fase", "fase", "pk"),
        ("fase_persona", "fk_persona", "referenti", "id"),
        ("fase_prodotto", "fk_fase", "fase", "pk"),
        ("fase_rischio", "fk_fase", "fase", "pk"),
        ("fase_rischio", "fk_rischio_gravita", "fase_rischio_gravita", "id"),
        ("fase_stato_avanzamento", "fk_fase", "fase", "pk"),
        ("fase_stato_avanzamento", "fk_fase_colore", "tabella_staticolore", "id"),
        ("fase_stato_avanzamento", "fk_stato_avanzamento", "tabella_statoavanzamento", "id"),
        ("indicatore", "fk_stati_colore", "tabella_staticolore", "id"),
        ("indicatore", "fk_valutazione_finale_percentuale", "tabella_valutazione_finale", "pk"),
        ("indicatore", "fk_indicatore_tipologia", "indicatore_tipologia", "id"),
        ("indicatore", "fk_progetto", "progetti", "id"),
        ("indicatore", "fk_operatore_aritmetico", "tabella_operatori_aritmetici", "id"),
        ("indicatore", "fk_tipo_dato", "tabella_tipo_dato_indicatore", "id"),
        ("indicatore", "fk_operatore_aritmetico_soglia", "tabella_op_aritm_soglia", "id"),
        ("indicatore_progetti", "fk_indicatore", "indicatore", "pk"),
        ("indicatore_progetti", "fk_progetto", "progetti", "id"),
        ("indicatore_progetti", "fk_valutazione", "valutazione", "pk"),
        ("operatoripianoweb", "id_dip", "dipartimenti", "id"),
        ("progetti", "id_classe_importanza", "tabella_classiimportanza", "id"),
        ("progetti_aree", "id_area", "aree", "id"),
        ("progetti_documenti", "id_fase", "fase", "pk"),
        ("progetti_documenti", "id_documento", "documenti", "id"),
        ("progetti_macrofasi_fasi", "id_fase", "fase", "pk"),
        ("progetti_macrofasi_fasi_referenti", "id_fase", "fase", "pk"),
        ("progetti_macrofasi_fasi_referenti", "id_referente", "referenti", "id"),
        ("progetti_macrofasi_fasi_referenti", "id_coinvolgimento", "tabella_coinvolgimenti", "id"),
        ("progetti_macrofasi_fasi_stati", "id_fase", "fase", "pk"),
        ("progetti_macrofasi_fasi_stati", "id_colore", "tabella_staticolore", "id"),
        ("progetti_macrofasi_fasi_stati", "id_stato_avanzamento", "tabella_statoavanzamento", "id"),
        ("progetti_macrofasi_referenti", "id_referente", "referenti", "id"),
        ("progetti_macrofasi_referenti", "id_coinvolgimento", "tabella_coinvolgimenti", "id"),
        ("progetti_macrofasi_stati", "id_colore", "tabella_staticolore", "id"),
        ("progetti_macrofasi_stati", "id_stato_avanzamento", "tabella_statoavanzamento", "id"),
        ("progetti_referenti", "id_referente", "referenti", "id"),
        ("progetti_referenti", "id_coinvolgimento", "tabella_coinvolgimenti", "id"),
        ("progetti_referenti", "id_referenti_responsabilita", "referenti_responsabilita", "id"),
        ("progetti_rischi", "id_fase", "fase", "pk"),
        ("progetti_rischi", "id_rischio", "rischi", "id"),
        ("progetti_stati", "id_colore", "tabella_staticolore", "id"),
        ("progetti_stati", "id_stato_avanzamento", "tabella_statoavanzamento", "id"),
        ("relazioni_progetti", "id_progetto_padre", "progetti", "id"),
        ("relazioni_progetti", "id_progetto_figlio", "progetti", "id"),
        ("rischi", "id_gravita", "tabella_gravitarischi", "id"),
        ("valutazione", "fk_progetto", "progetti", "id"),
        ("valutazione", "fk_val_progetto", "valutazione_progetto", "pk"),
        ("valutazione", "fk_val_obiettivi", "valutazione_obiettivi", "pk"),
        ("valutazione", "fk_val_responsabilita", "valutazione_responsabilita", "pk"),
        ("valutazione", "fk_val_pianificazione", "valutazione_pianificazione", "pk"),
        ("valutazione", "fk_val_avanzamento", "valutazione_avanzamento", "pk"),
    )
)
INFERRED_COMPOSITE_FOREIGN_KEYS = (
    CompositeForeignKeyDefinition(
        "progetti_documenti_project_macrophase_fkey",
        "progetti_documenti",
        ("id_progetto", "id_macrofase"),
        "progetti_macrofasi",
        ("id_progetto", "id_macrofase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_documenti_project_macrophase_phase_fkey",
        "progetti_documenti",
        ("id_progetto", "id_macrofase", "id_fase"),
        "progetti_macrofasi_fasi",
        ("id_progetto", "id_macrofase", "id_fase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_macrofasi_fasi_referenti_project_macrophase_fkey",
        "progetti_macrofasi_fasi_referenti",
        ("id_progetto", "id_macrofase"),
        "progetti_macrofasi",
        ("id_progetto", "id_macrofase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_macrofasi_fasi_referenti_project_macrophase_phase_fkey",
        "progetti_macrofasi_fasi_referenti",
        ("id_progetto", "id_macrofase", "id_fase"),
        "progetti_macrofasi_fasi",
        ("id_progetto", "id_macrofase", "id_fase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_macrofasi_fasi_stati_project_macrophase_fkey",
        "progetti_macrofasi_fasi_stati",
        ("id_progetto", "id_macrofase"),
        "progetti_macrofasi",
        ("id_progetto", "id_macrofase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_macrofasi_fasi_stati_project_macrophase_phase_fkey",
        "progetti_macrofasi_fasi_stati",
        ("id_progetto", "id_macrofase", "id_fase"),
        "progetti_macrofasi_fasi",
        ("id_progetto", "id_macrofase", "id_fase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_macrofasi_referenti_project_macrophase_fkey",
        "progetti_macrofasi_referenti",
        ("id_progetto", "id_macrofase"),
        "progetti_macrofasi",
        ("id_progetto", "id_macrofase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_rischi_project_macrophase_fkey",
        "progetti_rischi",
        ("id_progetto", "id_macrofase"),
        "progetti_macrofasi",
        ("id_progetto", "id_macrofase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_macrofasi_stati_project_macrophase_fkey",
        "progetti_macrofasi_stati",
        ("id_progetto", "id_macrofase"),
        "progetti_macrofasi",
        ("id_progetto", "id_macrofase"),
    ),
    CompositeForeignKeyDefinition(
        "progetti_rischi_project_macrophase_phase_fkey",
        "progetti_rischi",
        ("id_progetto", "id_macrofase", "id_fase"),
        "progetti_macrofasi_fasi",
        ("id_progetto", "id_macrofase", "id_fase"),
    ),
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


def ensure_stato_avanzamento_id_unique(cursor: Any) -> str:
    """Ensure stato-avanzamento IDs are protected as a referenced key."""
    cursor.execute(STATO_AVANZAMENTO_ID_UNIQUE_EXISTS_SQL)
    if cursor.fetchone() is not None:
        return "Checked tabella_statoavanzamento.id unique constraint: already exists"

    cursor.execute(STATO_AVANZAMENTO_ID_DUPLICATES_SQL)
    invalid_ids = cursor.fetchall()
    if invalid_ids:
        values = ", ".join(
            f"{value} ({count} rows)" for value, count in invalid_ids
        )
        raise RuntimeError(
            "Cannot make tabella_statoavanzamento.id unique; "
            f"duplicate or null IDs: {values}"
        )

    cursor.execute(ADD_STATO_AVANZAMENTO_ID_UNIQUE_SQL)
    return "Checked tabella_statoavanzamento.id unique constraint: created"


def _cleanup_small_project_area_orphans(cursor: Any) -> list[str]:
    cursor.execute(PROJECT_AREA_ORPHANS_SQL)
    orphan_rows = cursor.fetchall()
    if not orphan_rows:
        return []

    cursor.execute(PROJECT_AREA_ROW_COUNT_SQL)
    total_rows = cursor.fetchone()[0]
    orphan_count = len(orphan_rows)
    percentage = orphan_count / total_rows * 100 if total_rows else 100.0
    if orphan_count * 100 >= total_rows * 3:
        raise RuntimeError(
            "Cannot create progetti_aree.id_area foreign key; "
            f"{orphan_count}/{total_rows} rows are orphaned "
            f"({percentage:.2f}%), threshold is below 3%"
        )

    orphan_ids = [row[0] for row in orphan_rows]
    missing_area_ids = sorted({row[1] for row in orphan_rows})
    cursor.execute(DELETE_PROJECT_AREA_ORPHANS_SQL, (orphan_ids,))
    deleted_ids = [row[0] for row in cursor.fetchall()]
    if set(deleted_ids) != set(orphan_ids):
        raise RuntimeError(
            "Could not delete every orphan row from progetti_aree; "
            f"expected IDs {orphan_ids}, deleted IDs {deleted_ids}"
        )
    return [
        f"Found {orphan_count} orphan row(s) in progetti_aree "
        f"({orphan_count}/{total_rows}, {percentage:.2f}%); "
        f"missing area IDs: {', '.join(map(str, missing_area_ids))}",
        f"Deleted {len(deleted_ids)} orphan row(s) from progetti_aree",
    ]


def _clear_small_project_importance_orphans(cursor: Any) -> list[str]:
    cursor.execute(PROJECT_IMPORTANCE_ORPHANS_SQL)
    orphan_rows = cursor.fetchall()
    if not orphan_rows:
        return []

    cursor.execute(PROJECT_ROW_COUNT_SQL)
    total_rows = cursor.fetchone()[0]
    orphan_count = len(orphan_rows)
    percentage = orphan_count / total_rows * 100 if total_rows else 100.0
    if orphan_count * 100 >= total_rows * 3:
        raise RuntimeError(
            "Cannot create progetti.id_classe_importanza foreign key; "
            f"{orphan_count}/{total_rows} projects have orphan values "
            f"({percentage:.2f}%), threshold is below 3%"
        )

    project_ids = [row[0] for row in orphan_rows]
    missing_importance_ids = sorted({row[1] for row in orphan_rows})
    cursor.execute(NULL_PROJECT_IMPORTANCE_ORPHANS_SQL, (project_ids,))
    updated_ids = [row[0] for row in cursor.fetchall()]
    if set(updated_ids) != set(project_ids):
        raise RuntimeError(
            "Could not clear every orphan importance value from progetti; "
            f"expected project IDs {project_ids}, updated IDs {updated_ids}"
        )
    return [
        f"Found {orphan_count} orphan project importance value(s) "
        f"({orphan_count}/{total_rows}, {percentage:.2f}%); "
        f"missing importance IDs: {', '.join(map(str, missing_importance_ids))}",
        f"Cleared orphan importance values for {len(updated_ids)} project(s)",
    ]


def _ensure_composite_foreign_key(
    cursor: Any, foreign_key: CompositeForeignKeyDefinition
) -> str:
    table = _quote_identifier(foreign_key.table)
    referenced_table = _quote_identifier(foreign_key.referenced_table)
    child_columns = [
        _quote_identifier(column) for column in foreign_key.columns
    ]
    parent_columns = [
        _quote_identifier(column) for column in foreign_key.referenced_columns
    ]
    if len(child_columns) != len(parent_columns):
        raise ValueError(
            f"Composite foreign key {foreign_key.name} has mismatched column counts"
        )

    all_child_columns_present = " AND ".join(
        f"child.{column} IS NOT NULL" for column in child_columns
    )
    matching_columns = " AND ".join(
        f"parent.{parent_column} = child.{child_column}"
        for parent_column, child_column in zip(parent_columns, child_columns)
    )
    cursor.execute(
        f"""
        SELECT {', '.join(f'child.{column}' for column in child_columns)}
        FROM {table} AS child
        WHERE {all_child_columns_present}
          AND NOT EXISTS (
              SELECT 1 FROM {referenced_table} AS parent
              WHERE {matching_columns}
          )
        """
    )
    orphan_rows = cursor.fetchall()
    if orphan_rows:
        values = ", ".join(
            "(" + ", ".join(str(value) for value in row) + ")"
            for row in orphan_rows
        )
        raise RuntimeError(
            f"Cannot create {foreign_key.name} foreign key; "
            f"orphan key tuples: {values}"
        )

    cursor.execute(
        COMPOSITE_FOREIGN_KEY_EXISTS_SQL,
        (foreign_key.table, foreign_key.name),
    )
    if cursor.fetchone() is not None:
        return f"Checked {foreign_key.name} foreign key: already exists"

    cursor.execute(
        f"""
        ALTER TABLE {table}
        ADD CONSTRAINT {_quote_identifier(foreign_key.name)}
        FOREIGN KEY ({', '.join(child_columns)})
        REFERENCES {referenced_table} ({', '.join(parent_columns)})
        """
    )
    return f"Checked {foreign_key.name} foreign key: created"


def ensure_inferred_foreign_keys(cursor: Any) -> list[str]:
    """Ensure high-confidence references inferred from imported data exist."""
    messages = [ensure_stato_avanzamento_id_unique(cursor)]
    messages.extend(_clear_small_project_importance_orphans(cursor))
    messages.extend(_cleanup_small_project_area_orphans(cursor))
    messages.extend(
        _ensure_source_foreign_key(cursor, foreign_key)
        for foreign_key in INFERRED_FOREIGN_KEYS
    )
    messages.extend(
        _ensure_composite_foreign_key(cursor, foreign_key)
        for foreign_key in INFERRED_COMPOSITE_FOREIGN_KEYS
    )
    return messages


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


def ensure_project_foreign_keys(cursor: Any) -> list[str]:
    """Ensure tables with id_progetto reference the projects table."""
    cursor.execute(PROJECT_FOREIGN_KEY_TABLES_SQL)
    table_names = [row[0] for row in cursor.fetchall()]
    return [
        _ensure_source_foreign_key(
            cursor,
            ForeignKeyDefinition(
                f"{table}_id_progetto_fkey",
                table,
                "id_progetto",
                "progetti",
                "id",
            ),
        )
        for table in table_names
    ]


def ensure_operator_permission_foreign_key(cursor: Any) -> str:
    """Ensure operator permissions reference existing permissions."""
    return _ensure_source_foreign_key(
        cursor,
        ForeignKeyDefinition(
            "operatoripermessi_idpermesso_fkey",
            "operatoripermessi",
            "idpermesso",
            "permessi",
            "id",
        ),
    )


def ensure_project_macrophase_foreign_key(cursor: Any) -> str:
    """Ensure each phase belongs to a macro-phase in the same project."""
    cursor.execute(PROJECT_MACROPHASE_ORPHANS_SQL)
    orphan_pairs = cursor.fetchall()
    if orphan_pairs:
        values = ", ".join(
            f"({project_id}, {macro_phase_id})"
            for project_id, macro_phase_id in orphan_pairs
        )
        raise RuntimeError(
            "Cannot create project macro-phase foreign key; "
            f"orphan project/macro-phase pairs: {values}"
        )

    cursor.execute(PROJECT_MACROPHASE_FOREIGN_KEY_SQL)
    if cursor.fetchone() is not None:
        return "Checked project macro-phase foreign key: already exists"

    cursor.execute(ADD_PROJECT_MACROPHASE_FOREIGN_KEY_SQL)
    return "Checked project macro-phase foreign key: created"


def ensure_project_group_foreign_key(cursor: Any) -> list[str]:
    """Remove orphan project-group links, then ensure their foreign key."""
    cursor.execute(PROJECT_GROUP_ORPHANS_SQL)
    orphan_rows = cursor.fetchall()
    messages: list[str] = []
    if orphan_rows:
        orphan_ids = [row[0] for row in orphan_rows]
        details = ", ".join(
            f"id={row[0]} (project_id={row[1]}, group_id={row[2]})"
            for row in orphan_rows
        )
        messages.append(
            f"Found {len(orphan_rows)} orphan row(s) in progetti_gruppi: {details}"
        )
        cursor.execute(DELETE_PROJECT_GROUP_ORPHANS_SQL, (orphan_ids,))
        deleted_ids = [row[0] for row in cursor.fetchall()]
        if set(deleted_ids) != set(orphan_ids):
            raise RuntimeError(
                "Could not delete every orphan row from progetti_gruppi; "
                f"expected IDs {orphan_ids}, deleted IDs {deleted_ids}"
            )
        messages.append(
            f"Deleted {len(deleted_ids)} orphan row(s) from progetti_gruppi"
        )

    messages.append(
        _ensure_source_foreign_key(
            cursor,
            ForeignKeyDefinition(
                "progetti_gruppi_id_gruppo_fkey",
                "progetti_gruppi",
                "id_gruppo",
                "gruppi",
                "id",
            ),
        )
    )
    return messages


def ensure_project_division_foreign_key(cursor: Any) -> list[str]:
    """Delete a small number of orphan project-division links and add their FK."""
    cursor.execute(PROJECT_DIVISION_ORPHANS_SQL)
    orphan_rows = cursor.fetchall()
    messages: list[str] = []
    if orphan_rows:
        cursor.execute(PROJECT_DIVISION_ROW_COUNT_SQL)
        total_rows = cursor.fetchone()[0]
        orphan_count = len(orphan_rows)
        if orphan_count * 100 >= total_rows * 3:
            percentage = orphan_count / total_rows * 100 if total_rows else 100.0
            raise RuntimeError(
                "Cannot create progetti_divisioni foreign key; "
                f"{orphan_count}/{total_rows} rows are orphaned "
                f"({percentage:.2f}%), threshold is below 3%"
            )

        percentage = orphan_count / total_rows * 100
        division_ids = sorted({row[2] for row in orphan_rows})
        messages.append(
            f"Found {orphan_count} orphan row(s) in progetti_divisioni "
            f"({orphan_count}/{total_rows}, {percentage:.2f}%); "
            f"missing division IDs: {', '.join(map(str, division_ids))}"
        )
        orphan_ids = [row[0] for row in orphan_rows]
        cursor.execute(DELETE_PROJECT_DIVISION_ORPHANS_SQL, (orphan_ids,))
        deleted_ids = [row[0] for row in cursor.fetchall()]
        if set(deleted_ids) != set(orphan_ids):
            raise RuntimeError(
                "Could not delete every orphan row from progetti_divisioni; "
                f"expected IDs {orphan_ids}, deleted IDs {deleted_ids}"
            )
        messages.append(
            f"Deleted {len(deleted_ids)} orphan row(s) from progetti_divisioni"
        )

    messages.append(
        _ensure_source_foreign_key(
            cursor,
            ForeignKeyDefinition(
                "progetti_divisioni_id_divisione_fkey",
                "progetti_divisioni",
                "id_divisione",
                "divisioni",
                "id",
            ),
        )
    )
    return messages


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


def ensure_old_division_department_foreign_key(cursor: Any) -> str:
    """Ensure old divisions reference an existing department."""
    return _ensure_source_foreign_key(
        cursor,
        ForeignKeyDefinition(
            "divisioni_old_id_dipartimento_fkey",
            "divisioni_old",
            "id_dipartimento",
            "dipartimenti",
            "id",
        ),
    )


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
            messages.extend(ensure_project_foreign_keys(cursor))
            messages.extend(ensure_project_group_foreign_key(cursor))
            messages.extend(ensure_project_division_foreign_key(cursor))
            messages.append(ensure_project_macrophase_foreign_key(cursor))
            messages.append(ensure_division_department_foreign_key(cursor))
            messages.append(ensure_old_division_department_foreign_key(cursor))
            messages.append(ensure_referent_department_foreign_key(cursor))
            messages.append(ensure_referent_division_foreign_key(cursor))
            messages.append(ensure_referent_person_type_foreign_key(cursor))
            messages.extend(ensure_source_foreign_keys(cursor))
            messages.append(ensure_operator_permission_foreign_key(cursor))
            messages.extend(ensure_inferred_foreign_keys(cursor))
            return messages
