from pathlib import Path

import pytest
from ruamel.yaml import YAML
from typer.testing import CliRunner

from rimpack.main import app
from tests.helpers import copy_mods

runner = CliRunner()


@pytest.fixture
def populated_rimworld(rimworld_root_data: Path) -> Path:
    copy_mods(rimworld_root_data, "Core", "Royalty", "Ideology")
    return rimworld_root_data


def test_init_no_config_shows_friendly_error(
    tmp_path: Path, config_root: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert not isinstance(result.exception, FileNotFoundError)
    assert "Traceback" not in result.output
    assert "No RimPack config file found" in result.output
    assert str(config_root / "config.yml") in result.output
    assert "rimpack create-config" in result.output


@pytest.mark.usefixtures("populated_config")
@pytest.mark.usefixtures("populated_rimworld")
def test_init_creates_expected_module_files_in_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert (tmp_path / "modules" / "00_ludeon.yml").exists()
    assert (tmp_path / "modules" / "10_core.yml").exists()


@pytest.mark.usefixtures("populated_config")
@pytest.mark.usefixtures("populated_rimworld")
def test_init_creates_core_module_without_yaml_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert YAML().load(tmp_path / "modules" / "10_core.yml") is None


@pytest.mark.usefixtures("populated_config")
@pytest.mark.usefixtures("populated_rimworld")
def test_init_creates_core_correct_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rimworld_root_data: Path
):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    config_path = Path("pack.yml")
    ludeon_path = Path("modules/00_ludeon.yml")
    core_path = Path("modules/10_core.yml")
    yaml = YAML().load(config_path.read_text())
    assert [Path(module) for module in yaml["pack"]["modules"]] == [
        ludeon_path,
        core_path,
    ]
    assert ludeon_path.exists()
    yml = YAML().load(ludeon_path)
    assert yml.ca.comment[1][0].value == "# Core\r\n"
    assert yml == [
        {"pid": "Ludeon.RimWorld"},
        {"pid": "Ludeon.RimWorld.Royalty"},
        {"pid": "Ludeon.RimWorld.Ideology"},
    ]
