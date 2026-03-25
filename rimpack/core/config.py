from dataclasses import dataclass
import os
from pathlib import Path
from typing import Self, override
import re
import winreg
import tomlkit

from pydantic import TypeAdapter


class RimworldConfigParseError(ValueError):
    pass


class RimworldPathUnknownError(Exception):
    @override
    def __str__(self) -> str:
        return "Rimworld path is not set"


class WorkshopPathUnkwnownError(Exception):
    @override
    def __str__(self) -> str:
        return "Workshop path is not set"


@dataclass(frozen=True)
class RimworldConfig:
    rimworld_path: Path | None = None
    rimworld_workshop_path: Path | None = None


@dataclass(frozen=True)
class Config:
    _file_config: tomlkit.TOMLDocument | None = None

    @staticmethod
    def get_default_config_path() -> Path:
        return Path.resolve(Path("~/AppData/Local/rimpack/config.toml"))

    @classmethod
    def from_toml(cls, path: Path | None = None) -> Self:
        path = path or cls.get_default_config_path()
        source = path.read_text()
        return cls.from_toml_str(source)

    @classmethod
    def from_toml_str(cls, source: str) -> Self:
        doc = tomlkit.parse(source)
        return cls(doc)

    @property
    def rimworld_path(self) -> Path:
        if not self._file_config:
            if path := os.getenv("RIMWORLD_PATH"):
                return Path(path)
            raise RimworldPathUnknownError()
        if "rimworld_path" not in self._file_config:
            if path := os.getenv("RIMWORLD_PATH"):
                return Path(path)
            raise RimworldPathUnknownError()

        config_path = self._file_config["rimworld_path"]
        if not isinstance(config_path, str):
            raise RimworldConfigParseError("Incorrect value type for rimworld_path")
        return Path(config_path)

    @property
    def rimworld_workshop_path(self) -> Path:
        if not self._file_config:
            if path := os.getenv("RIMWORLD_WORKSHOP_PATH"):
                return Path(path)
            raise WorkshopPathUnkwnownError()
        if "rimworld_workshop_path" not in self._file_config:
            if path := os.getenv("RIMWORLD_WORKSHOP_PATH"):
                return Path(path)
            raise WorkshopPathUnkwnownError()

        config_path = self._file_config["rimworld_workshop_path"]
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


def find_steam_libraries(steam_root: Path) -> list[Path]:
    libraries = [steam_root]

    vdf_path = steam_root / "steamapps" / "libraryfolders.vdf"
    if not vdf_path.exists():
        return libraries

    text = vdf_path.read_text(encoding="utf-8", errors="ignore")

    matches = re.findall(r'"path"\s+"([^"]+)"', text)
    for raw in matches:
        path = Path(raw.replace("\\\\", "\\"))
        if path.exists() and path not in libraries:
            libraries.append(path)

    return libraries


def find_rimworld_root() -> Path | None:
    steam_root = find_steam_root()
    if steam_root is None:
        return None

    for library in find_steam_libraries(steam_root):
        candidate = library / "steamapps" / "common" / "RimWorld"
        if candidate.exists():
            return candidate

    return None
