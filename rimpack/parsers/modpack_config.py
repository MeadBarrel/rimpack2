from dataclasses import dataclass, field
import io
from pathlib import Path
from typing import NamedTuple, Self, cast, final, override

import typedload
from ruamel.yaml import YAML, CommentedMap, ruamel


class Commented[T](NamedTuple):
    value: T
    comment: str


class PackPack:
    def __init__(self, src: CommentedMap | None = None) -> None:
        self.src = src or CommentedMap()
        # self.name: str | None = None
        # self.rimworld_version: str | None = None

    @property
    def name(self) -> str | None:
        return self.src.get("name")

    @property
    def rimworld_version(self) -> str | None:
        return self.src.get("rimworld_version")

    @name.setter
    def name(self, value: str | Commented[str]):
        if isinstance(value, str):
            self.src["name"] = value
        else:
            self.src["name"] = value.value
            self.src.yaml_add_eol_comment(value.comment, "name")

    def __bool__(self) -> bool:
        return bool(self.src)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PackPack):
            return False
        return (
            self.name == other.name and self.rimworld_version == other.rimworld_version
        )


class PackLayout:
    mod_files: tuple[str, ...] = field(default_factory=tuple)
    mod_folders: tuple[Path, ...] = field(default_factory=tuple)

    def __init__(self, src: CommentedMap | None = None) -> None:
        self.src = src or CommentedMap()

    @override
    def __eq__(sef, other: object) -> bool:
        return True


@final
class ModpackConfigFile:
    def __init__(self, src: CommentedMap | None = None):
        self.src = src or CommentedMap()

    @property
    def layout(self) -> PackLayout | None:
        if "layout" in self.src:
            return PackLayout(self.src["layout"])
        return None

    @property
    def pack(self) -> PackPack:
        if "pack" in self.src:
            return PackPack(self.src["pack"])
        return PackPack()

    @pack.setter
    def pack(self, value: PackPack):
        self.src["pack"] = value.src

    def dump(self) -> str:
        yaml = _create_yaml()
        stream = io.StringIO()
        yaml.dump(self.src, stream)
        return stream.getvalue()


@final
class ModPackConfig:
    def __init__(self, src: CommentedMap | None = None) -> None:
        if src is None:
            self._src = CommentedMap()
            self._data = ModpackConfigFile()
        else:
            self._src = src or CommentedMap()
            self._data = typedload.load(src, ModpackConfigFile)

    @property
    def data(self) -> ModpackConfigFile:
        return self._data


def _create_yaml() -> YAML:
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)  # pyright: ignore[reportAny]
    yaml.preserve_quotes = True
    return yaml
