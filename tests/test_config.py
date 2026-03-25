from pathlib import Path
import platform

import tomlkit

from rimpack.core.config import RimworldConfig, Config
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


def test_rimworld_path_property_from_env_no_config(monkeypatch: MonkeyPatch):
    path = "c:/rimworld"
    monkeypatch.setenv("RIMWORLD_PATH", path)
    config = Config()
    assert config.rimworld_path == Path(path)


def test_workshop_path_property_from_env(monkeypatch: MonkeyPatch):
    path = "c:/rimworld"
    toml = tomlkit.TOMLDocument()
    monkeypatch.setenv("RIMWORLD_WORKSHOP_PATH", path)
    config = Config(toml)
    assert config.rimworld_workshop_path == Path(path)


def test_workshop_path_property_from_env_no_config(monkeypatch: MonkeyPatch):
    path = "c:/rimworld"
    monkeypatch.setenv("RIMWORLD_WORKSHOP_PATH", path)
    config = Config()
    assert config.rimworld_workshop_path == Path(path)


def test_get_default_config_path():
    if platform.system() != "Windows":
        raise RuntimeError("Currently only windows is supported")
    expected = Path.resolve(Path("~/AppData/Local/rimpack/config.toml"))
    result = Config.get_default_config_path()
    assert result == expected


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


def test_from_toml_default(tmp_path: Path, monkeypatch: MonkeyPatch):
    source = """
    rimworld_path="c:/rimworld_path"
    rimworld_workshop_path="c:/rimworld_workshop_path"
    """
    path = tmp_path / "config.toml"
    monkeypatch.setattr(Config, "get_default_config_path", staticmethod(lambda: path))
    _ = path.write_text(source)
    result = Config.from_toml()
    assert result.rimworld_path == Path("c:/rimworld_path")
    assert result.rimworld_workshop_path == Path("c:/rimworld_workshop_path")
