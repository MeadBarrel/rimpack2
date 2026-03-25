from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import pytest
from pytest import MonkeyPatch
from tomlkit import TOMLDocument
import tomlkit

from rimpack.core.config import Config
from rimpack.cli.main import console


@pytest.fixture()
def config_path(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    return config_path


@pytest.fixture(autouse=True)
def fake_config_path(config_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(
        Config, "get_default_config_path", staticmethod(lambda: config_path)
    )
    return config_path


@pytest.fixture
def rimworld_root(tmp_path: Path) -> Path:
    return tmp_path / "rimworld"


@pytest.fixture
def workshop_root(tmp_path: Path) -> Path:
    return tmp_path / "Workshop"


@pytest.fixture(autouse=True)
def fake_rimworld_path(rimworld_root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "rimpack.core.config._find_rimworld_root", lambda: rimworld_root
    )


@pytest.fixture(autouse=True)
def fake_steam_workshop_root(workshop_root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "rimpack.core.config._find_rimworld_workshop_path", lambda: workshop_root
    )


@dataclass
class FakeConsoleStatus:
    statuses: list[str]

    @contextmanager
    def __call__(self, value: str, **_):
        self.statuses.append(value)
        yield


@pytest.fixture(autouse=True)
def fake_console_status(monkeypatch: MonkeyPatch):
    result = FakeConsoleStatus([])
    monkeypatch.setattr(console, "status", result)
    return result


@pytest.fixture
def rimpack_config(rimworld_root: Path, workshop_root: Path) -> Config:
    source = f"""
    rimworld_path={rimworld_root.as_posix()},
    rimworld_workshop_path={workshop_root.as_posix()}
    """
    return Config.from_toml_str(source)
