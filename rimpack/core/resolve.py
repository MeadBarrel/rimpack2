from collections.abc import Collection
from pathlib import Path
from rimpack.core.config import Config
from rimpack.core.mod.modfolder import ModFolder
from rimpack.core.steamworks import Steamworks, resolve_rimworld_workshop_mod_by_id
from rimpack.core.types import ModReference


def find_installed_mod(config: Config, reference: ModReference) -> ModFolder | None: ...


def install_mod(config: Config, reference: ModReference) -> ModFolder: ...


def uninstall_mod(config: Config, reference: ModReference) -> ModFolder: ...


def _resolve_package_id(
    mod_folders: Collection[Path],
    package_id: int,
) -> ModFolder: ...


def _resolve_steam(
    steamworks: Steamworks,
    workshop_root: Path,
    workshop_id: int,
    unsubscribe: bool = False,
) -> ModFolder:
    return resolve_rimworld_workshop_mod_by_id(
        steamworks, workshop_root, workshop_id, unsubscribe
    )
