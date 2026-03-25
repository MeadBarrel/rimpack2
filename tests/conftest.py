from pathlib import Path
import pytest

from rimpack.core.config import Config
from rimpack.core import config


@pytest.fixture()
def config_path(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    return config_path


@pytest.fixture(autouse=True)
def fake_config_path(config_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    monkeypatch.setattr(config, "find_rimworld_root", lambda: rimworld_root)


@pytest.fixture(autouse=True)
def fake_steam_workshop_root(workshop_root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "find_rimworld_workshop_path", lambda: workshop_root)
