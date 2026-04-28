from collections.abc import Iterator
from pathlib import Path

import pytest
from rich.table import Table
import typer
from rich.console import Console
from rich.prompt import Confirm
from tomlkit import TOMLDocument

from rimpack.core.config import (
    Config,
    find_rimworld_root,
    find_rimworld_workshop_path,
    find_steam_root,
)
from rimpack.core.listfile import ModList, ModListRecord, ModListRecordPid
from rimpack.core.mod.about import AboutModMetadata, parse_about_xml
from rimpack.core.packfile import PackConfig
from rimpack.core.steamworks import Steamworks, resolve_rimworld_workshop_mod_by_id
from rimpack.core.toposort import mod_to_sort_item, sort_package_ids

app = typer.Typer()

console = Console()


@app.command("create-config")
def cli_create_config():
    _ = _attempt_create_config()


@app.command("init")
def cli_init():
    config = _attempt_create_config()
    dlcs_about = list(_detect_dlcs(config))
    dlcs_sort_items = [mod_to_sort_item(item, "1.6") for item in dlcs_about]
    dlcs = sort_package_ids(dlcs_sort_items)
    path = Path.cwd()
    Path("lists").mkdir()

    list_files = [
        "00_ludeon.yml",
        "05_libraries.yml",
        "10_core.yml",
        "50_textures.yml",
        "55_sounds.yml",
        "90_patches.yml",
    ]
    list_files = [Path("lists") / item for item in list_files]

    ludeon_mod_list = ModList().with_added_pack("ludeon")
    for dlc in dlcs:
        ludeon_mod_list = ludeon_mod_list.with_added_mod(
            "ludeon", ModListRecordPid(pid=dlc)
        )
    ludeon_mod_list.dump(list_files[0])

    ModList().with_added_pack("libraries", "Core Libraries").dump(list_files[1])
    ModList().with_added_pack("core").dump(list_files[2])
    ModList().with_added_pack("textures").dump(list_files[3])
    ModList().with_added_pack("sounds").dump(list_files[4])
    ModList().with_added_pack("patches").dump(list_files[5])

    list_files_str = [item.as_posix() for item in list_files]

    pack_file = PackConfig.initialize(path.name, "1.6", list_files_str)
    pack_file.save(Path("pack.toml"))


@app.command("resolve")
def cli_resolve(
    workshop_id: int,
    config_path: Path | None = None,
    unsubscribe: bool = False,
):
    config_path = config_path or Config.get_default_config_path()

    config = Config.from_toml(config_path)
    steamworks = Steamworks()
    workshop_root = config.rimworld_workshop_path
    if workshop_root is None:
        print("Workshop root not set")
        raise typer.Exit(1)
    mod = resolve_rimworld_workshop_mod_by_id(
        steamworks, workshop_root, workshop_id, unsubscribe=unsubscribe
    )
    table = Table(title="Mod Metadata")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Path", str(mod.path))
    table.add_row("Name", mod.about.name)
    table.add_row("Package ID", mod.about.package_id)
    table.add_row("Description", mod.about.description)
    table.add_row("Supported Versions", str(mod.about.supported_versions))
    console.print(table)


def _detect_dlcs(config: Config) -> Iterator[AboutModMetadata]:
    rimworld_path = config.rimworld_path
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


def _attempt_create_config() -> Config:
    config_path = Config.get_default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config = Config(TOMLDocument())
    else:
        config = Config.from_toml(config_path)
    assert config.file_config is not None

    if config.rimworld_path is None or config.rimworld_workshop_path is None:
        if config.rimworld_workshop_path is not None:
            confirm_str = (
                "[b]rimworld_path[/] is not set in config. Try to find automatically?"
            )
        elif config.rimworld_path is not None:
            confirm_str = "[b]rimworld_workshop_path[/] is not set in config. Try to find automatically?"
        else:
            confirm_str = (
                "Rimworld paths are not set in config. Try to find automatically?"
            )
        if not Confirm.ask(confirm_str, console=console):
            return config
        steam_root = find_steam_root()
        if steam_root is None:
            console.print("Steam root could not be found...")
            return config
        if config.rimworld_path is None:
            rimworld_root = find_rimworld_root(steam_root)
            if rimworld_root is None:
                console.print("[b]rimworld_path[/] could not be found")
            else:
                config = config.with_rimworld_path(rimworld_root)
                config.save(config_path)
                console.print(f"[b]rimworld_path[/] set to {rimworld_root}")
        if config.rimworld_workshop_path is None:
            workshop_root = find_rimworld_workshop_path(steam_root)
            if workshop_root is None:
                console.print("[b]rimworld_workshop_path[/] could not be found")
            else:
                config = config.with_rimworld_workshop_path(workshop_root)
                config.save(config_path)
                console.print(f"[b]rimworld_workshop_path[/] set to {workshop_root}")
    return config


def main():
    app()
