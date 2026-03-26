from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from rimpack.cli.main import console
from rimpack.core.config import Config


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
        "rimpack.core.config._find_rimworld_root",
        lambda _: rimworld_root,  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    )


@pytest.fixture(autouse=True)
def fake_steam_workshop_root(workshop_root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "rimpack.core.config._find_rimworld_workshop_path",
        lambda _: workshop_root,  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
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
    rimworld_path="{rimworld_root.as_posix()}"
    rimworld_workshop_path="{workshop_root.as_posix()}"
    """
    return Config.from_toml_str(source)


@pytest.fixture
def populated_config(rimpack_config: Config, config_path: Path):
    rimpack_config.save(config_path)


@pytest.fixture
def rimworld_root_data(rimworld_root: Path) -> Path:
    result = rimworld_root / "Data"
    result.mkdir(parents=True, exist_ok=True)
    return result


@pytest.fixture
def rimworld_core_mod(rimworld_root_data: Path):
    about_path = rimworld_root_data / "Core" / "About" / "About.xml"
    about_path.parent.mkdir(parents=True, exist_ok=True)
    about_xml = """\
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <packageId>Ludeon.RimWorld</packageId>
  <author>Ludeon Studios</author>
  <forceLoadBefore>
    <li>Ludeon.RimWorld.Ideology</li>
    <li>Ludeon.RimWorld.Royalty</li>
  </forceLoadBefore>
</ModMetaData>
    """
    pass
    _ = about_path.write_text(about_xml)


@pytest.fixture
def rimworld_royalty_mod(rimworld_root_data: Path):
    about_path = rimworld_root_data / "Royalty" / "About" / "About.xml"
    about_path.parent.mkdir(parents=True, exist_ok=True)
    about_xml = """\
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <packageId>Ludeon.RimWorld.Royalty</packageId>
  <author>Ludeon Studios</author>
  <steamAppId>1149640</steamAppId>
  <supportedVersions>
  	<li>1.6</li>
  </supportedVersions>
  <forceLoadAfter>
    <li>Ludeon.RimWorld</li>
  </forceLoadAfter>
  <forceLoadBefore>
    <li>Ludeon.RimWorld.Ideology</li>
    <li>Ludeon.RimWorld.Biotech</li>
    <li>Ludeon.RimWorld.Anomaly</li>
    <li>Ludeon.RimWorld.Odyssey</li>
  </forceLoadBefore>
</ModMetaData>
    """
    pass
    _ = about_path.write_text(about_xml)


@pytest.fixture
def rimworld_ideology_mod(rimworld_root_data: Path):
    about_path = rimworld_root_data / "Ideology" / "About" / "About.xml"
    about_path.parent.mkdir(parents=True, exist_ok=True)
    about_xml = """\
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>\
  <packageId>Ludeon.RimWorld.Ideology</packageId>
  <author>Ludeon Studios</author>
  <steamAppId>1392840</steamAppId>
  <supportedVersions>
  	<li>1.6</li>
  </supportedVersions>
  <forceLoadAfter>
    <li>Ludeon.RimWorld</li>
    <li>Ludeon.RimWorld.Royalty</li>
  </forceLoadAfter>
  <forceLoadBefore>
    <li>Ludeon.RimWorld.Biotech</li>
    <li>Ludeon.RimWorld.Anomaly</li>
    <li>Ludeon.RimWorld.Odyssey</li>
  </forceLoadBefore>
</ModMetaData>
    """
    pass
    _ = about_path.write_text(about_xml)
