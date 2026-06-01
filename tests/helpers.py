from pathlib import Path
from shutil import copytree

_DATA_PATH = Path(__file__).parent / "data"
_MODS_PATH = _DATA_PATH / "mods"


def get_mod_folder(mod_name: str) -> Path:
    result = _MODS_PATH / mod_name
    assert result.exists()
    assert result.is_dir()
    return result


def copy_mods(path: Path, *names: str):
    for name in names:
        copytree(get_mod_folder(name), path / name, dirs_exist_ok=True)
