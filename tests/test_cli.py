from pathlib import Path

import pytest
from typer.testing import CliRunner

from rimpack.cli.main import app
from rimpack.core.config import Config
from rimpack.core.listfile import ListFile, PackageIdReference
from rimpack.core.packfile import PackConfig

runner = CliRunner()


def test_create_config_cli(config_path: Path, rimworld_root: Path, workshop_root: Path):
    result = runner.invoke(app, "create-config", input="y\n")
    assert result.exit_code == 0
    assert config_path.exists()
    config = Config.from_toml(config_path)
    assert config.rimworld_path == rimworld_root
    assert config.rimworld_workshop_path == workshop_root


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
        assert mod_file_suffix == ".list"
        mod_file_prefix = mod_file_path.stem
        digits_part, name_part = mod_file_prefix.split("_", 1)
        assert digits_part.isdigit()
        list_file = ListFile.from_path(mod_file_path)
        assert list_file.alias == name_part

    assert "lists/00_ludeon.list" in mod_files
    ludeon_list_path = Path("lists/00_ludeon.list")
    ludeon_list = ListFile.from_path(ludeon_list_path)
    ludeon_list_references = ludeon_list.references
    assert ludeon_list_references == (
        PackageIdReference("Ludeon.RimWorld"),
        PackageIdReference("Ludeon.RimWorld.Royalty"),
        PackageIdReference("Ludeon.RimWorld.Ideology"),
    )
