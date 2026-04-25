from pathlib import Path
from typing import Literal

from rimpack.core.listfile import (
    ModList,
    ModListRecordLoc,
    ModListRecordPid,
    ModListRecordWid,
    ModListReferenceLoc,
    ModListReferencePid,
    ModListReferenceWid,
)


class ExternalWidReference:
    @property
    def kind(self) -> Literal["wid"]:
        return "wid"

    @property
    def reference(self) -> str:
        return "2009463077"


def test_load_mod_list_from_yaml(tmp_path: Path):
    list_path = tmp_path / "mods.yaml"
    list_path.write_text(
        """
core:
  - pid: ludeon.rimworld
    name: RimWorld
    before:
      - wid: 2009463077
        name: Harmony
    after:
      - loc: LocalFramework
  - wid: 2009463077
    name: Harmony
    before: []
    after:
      - pid: ludeon.rimworld
libraries:
  - loc: LocalFramework
""".strip(),
        encoding="utf-8",
    )

    mod_list = ModList.load(list_path)

    assert mod_list.data == {
        "core": (
            ModListRecordPid(
                pid="ludeon.rimworld",
                name="RimWorld",
                before=[
                    ModListReferenceWid(wid=2009463077, name="Harmony"),
                ],
                after=[
                    ModListReferenceLoc(loc="LocalFramework"),
                ],
            ),
            ModListRecordWid(
                wid=2009463077,
                name="Harmony",
                before=[],
                after=[
                    ModListReferencePid(pid="ludeon.rimworld"),
                ],
            ),
        ),
        "libraries": (
            ModListRecordLoc(
                loc="LocalFramework",
                before=[],
                after=[],
            ),
        ),
    }


def test_dump_mod_list_to_yaml(tmp_path: Path):
    mod_list = ModList(
        {
            "core": [
                {
                    "pid": "ludeon.rimworld",
                    "name": "RimWorld",
                    "before": [{"wid": 2009463077, "name": "Harmony"}],
                    "after": [{"loc": "LocalFramework"}],
                },
                {
                    "wid": 2009463077,
                    "name": "Harmony",
                    "after": [{"pid": "ludeon.rimworld"}],
                },
            ],
            "libraries": [{"loc": "LocalFramework"}],
        }
    )
    list_path = tmp_path / "mods.yaml"

    mod_list.dump(list_path)

    assert ModList.load(list_path).data == mod_list.data


def test_with_added_mod_returns_new_list_with_record_appended():
    mod_list = ModList({"core": [{"pid": "ludeon.rimworld"}]})
    record = ModListRecordWid(
        wid=2009463077,
        name="Harmony",
        before=[ModListReferencePid(pid="ludeon.rimworld")],
        after=[],
    )

    updated = mod_list.with_added_mod("core", record)

    assert mod_list.data == {
        "core": (
            ModListRecordPid(
                pid="ludeon.rimworld",
                before=[],
                after=[],
            ),
        )
    }
    assert updated.data == {
        "core": (
            ModListRecordPid(
                pid="ludeon.rimworld",
                before=[],
                after=[],
            ),
            record,
        )
    }


def test_with_added_mod_creates_missing_pack():
    mod_list = ModList({})
    record = ModListRecordLoc(loc="LocalFramework")

    updated = mod_list.with_added_mod("libraries", record)

    assert updated.data == {"libraries": (record,)}


def test_with_added_mod_accepts_mod_reference():
    mod_list = ModList({})

    updated = mod_list.with_added_mod("libraries", ExternalWidReference())

    assert updated.data == {
        "libraries": (
            ModListRecordWid(wid=2009463077, before=[], after=[]),
        )
    }


def test_with_added_mod_dumps_comment_when_set(tmp_path: Path):
    mod_list = ModList({})
    record = ModListRecordLoc(loc="LocalFramework")
    list_path = tmp_path / "mods.yaml"

    updated = mod_list.with_added_mod(
        "libraries",
        record,
        comment="Installed from local mods",
    )
    updated.dump(list_path)

    assert "# Installed from local mods" in list_path.read_text(encoding="utf-8")
    assert ModList.load(list_path).data == {"libraries": (record,)}


def test_with_added_mod_preserves_existing_comments(tmp_path: Path):
    list_path = tmp_path / "mods.yaml"
    list_path.write_text(
        """
libraries:
  - loc: LocalFramework  # Existing local mod
""".strip(),
        encoding="utf-8",
    )
    mod_list = ModList.load(list_path)

    updated = mod_list.with_added_mod(
        "libraries",
        ModListReferenceWid(wid=2009463077),
        comment="Added workshop mod",
    )
    updated.dump(list_path)

    contents = list_path.read_text(encoding="utf-8")
    assert "# Existing local mod" in contents
    assert "# Added workshop mod" in contents


def test_with_removed_mod_returns_new_list_without_matching_records():
    mod_list = ModList(
        {
            "core": [
                {"pid": "ludeon.rimworld"},
                {"wid": 2009463077, "name": "Harmony"},
            ],
            "libraries": [{"wid": 2009463077}],
        }
    )

    updated = mod_list.with_removed_mod(ModListReferenceWid(wid=2009463077))

    assert mod_list.data == {
        "core": (
            ModListRecordPid(pid="ludeon.rimworld", before=[], after=[]),
            ModListRecordWid(
                wid=2009463077,
                name="Harmony",
                before=[],
                after=[],
            ),
        ),
        "libraries": (
            ModListRecordWid(wid=2009463077, before=[], after=[]),
        ),
    }
    assert updated.data == {
        "core": (
            ModListRecordPid(pid="ludeon.rimworld", before=[], after=[]),
        ),
        "libraries": (),
    }
