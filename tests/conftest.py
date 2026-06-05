from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import pytest
from pytest import MonkeyPatch

from rimpack.main import console


@pytest.fixture()
def fs_root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def config_root(fs_root: Path, monkeypatch: MonkeyPatch) -> Path:
    result = fs_root / "config"
    result.mkdir(exist_ok=True)
    monkeypatch.setattr("rimpack.main.get_default_config_dir", lambda: result)
    return result


@pytest.fixture
def rimworld_root(fs_root: Path, monkeypatch: MonkeyPatch) -> Path:
    result = fs_root / "rimworld"
    result.mkdir(exist_ok=True)
    monkeypatch.setattr(
        "rimpack.main.find_rimworld_root",
        lambda _: result,
    )
    return result


@pytest.fixture
def rimworld_root_data(rimworld_root: Path) -> Path:
    result = rimworld_root / "Data"
    result.mkdir(exist_ok=True)
    return result


@pytest.fixture
def rimworld_root_mods(rimworld_root: Path) -> Path:
    result = rimworld_root / "Mods"
    result.mkdir(exist_ok=True)
    return result


@pytest.fixture
def steam_root(fs_root: Path) -> Path:
    result = fs_root / "Steam"
    result.mkdir(exist_ok=True)
    return result


@pytest.fixture
def workshop_root(steam_root: Path, monkeypatch: MonkeyPatch) -> Path:
    result = steam_root / "Workshop"
    result.mkdir(exist_ok=True)
    monkeypatch.setattr(
        "rimpack.main.find_rimworld_workshop_path",
        lambda _: result,
    )
    return result


@pytest.fixture
def extra_mod_path(fs_root: Path) -> Path:
    result = fs_root / "extra-mods"
    result.mkdir(exist_ok=True)
    return result


@pytest.fixture
def populated_config(
    config_root: Path,
    rimworld_root: Path,
    workshop_root: Path,
    extra_mod_path: Path,
    monkeypatch: MonkeyPatch,
) -> Path:
    src = f"""
rimworld_root: {rimworld_root.as_posix()}
workshop_root: {workshop_root.as_posix()}
extra_mod_folders:
  - {extra_mod_path.as_posix()}
    """
    path = config_root / "config.yml"
    path.write_text(src)
    return path


@pytest.fixture
def core_mod_list_path(tmp_path: Path) -> Path:
    modules_path = tmp_path / "modules"
    modules_path.mkdir()
    (tmp_path / "pack.yml").write_text(
        """pack:
  modules:
    - modules/00_ludeon.yml
    - modules/10_core.yml
""",
        encoding="utf-8",
    )
    (modules_path / "00_ludeon.yml").write_text(
        "- pid: ludeon.rimworld\n",
        encoding="utf-8",
    )
    path = modules_path / "10_core.yml"
    path.write_text(
        """# This is a comment
  - pid: some.mod
""",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def factions_mod_list_path(tmp_path: Path) -> Path:
    modules_path = tmp_path / "modules"
    modules_path.mkdir()
    (tmp_path / "pack.yml").write_text(
        """pack:
  modules:
    - modules/10_core.yml
    - modules/20_factions.yml
""",
        encoding="utf-8",
    )
    (modules_path / "10_core.yml").write_text(
        "- pid: some.mod\n",
        encoding="utf-8",
    )
    path = modules_path / "20_factions.yml"
    path.write_text(
        """# This is a comment
- factions:
  - pid: some.faction.mod
""",
        encoding="utf-8",
    )
    return path


class ConflictingFactionsModListPaths(NamedTuple):
    first: Path
    second: Path


@pytest.fixture
def conflicting_factions_mod_list_paths(
    tmp_path: Path,
) -> ConflictingFactionsModListPaths:
    modules_path = tmp_path / "modules"
    modules_path.mkdir()
    (tmp_path / "pack.yml").write_text(
        """pack:
  modules:
    - modules/10_core.yml
    - modules/20_factions.yml
""",
        encoding="utf-8",
    )
    first = modules_path / "10_core.yml"
    first.write_text(
        """- factions:
  - pid: core.faction.mod
""",
        encoding="utf-8",
    )
    second = modules_path / "20_factions.yml"
    second.write_text(
        """- factions:
  - pid: extra.faction.mod
""",
        encoding="utf-8",
    )
    return ConflictingFactionsModListPaths(first, second)


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
