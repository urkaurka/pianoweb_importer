SHELL := /bin/bash

PYTHON ?= .venv/bin/python
SQLSERVER_CONTAINER ?= pianoweb-sqlserver
SQLSERVER_IMAGE ?= mcr.microsoft.com/mssql/server:2022-latest
SQLSERVER_VOLUME ?= pianoweb_sqlserver_data
SQLSERVER_BACKUP_PATH ?= /var/opt/mssql/backup/pianoweb_import.bak
MSSQL_DATABASE ?= pianoweb_source
KEEP_TMP ?= 0

.PHONY: help import post_import

help:
	@echo "Available targets:"
	@echo "  make help"
	@echo "      Show this help."
	@echo "  make import FILE=path/to/backup.bak"
	@echo "      Start the SQL Server container when needed, then restore the SQL Server database and import into PostgreSQL."
	@echo "      WARNING: this operation is destructive."
	@echo "  make post_import"
	@echo "      Apply PostgreSQL operations required after the import."
	@echo ""
	@echo "Optional variables:"
	@echo "  SQLSERVER_CONTAINER=pianoweb-sqlserver"
	@echo "  SQLSERVER_IMAGE=mcr.microsoft.com/mssql/server:2022-latest"
	@echo "  SQLSERVER_VOLUME=pianoweb_sqlserver_data"
	@echo "  MSSQL_DATABASE=pianoweb_source"
	@echo "  SQLSERVER_BACKUP_PATH=/var/opt/mssql/backup/pianoweb_import.bak"
	@echo "  KEEP_TMP=1"
	@echo "      Keep the temporary PostgreSQL schema for inspection after import."

post_import:
	$(PYTHON) ut_post_import.py

import:
	@test -n "$(FILE)" || (echo "Usage: make import FILE=/absolute/or/relative/path/to/file.bak"; exit 2)
	@test -f "$(FILE)" || (echo "Backup file not found: $(FILE)"; exit 2)
	$(PYTHON) ut_ensure_sqlserver.py --container "$(SQLSERVER_CONTAINER)" --image "$(SQLSERVER_IMAGE)" --volume "$(SQLSERVER_VOLUME)"
	@docker exec "$(SQLSERVER_CONTAINER)" mkdir -p "$$(dirname "$(SQLSERVER_BACKUP_PATH)")"
	@docker cp "$(FILE)" "$(SQLSERVER_CONTAINER):$(SQLSERVER_BACKUP_PATH)"
	$(PYTHON) ut_restore_backup.py --backup-path "$(SQLSERVER_BACKUP_PATH)" --database "$(MSSQL_DATABASE)"
	$(PYTHON) ut_inspect_source.py
	$(PYTHON) ut_reset_postgres.py
	$(PYTHON) ut_migrate_database.py --apply $(if $(filter 1 true yes,$(KEEP_TMP)),--keep-tmp,)
	$(MAKE) post_import
