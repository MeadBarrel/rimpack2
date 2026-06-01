from pathlib import Path

import tomlkit

from rimpack.config import Config
from pytest import MonkeyPatch


def test_rimworld_path_property():
    source = r"""
    rimworld_path = "c:/rimworld"
    """
    path = Path(r"c:/rimworld")
    toml = tomlkit.parse(source)
    config = Config(toml)
    assert config.rimworld_path == path


def test_rimworld_workshop_path_property():
    source = """
    rimworld_workshop_path = "c:/workshop"
    """
    path = Path(r"c:/workshop")
    toml = tomlkit.parse(source)
    config = Config(toml)
    assert config.rimworld_workshop_path == path


def test_rimworld_path_property_from_env(monkeypatch: MonkeyPatch):
    path = Path(r"c:\rimworld")
    toml = tomlkit.TOMLDocument()
    path = "c:/rimworld"
    monkeypatch.setenv("RIMWORLD_PATH", path)
    config = Config(toml)
    assert config.rimworld_path == Path(path)


def test_workshop_path_property_from_env(monkeypatch: MonkeyPatch):
    path = "c:/rimworld"
    toml = tomlkit.TOMLDocument()
    monkeypatch.setenv("RIMWORLD_WORKSHOP_PATH", path)
    config = Config(toml)
    assert config.rimworld_workshop_path == Path(path)


def test_from_toml_str():
    source = """
    rimworld_path="c:/rimworld_path"
    rimworld_workshop_path="c:/rimworld_workshop_path"
    """
    result = Config.from_toml_str(source)
    assert result.rimworld_path == Path("c:/rimworld_path")
    assert result.rimworld_workshop_path == Path("c:/rimworld_workshop_path")


def test_from_toml(tmp_path: Path):
    source = """
    rimworld_path="c:/rimworld_path"
    rimworld_workshop_path="c:/rimworld_workshop_path"
    """
    path = tmp_path / "config.toml"
    _ = path.write_text(source)
    result = Config.from_toml(path)
    assert result.rimworld_path == Path(r"c:/rimworld_path")
    assert result.rimworld_workshop_path == Path(r"c:/rimworld_workshop_path")


def test_with_rimworld_path_fromempty():
    config = Config(tomlkit.TOMLDocument())
    path = Path("c:/rimworld")
    new_config = config.with_rimworld_path(path)
    assert new_config.rimworld_path == path


def test_with_rimworld_path():
    before_path = Path("c:/rimworld")
    config = Config(tomlkit.TOMLDocument()).with_rimworld_path(before_path)
    path = Path("c:/rimworld_after")
    new_config = config.with_rimworld_path(path)
    assert new_config.rimworld_path == path


def test_with_rimworld_workshop_path_fromempty():
    config = Config(tomlkit.TOMLDocument())
    path = Path("c:/workshop")
    new_config = config.with_rimworld_workshop_path(path)
    assert new_config.rimworld_workshop_path == path


def test_with_rimworld_workshop_path():
    before_path = Path("c:/workshop")
    config = Config(tomlkit.TOMLDocument()).with_rimworld_workshop_path(before_path)
    path = Path("c:/workshop_after")
    new_config = config.with_rimworld_workshop_path(path)
    assert new_config.rimworld_workshop_path == path


def test_save(rimworld_root: Path, fake_config_path: Path):
    config = Config(tomlkit.TOMLDocument()).with_rimworld_path(rimworld_root)
    config.save(fake_config_path)
    new_config = Config.from_toml(fake_config_path)
    assert new_config.rimworld_path == rimworld_root
