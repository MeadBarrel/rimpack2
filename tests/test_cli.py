from pathlib import Path
from unittest.mock import ANY, Mock

import pytest
from typer.testing import CliRunner

from rimpack.cli.main import app
from rimpack.core.config import Config
from rimpack.core.listfile import ModList, ModListPacks, ModListRecord, ModListRecordPid
from rimpack.core.mod.about import AboutModMetadata
from rimpack.core.mod.modfolder import ModFolder
from rimpack.core.packfile import PackConfig

runner = CliRunner()


def test_create_config_cli(config_path: Path, rimworld_root: Path, workshop_root: Path):
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
    monkeypatch.setattr("rimpack.cli.main.Steamworks", Mock())
    monkeypatch.setattr("rimpack.cli.main.resolve_rimworld_workshop_mod_by_id", mock)
    return (mock, fake_mod)


@pytest.mark.usefixtures("populated_config")
def test_resolve_steam_id(fake_resolve: tuple[Mock, ModFolder], workshop_root: Path):
    mock, mod = fake_resolve
    result = runner.invoke(app, ["resolve", "1000"])
    assert result.exit_code == 0
    mock.assert_called_with(ANY, workshop_root, 1000, unsubscribe=False)
    assert mod.about.package_id in result.output
    assert mod.about.name in result.output
    assert mod.about.description in result.output
    assert "1.6" in result.output
    assert str(mod.path)[:15] in result.output


@pytest.mark.usefixtures("populated_config")
def test_resolve_steam_id_unsubscribe(
    fake_resolve: tuple[Mock, ModFolder], workshop_root: Path
):
    mock, mod = fake_resolve
    result = runner.invoke(app, ["resolve", "1000", "--unsubscribe"])
    assert result.exit_code == 0
    mock.assert_called_with(ANY, workshop_root, 1000, unsubscribe=True)
    assert mod.about.package_id in result.output


@pytest.mark.usefixtures("populated_config")
@pytest.mark.usefixtures("rimworld_core_mod")
@pytest.mark.usefixtures("rimworld_royalty_mod")
@pytest.mark.usefixtures("rimworld_ideology_mod")
def test_init(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    config_path = Path("pack.toml")
    assert config_path.exists()
    config = PackConfig.from_toml(config_path)
    assert config.name
    assert config.rimworld_version == "1.6"
    mod_files = config.mod_files
    assert mod_files
    for mod_file in mod_files:
        mod_file_path = Path(mod_file)
        assert mod_file_path.exists()
        mod_file_suffix = mod_file_path.suffix
        assert mod_file_suffix == ".yml"
        mod_file_prefix = mod_file_path.stem
        digits_part, _ = mod_file_prefix.split("_", 1)
        assert digits_part.isdigit()

    assert "lists/00_ludeon.yml" in mod_files
    ludeon_list_path = Path("lists/00_ludeon.yml")
    ludeon_list = ModList.load(ludeon_list_path)
    expected: ModListPacks = {
        "ludeon": (
            ModListRecordPid(pid="Ludeon.RimWorld"),
            ModListRecordPid(pid="Ludeon.RimWorld.Royalty"),
            ModListRecordPid(pid="Ludeon.RimWorld.Ideology"),
        )
    }
    assert ludeon_list.data == expected
