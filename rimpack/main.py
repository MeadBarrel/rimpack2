from collections.abc import Iterator
from functools import cache
from pathlib import Path
import re
from typing import cast

import platformdirs
from ruamel.yaml import YAML, CommentedMap, CommentedSeq
import typer
from rich.console import Console

from rimpack.config import find_steam_root
from rimpack.parsers.config import Config
from rimpack.mod.about import AboutModMetadata, parse_about_xml
from rimpack.toposort import mod_to_sort_item, sort_package_ids
from rimpack.constants import RIMWORLD_STEAM_APP_ID

app = typer.Typer()

console = Console()

_NO_CONFIG_FILE_MESSAGE = (
    "No RimPack config file found at {path}. Run `rimpack create-config` to create one."
)


@app.command("create-config")
def cli_create_config():
    config_dir = get_default_config_dir()
    config_path = config_dir / "config.yml"
    if config_path.exists():
        console.print(f"RimPack config already exists at {config_path}")
        return

    steam_root = find_steam_root() or Path()
    rimworld_root = _prompt_path(
        "RimWorld root",
        find_rimworld_root(steam_root),
    )
    workshop_root = _prompt_path(
        "RimWorld workshop root",
        find_rimworld_workshop_path(steam_root),
    )

    config_dir.mkdir(parents=True, exist_ok=True)
    data = CommentedMap(
        {
            "rimworld_root": rimworld_root.as_posix(),
            "workshop_root": workshop_root.as_posix(),
        }
    )
    YAML().dump(data, config_path)  # pyright: ignore[reportUnknownMemberType]
    console.print(f"Created RimPack config at {config_path}")


def _prompt_path(label: str, default: Path | None) -> Path:
    if default is None:
        return Path(cast("str", typer.prompt(label)))
    return Path(cast("str", typer.prompt(label, default=default.as_posix())))


@app.command("init")
def cli_init():
    config = _read_config(get_default_config_dir())
    dlcs_about = list(_detect_dlcs(config))
    dlcs_sort_items = [mod_to_sort_item(item, "1.6") for item in dlcs_about]
    dlcs = sort_package_ids(dlcs_sort_items)

    path = Path.cwd()

    src = {"pack": {"modules": ["modules/00_ludeon.yml", "modules/10_core.yml"]}}

    pack_file_path = path / "pack.yml"
    YAML().dump(src, pack_file_path)  # pyright: ignore[reportUnknownMemberType]

    modules_path = path / "modules"
    modules_path.mkdir()
    modules_path_ludeon = modules_path / "00_ludeon.yml"
    modules_path_core = modules_path / "10_core.yml"

    data = CommentedSeq([{"pid": dlc} for dlc in dlcs])
    data.yaml_set_start_comment("Core")  # pyright: ignore[reportUnknownMemberType]
    YAML().dump(data, modules_path_ludeon)  # pyright: ignore[reportUnknownMemberType]
    modules_path_core.write_text(
        "# This module is expected to contain the core modules of the modpack.\n"
    )


def _read_config(config_dir: Path) -> Config:
    path = config_dir / "config.yml"
    try:
        return Config.from_file(path)
    except FileNotFoundError:
        console.print(_NO_CONFIG_FILE_MESSAGE.format(path=path), soft_wrap=True)
        raise typer.Exit(1)


def get_default_config_dir() -> Path:
    user_config_dir = platformdirs.user_config_dir()
    return Path(user_config_dir) / "rimpack"


def _detect_dlcs(config: Config) -> Iterator[AboutModMetadata]:
    rimworld_path = config.rimworld_root
    if rimworld_path is None:
        raise ValueError("Rimworld path is not set")
    rimworld_data_path = rimworld_path / "Data"
    for child in rimworld_data_path.iterdir():
        if not child.is_dir():
            continue
        about_xml_path = child / "About" / "About.xml"
        if not about_xml_path.exists():
            continue
        about = parse_about_xml(about_xml_path.read_text(encoding="utf-8"))
        yield about


def find_rimworld_root(steam_root: Path) -> Path | None:
    for library in find_steam_libraries(steam_root):
        candidate = library / "steamapps" / "common" / "RimWorld"
        if candidate.exists():
            return candidate

    return None


def find_rimworld_workshop_path(steam_root: Path) -> Path | None:
    for library in find_steam_libraries(steam_root):
        candidate = (
            library / "steamapps" / "workshop" / "content" / RIMWORLD_STEAM_APP_ID
        )
        if candidate.exists():
            return candidate

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


def main():
    app()
