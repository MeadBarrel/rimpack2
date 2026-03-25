from dataclasses import dataclass
from .packfile import PackConfig


@dataclass(frozen=True)
class Modpack:
    pack: PackConfig
