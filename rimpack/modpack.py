from dataclasses import dataclass
from pathlib import Path
from .packfile import PackConfig


@dataclass(frozen=True)
class Modpack:
    pack: PackConfig
    root: Path
