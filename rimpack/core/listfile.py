from dataclasses import dataclass
from math import inf
from typing import Literal, Self, override
import re
from functools import cached_property


class ListFileParsingError(ValueError): ...


class MultipleAliasDefinitionsError(ListFileParsingError):
    def __init__(self) -> None:
        super().__init__()

    @override
    def __str__(self) -> str:
        return "Multiple alias definitions are not allowed in list file"


class NonTopAliasDefinitionError(ListFileParsingError):
    def __init__(self) -> None:
        super().__init__()

    @override
    def __str__(self) -> str:
        return "Alias definition must be on top"


LineKind = Literal["blank", "alias", "comment", "entry", "unknown"]

ALIAS_RE = re.compile(
    r"""
    ^
    (?P<leading_ws>[ \t]*)
    @alias
    (?P<after_alias_keyword_ws>[ \t]+)
    (?P<alias>\w+)
    (?P<before_comment_ws>[ \t]*)
    (?P<trailing_comment>\#.*)?
    $
    """,
    re.VERBOSE,
)

REFERENCE_RE = re.compile(
    r"""
    ^
    (?P<leading_ws>[ \t]*)
    (?P<disabled>!)?
    (?P<after_bang_ws>[ \t]*)
    (?P<reference>steam:\d+|packageid:[^\s#]+|local:[^\s#]+)
    (?P<before_comment_ws>[ \t]*)
    (?P<trailing_comment>\#.*)?
    $
    """,
    re.VERBOSE,
)

COMMENT_RE = re.compile(r"^(?P<leading_ws>[ \t]*)(?P<comment>\#.*)$")


class Line:
    @classmethod
    def from_raw_line(cls, line: str) -> Self: ...  # pyright: ignore[reportUnusedParameter]

    def render_as_raw_line(self) -> str: ...


@dataclass(frozen=True)
class SteamReference:
    id: str


@dataclass(frozen=True)
class PackageIdReference:
    package_id: str


@dataclass(frozen=True)
class LocalReference:
    package_id: str


type Reference = SteamReference | PackageIdReference | LocalReference


@dataclass(frozen=True)
class ListFile:
    lines: tuple[Line, ...]

    @classmethod
    def from_string(cls, source: str) -> Self:
        lines = source.splitlines()
        lines = tuple(parse_line(line) for line in lines)
        aliases = [i for i, line in enumerate(lines) if isinstance(line, AliasLine)]
        first_reference_line_index = next(
            (i for i, line in enumerate(lines) if isinstance(line, ReferenceLine)), inf
        )
        if len(aliases) > 1:
            raise MultipleAliasDefinitionsError()
        if any(i > first_reference_line_index for i in aliases):
            raise NonTopAliasDefinitionError()
        return cls(lines=lines)

    @cached_property
    def alias(self) -> str | None:
        alias = next((line for line in self.lines if isinstance(line, AliasLine)), None)
        if alias is None:
            return None
        return alias.alias

    @cached_property
    def references(self) -> tuple[Reference, ...]:
        return tuple(
            reference_line_to_reference(line)
            for line in self.lines
            if isinstance(line, ReferenceLine)
        )

    def render(self) -> str:
        return "\n".join(line.render_as_raw_line() for line in self.lines)


def reference_line_to_reference(line: "ReferenceLine") -> Reference:
    reference_type, reference_value = line.reference.split(":", 1)
    match reference_type:
        case "steam":
            return SteamReference(reference_value)
        case "local":
            return LocalReference(reference_value)
        case "packageid":
            return PackageIdReference(reference_value)
        case _:
            raise ListFileParsingError(f"Unknown reference type: {reference_type}")


@dataclass(frozen=True)
class AliasLine(Line):
    leading_ws: str
    after_alias_keyword_ws: str
    alias: str
    before_comment_ws: str
    trailing_comment: str | None

    @classmethod
    @override
    def from_raw_line(cls, line: str) -> Self:
        match = ALIAS_RE.match(line)
        if match is None:
            raise ListFileParsingError(f"Incorrect input line for alias: {line}")
        groups = match.groupdict()
        leading_ws = groups["leading_ws"]
        after_alias_keyword_ws = groups["after_alias_keyword_ws"]
        alias = groups["alias"]
        before_comment_ws = groups["before_comment_ws"]
        trailing_comment = groups["trailing_comment"]
        return cls(
            leading_ws=leading_ws,
            after_alias_keyword_ws=after_alias_keyword_ws,
            alias=alias,
            before_comment_ws=before_comment_ws,
            trailing_comment=trailing_comment,
        )

    @override
    def render_as_raw_line(self) -> str:
        return f"{self.leading_ws}@alias{self.after_alias_keyword_ws}{self.alias}{self.before_comment_ws}{self.trailing_comment or ''}"


@dataclass(frozen=True)
class ReferenceLine(Line):
    leading_ws: str
    disabled: str | None
    after_bang_ws: str
    reference: str
    before_comment_ws: str
    trailing_comment: str | None

    @classmethod
    @override
    def from_raw_line(cls, line: str) -> Self:
        match = REFERENCE_RE.match(line)
        if match is None:
            raise ListFileParsingError(f"Incorrect input line for reference: {line}")
        groups = match.groupdict()
        return cls(
            leading_ws=groups["leading_ws"],
            disabled=groups["disabled"],
            after_bang_ws=groups["after_bang_ws"],
            reference=groups["reference"],
            before_comment_ws=groups["before_comment_ws"],
            trailing_comment=groups["trailing_comment"],
        )

    @override
    def render_as_raw_line(self) -> str:
        return f"{self.leading_ws}{self.disabled or ''}{self.after_bang_ws}{self.reference}{self.before_comment_ws}{self.trailing_comment or ''}"


@dataclass(frozen=True)
class BlankLine(Line):
    text: str

    @classmethod
    @override
    def from_raw_line(cls, line: str) -> Self:
        if line.strip() != "":
            raise ListFileParsingError(f"Incorrect input line for blank line: {line}")
        return cls(text=line)

    @override
    def render_as_raw_line(self) -> str:
        return self.text


@dataclass(frozen=True)
class CommentLine(Line):
    leading_ws: str
    comment: str

    @classmethod
    @override
    def from_raw_line(cls, line: str) -> Self:
        match = COMMENT_RE.match(line)
        if match is None:
            raise ListFileParsingError(f"Incorrect input line for comment line: {line}")
        groups = match.groupdict()
        return cls(
            leading_ws=groups["leading_ws"],
            comment=groups["comment"],
        )

    @override
    def render_as_raw_line(self) -> str:
        return f"{self.leading_ws}{self.comment}"


def parse_line(line: str) -> Line:
    for cls in (
        AliasLine,
        ReferenceLine,
        BlankLine,
        CommentLine,
    ):
        try:
            return cls.from_raw_line(line)
        except ListFileParsingError:
            continue
    raise ListFileParsingError(f"Unknown line format: {line}")
