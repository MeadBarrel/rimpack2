from pathlib import Path
from dataclasses import dataclass
from .about import AboutModMetadata, load_about_xml


class ModFolderError(ValueError):
    """Raised when a mod folder does not contain the expected files."""


@dataclass(frozen=True)
class ModFolder:
    path: Path
    about: AboutModMetadata


def load_mod_folder(path: Path) -> ModFolder:
    mod_path = path.resolve()
    if not mod_path.is_dir():
        raise ModFolderError(f"Mod folder path is not a directory: {mod_path}")

    about_path = mod_path / "About" / "About.xml"
    if not about_path.is_file():
        raise ModFolderError(f"Missing required file: {about_path}")

    return ModFolder(path=mod_path, about=load_about_xml(about_path))
