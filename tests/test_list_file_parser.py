from _pytest._py.path import LocalPath
from rimpack.core.listfile import (
    AliasLine,
    BlankLine,
    CommentLine,
    Line,
    ListFile,
    LocalReference,
    MultipleAliasDefinitionsError,
    NonTopAliasDefinitionError,
    PackageIdReference,
    ReferenceLine,
    SteamReference,
    parse_line,
)
import pytest


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (
            "@alias hello_world",
            AliasLine(
                leading_ws="",
                after_alias_keyword_ws=" ",
                alias="hello_world",
                before_comment_ws="",
                trailing_comment=None,
            ),
        ),
        (
            "@alias hello_world # my comment! ",
            AliasLine(
                leading_ws="",
                after_alias_keyword_ws=" ",
                alias="hello_world",
                before_comment_ws=" ",
                trailing_comment="# my comment! ",
            ),
        ),
    ],
)
def test_alias_line_from_raw_line(line: str, expected: AliasLine):
    result = AliasLine.from_raw_line(line)
    assert result == expected


@pytest.mark.parametrize(
    "line",
    [
        "@alias hello_world",
        "  @alias    hello_world  ",
        "@alias hello_world # my comment ! ",
    ],
)
def test_alias_line_render(line: str):
    result = AliasLine.from_raw_line(line).render_as_raw_line()
    assert result == line


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (
            "steam:12345",
            ReferenceLine(
                leading_ws="",
                disabled=None,
                after_bang_ws="",
                reference="steam:12345",
                before_comment_ws="",
                trailing_comment=None,
            ),
        ),
        (
            "packageid:my.mod",
            ReferenceLine(
                leading_ws="",
                disabled=None,
                after_bang_ws="",
                reference="packageid:my.mod",
                before_comment_ws="",
                trailing_comment=None,
            ),
        ),
        (
            "local:my.mod",
            ReferenceLine(
                leading_ws="",
                disabled=None,
                after_bang_ws="",
                reference="local:my.mod",
                before_comment_ws="",
                trailing_comment=None,
            ),
        ),
        (
            "!steam:12345",
            ReferenceLine(
                leading_ws="",
                disabled="!",
                after_bang_ws="",
                reference="steam:12345",
                before_comment_ws="",
                trailing_comment=None,
            ),
        ),
        (
            "steam:12345  # hello world !",
            ReferenceLine(
                leading_ws="",
                disabled=None,
                after_bang_ws="",
                reference="steam:12345",
                before_comment_ws="  ",
                trailing_comment="# hello world !",
            ),
        ),
    ],
)
def test_reference_line_from_raw_line(line: str, expected: ReferenceLine):
    result = ReferenceLine.from_raw_line(line)
    assert result == expected


@pytest.mark.parametrize(
    "line",
    [
        "steam:12345",
        "!steam:12345",
        "packageid:my.mod",
        "   steam:12345    ",
        "steam:12345 # hello world!",
    ],
)
def test_reference_line_render_as_raw_line(line: str):
    result = ReferenceLine.from_raw_line(line).render_as_raw_line()
    assert result == line


@pytest.mark.parametrize("line", ["", "   \t   ", " "])
def test_blank_line_from_raw_line(line: str):
    result = BlankLine.from_raw_line(line)
    assert result.text == line


@pytest.mark.parametrize("line", ["", "   \t   ", " "])
def test_blank_line_from_raw_render_as_raw_line(line: str):
    result = BlankLine.from_raw_line(line).render_as_raw_line()
    assert result == line


@pytest.mark.parametrize(
    ["line", "expected"],
    [
        (
            "# my comment!",
            CommentLine(
                leading_ws="",
                comment="# my comment!",
            ),
        ),
        (
            "   # my comment!",
            CommentLine(
                leading_ws="   ",
                comment="# my comment!",
            ),
        ),
        (
            " \t   # my comment!",
            CommentLine(
                leading_ws=" \t   ",
                comment="# my comment!",
            ),
        ),
    ],
)
def test_comment_line_from_raw_line(line: str, expected: CommentLine):
    result = CommentLine.from_raw_line(line)
    assert result == expected


@pytest.mark.parametrize(
    "line", ["# my comment!", "  #coment", "#", " \t\t# my comment"]
)
def test_comment_line_render_as_raw_line(line: str):
    result = CommentLine.from_raw_line(line).render_as_raw_line()
    assert result == line


@pytest.mark.parametrize(
    ["line", "cls"],
    [
        ("@alias hello_world", AliasLine),
        ("steam:12345", ReferenceLine),
        ("", BlankLine),
        ("#hello world", CommentLine),
    ],
)
def test_parse_line(line: str, cls: type[Line]):
    result = parse_line(line)
    assert type(result) is cls


def test_list_file_from_string_fails_on_multiple_aliases():
    source = """
    @alias alias_1
    @alias alias_2
    """
    with pytest.raises(MultipleAliasDefinitionsError):
        _ = ListFile.from_string(source)


def test_list_file_from_string_fails_on_nontop_alias():
    source = """
    steam:12345

    @alias alias_2
    """
    with pytest.raises(NonTopAliasDefinitionError):
        _ = ListFile.from_string(source)


def test_list_file_from_string_accepts_alias_after_comment():
    source = """
    # My file
    @alias alias_2
    steam:12345
    """
    _ = ListFile.from_string(source)


def test_list_file_from_string_succeeds():
    source = """
    @alias myalias

    # Some comment

    steam:12345  # some other comment
    """
    _ = ListFile.from_string(source)


def test_list_file_with_property():
    source = """
    @alias myalias
    steam:12345
    """
    list_file = ListFile.from_string(source)
    assert list_file.alias == "myalias"


def test_list_file_without_property():
    source = """
    steam:12345
    """
    list_file = ListFile.from_string(source)
    assert list_file.alias is None


def test_list_file_references():
    source = """
    @alias my_alias

    steam:12345 # comment

    # Another comment
    local:my.mod
    packageid:another.mod
    """
    result = ListFile.from_string(source).references
    assert result == (
        SteamReference("12345"),
        LocalReference("my.mod"),
        PackageIdReference("another.mod"),
    )


def test_list_file_render():
    source = """
    @alias my_alias

    steam:12345 # comment

    # Another comment
    local:my.mod
    packageid:another.mod
    """
    result = ListFile.from_string(source).render()
    assert result == source
