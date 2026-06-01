from pathlib import Path
from unittest.mock import ANY, Mock

import pytest
from ruamel.yaml import YAML
from typer.testing import CliRunner

from rimpack.main import app
from rimpack.config import Config
from rimpack.mod.about import AboutModMetadata
from rimpack.mod.modfolder import ModFolder

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
