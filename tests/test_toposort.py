from rimpack.core.mod.about import parse_about_xml
from rimpack.core.toposort import (
    mod_to_sort_item,
    sort_package_ids,
    stable_toposort,
    ToposortItem,
    CycleError,
    restore_original_order,
)
import pytest


def test_stable_toposort():
    items = [
        ToposortItem(0, before=[1]),
        ToposortItem(1),
        ToposortItem(2, after=[4]),
        ToposortItem(3),
        ToposortItem(4, before=[2], after=[5]),
        ToposortItem(5),
        ToposortItem(6),
        ToposortItem(7, before=[4]),
        ToposortItem(8, before=[1, 2]),
        ToposortItem(9, before=[3, 6], after=[1]),
    ]
    expected = [0, 8, 1, 9, 3, 5, 7, 4, 2, 6]
    result = stable_toposort(items)
    assert result == expected


def test_stable_toposort_ignore_missing_dependencies():
    items = [
        ToposortItem(0, after=[2]),
    ]
    result = stable_toposort(items)
    assert result == [0]


def test_stable_toposort_ignore_missing_dependencies_before():
    items = [
        ToposortItem(0, before=[2]),
    ]
    result = stable_toposort(items)
    assert result == [0]


def test_stable_toposort_cycle():
    items = [
        ToposortItem(0),
        ToposortItem(1, before=[2]),
        ToposortItem(2, before=[1]),
    ]
    with pytest.raises(CycleError):
        _ = stable_toposort(items)


def test_restore_original_order():
    original = ["Foo", "Bar", "Baz"]
    shuffled_lower = ["baz", "foo", "bar"]

    result = restore_original_order(original, shuffled_lower)

    assert result == ["Baz", "Foo", "Bar"]


def test_restore_original_order_with_duplicates():
    original = ["Foo", "FOO", "Bar"]
    shuffled_lower = ["foo", "foo", "bar"]

    result = restore_original_order(original, shuffled_lower)

    assert result == ["Foo", "FOO", "Bar"]


def test_restore_original_order_raises_for_missing_item():
    original = ["Foo", "Bar"]
    shuffled_lower = ["foo", "baz"]

    with pytest.raises(ValueError, match="baz"):
        _ = restore_original_order(original, shuffled_lower)


def test_sort_package_ids():
    items = [
        ToposortItem("Ludeon.Rimworld"),
        ToposortItem("Harmony", before=["ludeon.Rimworld"]),
        ToposortItem("my.mod", after=["harmony"]),
    ]
    result = sort_package_ids(items)
    expected = ["Harmony", "Ludeon.Rimworld", "my.mod"]
    assert result == expected


def test_mod_to_toposort_item():
    source = """\
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <packageId>AuthorName.ModName</packageId>
    <name>My Mod Name</name>
    <author>Author Name, Another Author Name, A Third Author Name</author>
    <description>This is the description of this mod.</description>
    <supportedVersions>
    <li>1.6</li>
    </supportedVersions>
    <modDependencies>
        <li>
            <packageId>brrainz.harmony</packageId>
            <displayName>Harmony</displayName>
            <steamWorkshopUrl>steam://url/CommunityFilePage/2009463077</steamWorkshopUrl>
        </li>
        <li>
            <packageId>some.library</packageId>
        </li>
        <li>
            <packageId>erdelf.HumanoidAlienRaces</packageId>
            <displayName>Humanoid Alien Races</displayName>
            <steamWorkshopUrl>steam://url/CommunityFilePage/839005762</steamWorkshopUrl>
            <alternativePackageIds IgnoreIfNoMatchingField="True">
            <li>erdelf.HumanoidAlienRaces.dev</li>
            </alternativePackageIds>
        </li>
    </modDependencies>
    <modDependenciesByVersion>
        <v1.4>
            <li>
            <packageId>some.other.library</packageId>
            </li>
        </v1.4>
        <v1.6>
            <li>
            <packageId>some.other.library.2</packageId>
            </li>
        </v1.6>
    </modDependenciesByVersion>
    <loadBefore>
        <li>CETeam.CombatExtended</li>
    </loadBefore>
    <loadBeforeByVersion>
        <v1.4>
            <li>prepatcher</li>
        </v1.4>
        <v1.6>
            <li>prepatcher.new</li>
        </v1.6>
    </loadBeforeByVersion>
    <forceLoadBefore>
        <li>force.load.before</li>
    </forceLoadBefore>
    <loadAfter>
        <li>load.after</li>
    </loadAfter>
    <loadAfterByVersion>
        <v1.4>
            <li>load.after.by.version.14</li>
        </v1.4>
        <v1.6>
            <li>load.after.by.version.16</li>
        </v1.6>
    </loadAfterByVersion>
    <forceLoadAfter>
        <li>force.load.after</li>
    </forceLoadAfter>
</ModMetaData>
    """
    about = parse_about_xml(source)
    result = mod_to_sort_item(about, "1.6.2")
    assert result.item == "AuthorName.ModName"
    assert set(result.before) == {
        "CETeam.CombatExtended",
        "prepatcher.new",
        "force.load.before",
    }
    assert set(result.after) == {
        "brrainz.harmony",
        "some.library",
        "erdelf.HumanoidAlienRaces",
        "some.other.library.2",
        "load.after",
        "load.after.by.version.16",
        "force.load.after",
    }
