from pathlib import Path


def test_import_uses_sqlserver_ensure_script_without_removing_container() -> None:
    makefile = Path("Makefile").read_text()
    import_recipe = makefile.split("import:\n", maxsplit=1)[1]

    assert "ut_ensure_sqlserver.py" in import_recipe
    assert "docker rm -f" not in import_recipe
    assert "docker volume rm" not in import_recipe


def test_import_removes_temporary_schema_by_default_and_can_keep_it() -> None:
    makefile = Path("Makefile").read_text()

    assert "KEEP_TMP ?= 0" in makefile
    assert "--keep-tmp" in makefile


def test_import_runs_post_import_operations_in_importer() -> None:
    makefile = Path("Makefile").read_text()

    assert ".PHONY: help import post_import" in makefile
    assert "post_import:" in makefile
    assert "$(MAKE) post_import" in makefile


def test_help_documents_post_import_target() -> None:
    makefile = Path("Makefile").read_text()

    help_recipe = makefile.split("help:\n", maxsplit=1)[1].split("\n\n", maxsplit=1)[0]
    assert '@echo "  make post_import"' in help_recipe
