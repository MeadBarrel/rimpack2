from pathlib import Path

import pytest
from typer.testing import CliRunner

from rimpack.main import app
from tests.helpers import assert_yaml_text_equal, copy_mods, copy_workshop_mods

runner = CliRunner()


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
    copy_workshop_mods(workshop_root, 725219116)

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
    copy_mods(rimworld_root_mods, "FluffysWorktab")

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
    copy_mods(extra_mod_path, "FluffysWorktab")

    _assert_add_appends_pid_mod_name_comment(core_mod_list_path, use_pid_flag)


@pytest.mark.usefixtures("populated_config")
@pytest.mark.parametrize("use_wid_flag", [True, False])
def test_add_workshop_id_from_steam_workshop_appends_mod_name_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    core_mod_list_path: Path,
    workshop_root: Path,
    use_wid_flag: bool,
):
    monkeypatch.chdir(tmp_path)
    copy_workshop_mods(workshop_root, 724602224)

    _assert_add_appends_wid_mod_name_comment(core_mod_list_path, use_wid_flag)


@pytest.mark.usefixtures("populated_config")
@pytest.mark.parametrize("use_loc_flag", [True, False])
def test_add_loc_from_rimworld_local_mods_appends_mod_name_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    core_mod_list_path: Path,
    rimworld_root_mods: Path,
    use_loc_flag: bool,
):
    monkeypatch.chdir(tmp_path)
    copy_mods(rimworld_root_mods, "FluffysWorktab")
    _assert_loc_mod_folder_exists(rimworld_root_mods, "FluffysWorktab")

    _assert_add_appends_loc_mod_name_comment(core_mod_list_path, use_loc_flag)


@pytest.mark.usefixtures("populated_config")
@pytest.mark.parametrize("use_loc_flag", [True, False])
def test_add_loc_from_extra_mod_path_appends_mod_name_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    core_mod_list_path: Path,
    extra_mod_path: Path,
    use_loc_flag: bool,
):
    monkeypatch.chdir(tmp_path)
    copy_mods(extra_mod_path, "FluffysWorktab")
    _assert_loc_mod_folder_exists(extra_mod_path, "FluffysWorktab")

    _assert_add_appends_loc_mod_name_comment(core_mod_list_path, use_loc_flag)


@pytest.mark.usefixtures("populated_config")
@pytest.mark.parametrize("use_pid_flag", [True, False])
def test_add_pid_appends_to_subsection_found_across_mod_lists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    factions_mod_list_path: Path,
    rimworld_root_mods: Path,
    use_pid_flag: bool,
):
    monkeypatch.chdir(tmp_path)
    copy_mods(rimworld_root_mods, "FluffysWorktab")

    _assert_add_appends_pid_to_factions_subsection(
        factions_mod_list_path, use_pid_flag
    )


@pytest.mark.usefixtures("populated_config")
def test_add_pid_to_duplicate_subsection_reports_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    conflicting_factions_mod_list_paths: tuple[Path, Path],
    rimworld_root_mods: Path,
):
    monkeypatch.chdir(tmp_path)
    copy_mods(rimworld_root_mods, "FluffysWorktab")
    first_before = conflicting_factions_mod_list_paths[0].read_text(encoding="utf-8")
    second_before = conflicting_factions_mod_list_paths[1].read_text(encoding="utf-8")

    result = runner.invoke(
        app, ["add", "factions", "--pid", "Fluffy.WorkTab"]
    )

    assert result.exit_code == 1
    assert "factions" in result.output
    assert "defined multiple times" in result.output
    assert conflicting_factions_mod_list_paths[0].read_text(
        encoding="utf-8"
    ) == first_before
    assert conflicting_factions_mod_list_paths[1].read_text(
        encoding="utf-8"
    ) == second_before


def _assert_add_appends_pid_mod_name_comment(
    core_mod_list_path: Path, use_pid_flag: bool
) -> None:
    args = (
        ["core", "--pid", "Fluffy.WorkTab"]
        if use_pid_flag
        else ["core", "Fluffy.WorkTab"]
    )
    result = runner.invoke(app, ["add", *args])

    assert result.exit_code == 0
    assert_yaml_text_equal(
        core_mod_list_path.read_text(encoding="utf-8"),
        """# This is a comment
  - pid: some.mod
  - pid: Fluffy.WorkTab  # Work Tab
""",
    )


def _assert_add_appends_pid_to_factions_subsection(
    factions_mod_list_path: Path, use_pid_flag: bool
) -> None:
    args = (
        ["factions", "--pid", "Fluffy.WorkTab"]
        if use_pid_flag
        else ["factions", "Fluffy.WorkTab"]
    )
    result = runner.invoke(app, ["add", *args])

    assert result.exit_code == 0
    assert_yaml_text_equal(
        factions_mod_list_path.read_text(encoding="utf-8"),
        """# This is a comment
- factions:
  - pid: some.faction.mod
  - pid: Fluffy.WorkTab  # Work Tab
""",
    )


def _assert_add_appends_loc_mod_name_comment(
    core_mod_list_path: Path, use_loc_flag: bool
) -> None:
    args = (
        ["core", "--loc", "FluffysWorktab"]
        if use_loc_flag
        else ["core", "FluffysWorktab"]
    )
    result = runner.invoke(app, ["add", *args])

    assert result.exit_code == 0
    assert_yaml_text_equal(
        core_mod_list_path.read_text(encoding="utf-8"),
        """# This is a comment
  - pid: some.mod
  - loc: FluffysWorktab  # Work Tab
""",
    )


def _assert_loc_mod_folder_exists(root: Path, loc: str) -> None:
    assert (root / loc / "About" / "About.xml").exists()


def _assert_add_appends_wid_mod_name_comment(
    core_mod_list_path: Path, use_wid_flag: bool
) -> None:
    args = (
        ["core", "--wid", "724602224"]
        if use_wid_flag
        else ["core", "724602224"]
    )
    result = runner.invoke(app, ["add", *args])

    assert result.exit_code == 0
    assert_yaml_text_equal(
        core_mod_list_path.read_text(encoding="utf-8"),
        """# This is a comment
  - pid: some.mod
  - wid: 724602224  # Misc. Robots
""",
    )
