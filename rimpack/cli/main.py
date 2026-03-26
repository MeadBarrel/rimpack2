from collections.abc import Iterator
from pathlib import Path
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
from rimpack.core.listfile import (
    AliasLine,
    BlankLine,
    CommentLine,
    ListFile,
    ReferenceLine,
)
from rimpack.core.mod.about import parse_about_xml
from rimpack.core.packfile import PackConfig

app = typer.Typer()

console = Console()


@app.command("create-config")
def cli_create_config():
    _ = _attempt_create_config()


@app.command("init")
def cli_init():
    config = _attempt_create_config()
    dlcs = list(_detect_dlcs(config))
    path = Path.cwd()
    Path("lists").mkdir()

    list_files = [
        "00_ludeon.list",
        "05_libraries.list",
        "10_core.list",
        "50_textures.list",
        "55_sounds.list",
        "90_patches.list",
    ]
    list_files = [Path("lists") / item for item in list_files]

    lines = [
        AliasLine("ludeon"),
        BlankLine(),
        CommentLine("# Rimworld core and DLCs"),
        *[ReferenceLine(f"packageid:{dlc}") for dlc in dlcs],
    ]

    ludeon_list = ListFile(tuple(lines))
    ludeon_list.save(list_files[0])
    libraries_list = ListFile(
        (
            AliasLine("libraries"),
            BlankLine(),
            CommentLine("# Libraries"),
        )
    )
    libraries_list.save(list_files[1])
    core_list = ListFile(
        (AliasLine("core"), BlankLine(), CommentLine("# Core modpack mods"))
    )
    core_list.save(list_files[2])
    textures_list = ListFile(
        (AliasLine("textures"), BlankLine(), CommentLine("# Texture replacers"))
    )
    textures_list.save(list_files[3])
    sounds_list = ListFile(
        (AliasLine("sounds"), BlankLine(), CommentLine("# Sound replacers"))
    )
    sounds_list.save(list_files[4])
    patches_list = ListFile(
        (
            AliasLine("patches"),
            BlankLine(),
            CommentLine("# Patches"),
        )
    )
    patches_list.save(list_files[5])
    list_files_str = [item.as_posix() for item in list_files]

    pack_file = PackConfig.initialize(path.name, "1.6", list_files_str)
    pack_file.save(Path("pack.toml"))


def _detect_dlcs(config: Config) -> Iterator[str]:
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
        package_id = about.package_id
        yield package_id


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
