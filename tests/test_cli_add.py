from pathlib import Path

import pytest
from typer.testing import CliRunner

from rimpack.main import app
from tests.helpers import assert_yaml_text_equal

runner = CliRunner()


def _write_about_xml(mod_root: Path, *, package_id: str, name: str) -> None:
    about_path = mod_root / "About" / "About.xml"
    about_path.parent.mkdir(parents=True)
    about_path.write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>{name}</name>
  <packageId>{package_id}</packageId>
</ModMetaData>
""",
        encoding="utf-8",
    )


@pytest.mark.usefixtures("populated_config")
@pytest.mark.parametrize("use_pid_flag", [True, False])
def test_add_pid_from_steam_workshop_appends_mod_name_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    core_mod_list_path: Path,
    workshop_root: Path,
    use_pid_flag: bool,
):
    monkeypatch.chdir(tmp_path)
    _write_about_xml(
        workshop_root / "123456789",
        package_id="my.package",
        name="My Package",
    )

    _assert_add_appends_pid_mod_name_comment(core_mod_list_path, use_pid_flag)


@pytest.mark.usefixtures("populated_config")
@pytest.mark.parametrize("use_pid_flag", [True, False])
def test_add_pid_from_rimworld_local_mods_appends_mod_name_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    core_mod_list_path: Path,
    rimworld_root_mods: Path,
    use_pid_flag: bool,
):
    monkeypatch.chdir(tmp_path)
    _write_about_xml(
        rimworld_root_mods / "MyMod",
        package_id="my.package",
        name="My Package",
    )

    _assert_add_appends_pid_mod_name_comment(core_mod_list_path, use_pid_flag)


@pytest.mark.usefixtures("populated_config")
@pytest.mark.parametrize("use_pid_flag", [True, False])
def test_add_pid_from_extra_mod_path_appends_mod_name_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    core_mod_list_path: Path,
    extra_mod_path: Path,
    use_pid_flag: bool,
):
    monkeypatch.chdir(tmp_path)
    _write_about_xml(
        extra_mod_path / "MyExtraMod",
        package_id="my.package",
        name="My Package",
    )

    _assert_add_appends_pid_mod_name_comment(core_mod_list_path, use_pid_flag)


def _assert_add_appends_pid_mod_name_comment(
    core_mod_list_path: Path, use_pid_flag: bool
) -> None:
    args = (
        ["core", "--pid", "my.package"]
        if use_pid_flag
        else ["core", "my.package"]
    )
    result = runner.invoke(app, ["add", *args])

    assert result.exit_code == 0
    assert_yaml_text_equal(
        core_mod_list_path.read_text(encoding="utf-8"),
        "# This is a comment\n"
        "  - pid: some.mod\n"
        "  - pid: my.package  # My Package\n",
    )
