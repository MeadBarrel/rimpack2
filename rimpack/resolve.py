from collections.abc import Collection, Iterable, Iterator
from pathlib import Path
from rimpack.config import Config
from rimpack.exceptions import ModFolderError
from rimpack.mod.modfolder import ModFolder, load_mod_folder
from rimpack.modpack import Modpack
from rimpack.steamworks import Steamworks, resolve_rimworld_workshop_mod_by_id
from rimpack.types import ModReference, ModReferencePid, ModReferenceWid


def find_installed_mod(
    config: Config | None, modpack: Modpack | None, reference: ModReference
) -> Iterable[ModFolder]: ...


def install_mod(config: Config, reference: ModReferenceWid) -> ModFolder: ...


def uninstall_mod(config: Config, reference: ModReferenceWid) -> ModFolder: ...


def _resolve_package_id(
    mod_folders: Collection[Path],
    package_id: int,
) -> ModFolder: ...


def _find_installed_mod_pid(
    config: Config | None, modpack: Modpack | None, reference: ModReferencePid
) -> Iterator[ModFolder]:
    paths = (
        config.rimworld_workshop_path,
        config.rimworld_local_mods_path,
    )


def _find_installed_mod_pid_in_folder(
    path: Path, reference: ModReferencePid
) -> Iterator[ModFolder]:
    if not path.is_dir():
        raise ValueError("path is not a directory")
    for subfolder in path.iterdir():
        if not subfolder.is_dir():
            continue
        item = _try_load_modfolder(subfolder)
        if item is not None:
            yield item


def _try_load_modfolder(path: Path) -> ModFolder | None:
    try:
        return load_mod_folder(path)
    except ModFolderError:
        return None


def _resolve_steam(
    steamworks: Steamworks,
    workshop_root: Path,
    workshop_id: int,
    unsubscribe: bool = False,
) -> ModFolder:
    return resolve_rimworld_workshop_mod_by_id(
        steamworks, workshop_root, workshop_id, unsubscribe
    )
