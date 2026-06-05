from dataclasses import dataclass, field
from pathlib import Path
from typing import Self
from ruamel.yaml import YAML
import typedload


@dataclass(frozen=True)
class Config:
    rimworld_root: Path | None = None
    workshop_root: Path | None = None
    extra_mod_folders: list[Path] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> Self:
        return cls.parse(path.read_text("utf-8"))

    @classmethod
    def parse(cls, source: str) -> Self:
        yaml = YAML()
        src = yaml.load(source)  # pyright: ignore[reportAny, reportUnknownMemberType]
        return typedload.load(src, cls)
