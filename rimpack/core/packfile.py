from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Self
from pydantic import BaseModel
from tomlkit import TOMLDocument, dumps, table  # pyright: ignore[reportUnknownVariableType]
import tomlkit
from tomlkit.items import Array, Table


class PackPack(BaseModel):
    name: str
    rimworld_version: str


class PackLayout(BaseModel):
    mod_files: tuple[str, ...]


class PackFileModel(BaseModel):
    pack: PackPack
    layout: PackLayout


@dataclass(frozen=True)
class PackConfig:
    _doc: TOMLDocument
    _model: PackFileModel

    @classmethod
    def from_toml(cls, path: Path) -> Self:
        return cls.from_source(path.read_text())

    @classmethod
    def from_source(cls, source: str) -> Self:
        doc, model = load_pack_file(source)
        return cls(doc, model)

    @classmethod
    def initialize(
        cls,
        name: str,
        rimworld_version: str,
        mod_files: Iterable[str],
    ) -> Self:
        doc = TOMLDocument()
        pack = table()
        _ = pack.add("name", name)
        _ = pack.add("rimworld_version", rimworld_version)
        _ = doc.add("pack", pack)
        layout = table()
        _ = layout.add("mod_files", list(mod_files))
        _ = doc.add("layout", layout)
        model = PackFileModel.model_validate(doc)
        return cls(doc, model)

    def save(self, path: Path):
        _ = path.write_text(self.render())

    def render(self) -> str:
        return dumps(self._doc)

    @property
    def name(self) -> str:
        return self._model.pack.name

    @property
    def rimworld_version(self) -> str:
        return self._model.pack.rimworld_version

    @property
    def mod_files(self) -> tuple[str, ...]:
        return self._model.layout.mod_files

    def with_added_mod_file(self, mod_file: str) -> Self:
        doc = deepcopy(self._doc)
        layout = doc["layout"]
        assert isinstance(layout, Table)
        mod_files = layout["mod_files"]
        assert isinstance(mod_files, Array)
        mod_files.append(mod_file)  # pyright: ignore[reportUnknownMemberType]
        model = PackFileModel.model_validate(doc)
        return self.__class__(doc, model)


def load_pack_file(source: str) -> tuple[TOMLDocument, PackFileModel]:
    doc = tomlkit.parse(source)
    model = PackFileModel.model_validate(doc)
    return doc, model
