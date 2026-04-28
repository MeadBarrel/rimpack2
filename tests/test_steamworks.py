from pathlib import Path
import pytest

from rimpack.core.steamworks import (
    Steamworks,
    SteamworksError,
    resolve_rimworld_workshop_mod_by_id,
)
from concurrent.futures import ThreadPoolExecutor


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


def test_resolve_rimworld_workshop_mod_by_id(workshop_root: Path):
    class FakeSteamworks:
        def subscribe(self, workshop_id: int) -> bool:
            assert workshop_id == 1000
            path = workshop_root / "1000" / "About" / "About.xml"
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(about_xml)
            return True

    steamworks = FakeSteamworks()
    result = resolve_rimworld_workshop_mod_by_id(steamworks, workshop_root, 1000)
    assert result
    assert result.path.is_dir()


def test_resolve_rimworld_workshop_mod_by_id_subscribe_failed(
    workshop_root: Path, monkeypatch: pytest.MonkeyPatch
):
    class FakeSteamworks:
        def subscribe(self, workshop_id: int):
            return

    monkeypatch.setattr(
        "rimpack.core.steamworks._wait_for_workshop_mod", lambda *_: None
    )

    steamworks = FakeSteamworks()
    with pytest.raises(SteamworksError):
        _ = resolve_rimworld_workshop_mod_by_id(steamworks, workshop_root, 1000)


def test_resolve_rimworld_workshop_mod_by_id_unsubscribe(workshop_root: Path):
    unsubscribed = False

    class FakeSteamworks:
        def subscribe(self, workshop_id: int):
            assert workshop_id == 1000
            path = workshop_root / "1000" / "About" / "About.xml"
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(about_xml)

        def unsubscribe(self, workshop_id: int):
            nonlocal unsubscribed
            unsubscribed = True

    steamworks = FakeSteamworks()
    result = resolve_rimworld_workshop_mod_by_id(
        steamworks, workshop_root, 1000, unsubscribe=True
    )
    assert result
    assert unsubscribed


def test_resolve_rimworld_workshop_mod_by_id_unsubscribe_preexisted(
    workshop_root: Path,
):
    unsubscribed = False

    class FakeSteamworks:
        def subscribe(self, workshop_id: int):
            assert workshop_id == 1000
            path = workshop_root / "1000" / "About" / "About.xml"
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(about_xml)

        def unsubscribe(self, workshop_id: int):
            nonlocal unsubscribed
            unsubscribed = True

    steamworks = FakeSteamworks()
    steamworks.subscribe(1000)
    result = resolve_rimworld_workshop_mod_by_id(
        steamworks, workshop_root, 1000, unsubscribe=True
    )
    assert result
    assert not unsubscribed
