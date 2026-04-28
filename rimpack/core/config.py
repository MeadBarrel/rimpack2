from copy import deepcopy
from dataclasses import dataclass, replace
from functools import cache
import os
from pathlib import Path
import platformdirs
from typing import Self
import re
import winreg
import tomlkit

from rimpack.constants import RIMWORLD_STEAM_APP_ID
from rimpack.core.exceptions import RimworldConfigParseError as RimworldConfigParseError


@dataclass(frozen=True)
class RimworldConfig:
    rimworld_path: Path | None = None
    rimworld_workshop_path: Path | None = None


@dataclass(frozen=True)
class Config:
    file_config: tomlkit.TOMLDocument

    @staticmethod
    def get_default_config_path() -> Path:
        user_config_dir = platformdirs.user_config_dir()
        return Path(user_config_dir) / "rimpack" / "config.toml"

    @classmethod
    def from_toml(cls, path: Path) -> Self:
        path = path or cls.get_default_config_path()
        source = path.read_text()
        return cls.from_toml_str(source)

    @classmethod
    def from_toml_str(cls, source: str) -> Self:
        doc = tomlkit.parse(source)
        return cls(doc)

    def save(self, path: Path):
        _ = path.write_text(tomlkit.dumps(self.file_config))  # pyright: ignore[reportUnknownMemberType]

    def with_rimworld_path(self, path: Path) -> Self:
        file_config = deepcopy(self.file_config)
        if "rimworld_path" not in file_config:
            _ = file_config.add("rimworld_path", path.as_posix())  # pyright: ignore[reportArgumentType]
        else:
            file_config["rimworld_path"] = path.as_posix()
        return replace(self, file_config=file_config)

    def with_rimworld_workshop_path(self, path: Path) -> Self:
        file_config = deepcopy(self.file_config)
        if "rimworld_workshop_path" not in file_config:
            _ = file_config.add("rimworld_workshop_path", path.as_posix())  # pyright: ignore[reportArgumentType]
        else:
            file_config["rimworld_workshop_path"] = path.as_posix()
        return replace(self, file_config=file_config)

    @property
    def rimworld_path(self) -> Path | None:
        if "rimworld_path" not in self.file_config:
            if path := os.getenv("RIMWORLD_PATH"):
                return Path(path)
            return None

        config_path = self.file_config["rimworld_path"]
        if not isinstance(config_path, str):
            raise RimworldConfigParseError("Incorrect value type for rimworld_path")
        return Path(config_path)

    @property
    def rimworld_workshop_path(self) -> Path | None:
        if "rimworld_workshop_path" not in self.file_config:
            if path := os.getenv("RIMWORLD_WORKSHOP_PATH"):
                return Path(path)
            return None

        config_path = self.file_config["rimworld_workshop_path"]
        if not isinstance(config_path, str):
            raise RimworldConfigParseError(
                "Incorrect value type for rimworld_workshop_path"
            )
        return Path(config_path)


def find_steam_root() -> Path | None:
    subkeys = [
        r"SOFTWARE\WOW6432Node\Valve\Steam",
        r"SOFTWARE\Valve\Steam",
    ]
    for subkey in subkeys:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "InstallPath")  # pyright: ignore[reportAny]
                path = Path(value)  # pyright: ignore[reportAny]
                if path.exists():
                    return path
        except FileNotFoundError:
            pass
        except OSError:
            pass

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            value, _ = winreg.QueryValueEx(key, "SteamPath")  # pyright: ignore[reportAny]
            path = Path(value)  # pyright: ignore[reportAny]
            if path.exists():
                return path
    except FileNotFoundError:
        pass
    except OSError:
        pass

    fallback = Path(r"C:\Program Files (x86)\Steam")
    if fallback.exists():
        return fallback

    return None


@cache
def find_steam_libraries(steam_root: Path) -> list[Path]:
    libraries = [steam_root]

    vdf_path = steam_root / "steamapps" / "libraryfolders.vdf"
    if not vdf_path.exists():
        return libraries

    text = vdf_path.read_text(encoding="utf-8", errors="ignore")

    matches = re.findall(r'"path"\s+"([^"]+)"', text)
    for raw in matches:  # pyright: ignore[reportAny]
        path = Path(raw.replace("\\\\", "\\"))  # pyright: ignore[reportAny]
        if path.exists() and path not in libraries:
            libraries.append(path)

    return libraries


def find_rimworld_root(steam_root: Path) -> Path | None:
    return _find_rimworld_root(steam_root)


def _find_rimworld_root(steam_root: Path) -> Path | None:
    for library in find_steam_libraries(steam_root):
        candidate = library / "steamapps" / "common" / "RimWorld"
        if candidate.exists():
            return candidate

    return None


def find_rimworld_workshop_path(steam_root: Path) -> Path | None:
    return _find_rimworld_workshop_path(steam_root)


def _find_rimworld_workshop_path(steam_root: Path) -> Path | None:
    for library in find_steam_libraries(steam_root):
        candidate = (
            library / "steamapps" / "workshop" / "content" / RIMWORLD_STEAM_APP_ID
        )
        if candidate.exists():
            return candidate

    return None
