from pydantic import BaseModel
from tomlkit import TOMLDocument
import tomlkit


class PackPack(BaseModel):
    name: str
    rimworld_version: str


class PackLayout(BaseModel):
    mod_files: list[str]


class PackFileModel(BaseModel):
    pack: PackPack
    layout: PackLayout


def load_pack_file(source: str) -> tuple[TOMLDocument, PackFileModel]:
    doc = tomlkit.parse(source)
    model = PackFileModel.model_validate(doc)
    return doc, model
