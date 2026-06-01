from dataclasses import dataclass, field
from typing import Self, TypeAlias

from ruamel.yaml import YAML
import typedload


@dataclass(frozen=True)
class ModuleModReferencePid:
    pid: str


@dataclass(frozen=True)
class ModuleModReferenceWid:
    wid: int


@dataclass(frozen=True)
class ModuleModReferenceLoc:
    wid: str


ModuleModReference: TypeAlias = (
    ModuleModReferencePid | ModuleModReferenceWid | ModuleModReferenceLoc
)


@dataclass(frozen=True)
class ModuleModExtras:
    before: tuple[ModuleModReference, ...] = field(default_factory=tuple)
    after: tuple[ModuleModReference, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ModuleModPid(ModuleModReferencePid, ModuleModExtras): ...


@dataclass(frozen=True)
class ModuleModWid(ModuleModReferenceWid, ModuleModExtras): ...


class ModuleModLoc(ModuleModReferenceLoc, ModuleModExtras): ...


ModuleMod: TypeAlias = ModuleModPid | ModuleModWid | ModuleModLoc


@dataclass(frozen=True)
class Group:
    group: str
    mods: tuple[ModuleMod]


Groups = tuple[Group, ...]


@dataclass(frozen=True)
class Module:
    groups: Groups

    @classmethod
    def parse(cls, source: str) -> Self:
        yaml = YAML()
        src = yaml.parse(source)  # pyright: ignore[reportAny, reportUnknownMemberType]
        groups = typedload.load(src, Groups)
        return cls(groups)
