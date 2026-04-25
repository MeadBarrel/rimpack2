from copy import deepcopy
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Self, TypeAlias, cast, final, overload

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
import typedload

from rimpack.core.types import ModReference, references_match


@dataclass(frozen=True, kw_only=True)
class ModListReferenceFields:
    name: str | None = None


@dataclass(frozen=True, kw_only=True)
class ModListReferencePid(ModListReferenceFields):
    pid: str

    @property
    def kind(self) -> Literal["pid"]:
        return "pid"

    @property
    def reference(self) -> str:
        return self.pid


@dataclass(frozen=True, kw_only=True)
class ModListReferenceWid(ModListReferenceFields):
    wid: int

    @property
    def kind(self) -> Literal["wid"]:
        return "wid"

    @property
    def reference(self) -> str:
        return str(self.wid)


@dataclass(frozen=True, kw_only=True)
class ModListReferenceLoc(ModListReferenceFields):
    loc: str

    @property
    def kind(self) -> Literal["loc"]:
        return "loc"

    @property
    def reference(self) -> str:
        return self.loc


ModListReference: TypeAlias = (
    ModListReferencePid | ModListReferenceWid | ModListReferenceLoc
)


@dataclass(frozen=True, kw_only=True)
class ModListRecordFields:
    before: list[ModListReference] = field(default_factory=list)
    after: list[ModListReference] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class ModListRecordPid(ModListReferencePid, ModListRecordFields): ...


@dataclass(frozen=True, kw_only=True)
class ModListRecordWid(ModListReferenceWid, ModListRecordFields): ...


@dataclass(frozen=True, kw_only=True)
class ModListRecordLoc(ModListReferenceLoc, ModListRecordFields): ...


ModListRecord: TypeAlias = ModListRecordPid | ModListRecordWid | ModListRecordLoc
ModListRecords: TypeAlias = tuple[ModListRecord, ...]
ModListPacks: TypeAlias = dict[str, ModListRecords]


@final
class ModList:
    def __init__(
        self,
        source: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> None:
        self.data: ModListPacks = typedload.load(source, ModListPacks)
        self._source = (
            source
            if isinstance(source, CommentedMap)
            else _packs_to_source(self.data)
        )

    def dump(self, file: Path):
        yaml = _create_yaml()
        with file.open("w", encoding="utf-8") as output_file:
            yaml.dump(self._source, output_file)  # pyright: ignore[reportUnknownMemberType]

    @classmethod
    def load(cls, file: Path) -> Self:
        text_contents = file.read_text("utf-8")
        yaml = _create_yaml()
        source = yaml.load(text_contents)  # pyright: ignore[reportAny, reportUnknownMemberType]
        return cls(source)

    @overload
    def with_added_mod(
        self, pack: str, record: ModListRecord, comment: str | None = None
    ) -> Self: ...

    @overload
    def with_added_mod(
        self, pack: str, record: ModReference, comment: str | None = None
    ) -> Self: ...

    def with_added_mod(
        self, pack: str, record: ModListRecord | ModReference, comment: str | None = None
    ) -> Self:
        mod_record = _reference_to_record(record)
        source = _copy_source(self._source)
        sequence = _get_or_create_pack_sequence(source, pack)
        sequence.append(_record_to_source(mod_record))  # pyright: ignore[reportUnknownMemberType]
        if comment is not None:
            sequence.yaml_add_eol_comment(comment, len(sequence) - 1)  # pyright: ignore[reportUnknownMemberType]
        return self.__class__(source)

    def with_removed_mod(
        self, reference: ModReference, comment: str | None = None
    ) -> Self:
        _ = comment
        data = {
            pack: tuple(
                record
                for record in records
                if not references_match(record, reference)
            )
            for pack, records in self.data.items()
        }
        return self.__class__(_packs_to_source(data))


def _create_yaml() -> YAML:
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)  # pyright: ignore[reportAny]
    yaml.preserve_quotes = True
    return yaml


def _packs_to_source(
    packs: ModListPacks,
) -> CommentedMap:
    source = CommentedMap()
    for pack, records in packs.items():
        source[pack] = CommentedSeq(_record_to_source(record) for record in records)
    return source


def _copy_source(source: CommentedMap) -> CommentedMap:
    return deepcopy(source)


def _get_or_create_pack_sequence(source: CommentedMap, pack: str) -> CommentedSeq:
    if pack not in source:
        sequence = CommentedSeq()
        source[pack] = sequence
        return sequence
    current = cast(object, source[pack])
    if isinstance(current, CommentedSeq):
        return current
    if not isinstance(current, Iterable):
        raise TypeError("Expected pack contents to be a sequence")
    sequence = CommentedSeq(current)
    source[pack] = sequence
    return sequence


def _record_to_source(record: ModListRecord) -> dict[str, object]:
    source = _reference_to_source(record)
    if record.before:
        source["before"] = [
            _reference_to_source(reference) for reference in record.before
        ]
    if record.after:
        source["after"] = [
            _reference_to_source(reference) for reference in record.after
        ]
    return source


def _reference_to_source(reference: ModListReference) -> dict[str, object]:
    match reference:
        case ModListReferencePid(pid=pid):
            source: dict[str, object] = {"pid": pid}
        case ModListReferenceWid(wid=wid):
            source = {"wid": wid}
        case ModListReferenceLoc(loc=loc):
            source = {"loc": loc}
    if reference.name is not None:
        source["name"] = reference.name
    return source


def _reference_to_record(reference: ModListRecord | ModReference) -> ModListRecord:
    if isinstance(
        reference,
        (ModListRecordPid, ModListRecordWid, ModListRecordLoc),
    ):
        return reference
    match reference.kind:
        case "pid":
            return ModListRecordPid(pid=reference.reference)
        case "wid":
            return ModListRecordWid(wid=int(reference.reference))
        case "loc":
            return ModListRecordLoc(loc=reference.reference)

