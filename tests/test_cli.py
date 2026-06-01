from pathlib import Path
from unittest.mock import ANY, Mock

import pytest
from ruamel.yaml import YAML
from typer.testing import CliRunner

from rimpack.main import app
from rimpack.config import Config
from rimpack.listfile import ModList, ModListPacks, ModListRecordPid
from rimpack.mod.about import AboutModMetadata
from rimpack.mod.modfolder import ModFolder
from tests.helpers import copy_mods

runner = CliRunner()


def _test_create_config_cli(
    config_path: Path, rimworld_root: Path, workshop_root: Path
):
    result = runner.invoke(app, "create-config", input="y\n")
    assert result.exit_code == 0
    assert config_path.exists()
    config = Config.from_toml(config_path)
    assert config.rimworld_path == rimworld_root
    assert config.rimworld_workshop_path == workshop_root


@pytest.fixture
def fake_mod(tmp_path: Path):
    return ModFolder(
        tmp_path,
        AboutModMetadata(
            package_id="my.mod",
            name="My Mod",
            authors=("me",),
            description="my mod",
            supported_versions=("1.6",),
        ),
    )


@pytest.fixture
def fake_resolve(fake_mod: ModFolder, monkeypatch):
    mock = Mock(return_value=fake_mod)
    monkeypatch.setattr("rimpack.main.Steamworks", Mock())
    monkeypatch.setattr("rimpack.main.resolve_rimworld_workshop_mod_by_id", mock)
    return (mock, fake_mod)


@pytest.mark.usefixtures("populated_config")
def _test_resolve_steam_id(fake_resolve: tuple[Mock, ModFolder], workshop_root: Path):
    mock, mod = fake_resolve
    result = runner.invoke(app, ["resolve", "1000"])
    assert result.exit_code == 0
    mock.assert_called_with(ANY, workshop_root, 1000, unsubscribe=False)
    assert mod.about.package_id in result.output
    assert mod.about.name in result.output
    assert mod.about.description in result.output
    assert "1.6" in result.output
    assert str(mod.path)[:15] in result.output


@pytest.fixture
def populated_rimworld(rimworld_root_data: Path) -> Path:
    copy_mods(rimworld_root_data, "Core", "Royalty", "Ideology")
    return rimworld_root_data


def test_create_config_exists(populated_config: Path):
    mtime = populated_config.stat().st_mtime
    runner.invoke(app, ["create-config"])
    assert mtime == populated_config.stat().st_mtime


def test_create_config(config_root: Path, rimworld_root: Path, workshop_root: Path):
    runner.invoke(app, ["create-config"], input="\n\n")
    path = config_root / "config.yml"
    yml = YAML().load(path)
    assert yml == {
        "rimworld_root": rimworld_root.as_posix(),
        "workshop_root": workshop_root.as_posix(),
    }


def test_init_no_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert isinstance(result.exception, FileNotFoundError)


def test_init_no_config_shows_friendly_error(
    tmp_path: Path, config_root: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert not isinstance(result.exception, FileNotFoundError)
    assert "Traceback" not in result.output
    assert "config.yml" in result.output
    assert str(config_root / "config.yml") in result.output


@pytest.mark.usefixtures("populated_config")
@pytest.mark.usefixtures("populated_rimworld")
def test_init_creates_core_correct_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rimworld_root_data: Path
):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    config_path = Path("pack.yml")
    core_path = Path("modules/00_core.yml")
    yaml = YAML().load(config_path.read_text())
    assert Path(yaml["pack"]["modules"][0]) == core_path
    assert core_path.exists()
    yml = YAML().load(core_path)
    assert yml.ca.comment[1][0].value == "# Core\r\n"
    assert yml == [
        {"pid": "Ludeon.RimWorld"},
        {"pid": "Ludeon.RimWorld.Royalty"},
        {"pid": "Ludeon.RimWorld.Ideology"},
    ]
