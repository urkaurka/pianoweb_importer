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
