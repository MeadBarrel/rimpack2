from pathlib import Path
from shutil import copytree
from io import StringIO

from ruamel.yaml import YAML

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


def normalize_yaml_text(text: str) -> str:
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)  # pyright: ignore[reportAny]
    yaml.preserve_quotes = True
    data = yaml.load(text)  # pyright: ignore[reportAny, reportUnknownMemberType]
    stream = StringIO()
    yaml.dump(data, stream)  # pyright: ignore[reportUnknownMemberType]
    return stream.getvalue()


def assert_yaml_text_equal(actual: str, expected: str) -> None:
    assert normalize_yaml_text(actual) == normalize_yaml_text(expected)
