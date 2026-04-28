from __future__ import annotations

from pathlib import Path

import pytest

from rimpack.core.mod.about import (
    AboutDependency,
    AboutModMetadata,
    AboutTextValue,
    AboutXmlError,
    VersionedDependencyList,
    VersionedDescription,
    VersionedPackageIdList,
    load_about_xml,
    parse_about_xml,
)


def test_parse_required_fields_with_author_string() -> None:
    about = parse_about_xml(
        """\
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <packageId>AuthorName.ModName</packageId>
  <name>My Mod Name</name>
  <author>Author Name, Another Author</author>
  <description>This is the description of this mod.</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
""",
    )

    assert about == AboutModMetadata(
        package_id="AuthorName.ModName",
        name="My Mod Name",
        authors=("Author Name", "Another Author"),
        description="This is the description of this mod.",
        supported_versions=("1.6",),
    )


def test_parse_optional_sections_with_nested_structures() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <authors>
    <li>Author One</li>
    <li>Author Two</li>
  </authors>
  <description>Description</description>
  <supportedVersions>
    <li>1.5</li>
    <li>1.6</li>
  </supportedVersions>
  <modVersion IgnoreIfNoMatchingField="True">1.0.0</modVersion>
  <modIconPath IgnoreIfNoMatchingField="True">Textures/Icon</modIconPath>
  <url>https://example.invalid/mod</url>
  <descriptionsByVersion>
    <v1.5>Old description</v1.5>
    <v1.6>Current description</v1.6>
  </descriptionsByVersion>
  <modDependencies>
    <li>
      <packageId>brrainz.harmony</packageId>
      <displayName>Harmony</displayName>
      <steamWorkshopUrl>steam://url/CommunityFilePage/2009463077</steamWorkshopUrl>
      <downloadUrl>https://example.invalid/harmony</downloadUrl>
      <alternativePackageIds IgnoreIfNoMatchingField="True">
        <li>brrainz.harmony.dev</li>
      </alternativePackageIds>
    </li>
  </modDependencies>
  <modDependenciesByVersion>
    <v1.6>
      <li>
        <packageId>erdelf.humanoidalienraces</packageId>
        <displayName>Humanoid Alien Races</displayName>
      </li>
    </v1.6>
  </modDependenciesByVersion>
  <loadBefore>
    <li>CETeam.CombatExtended</li>
  </loadBefore>
  <loadBeforeByVersion>
    <v1.6>
      <li>some.mod</li>
    </v1.6>
  </loadBeforeByVersion>
  <forceLoadBefore>
    <li>forced.before</li>
  </forceLoadBefore>
  <loadAfter>
    <li>after.mod</li>
  </loadAfter>
  <loadAfterByVersion>
    <v1.5>
      <li>after.by.version</li>
    </v1.5>
  </loadAfterByVersion>
  <forceLoadAfter>
    <li>forced.after</li>
  </forceLoadAfter>
  <incompatibleWith>
    <li>bad.mod</li>
  </incompatibleWith>
  <incompatibleWithByVersion>
    <v1.6>
      <li>bad.versioned.mod</li>
    </v1.6>
  </incompatibleWithByVersion>
</ModMetaData>
""",
    )

    assert about == AboutModMetadata(
        package_id="author.mod",
        name="My Mod Name",
        authors=("Author One", "Author Two"),
        description="Description",
        supported_versions=("1.5", "1.6"),
        mod_version=AboutTextValue("1.0.0", ignore_if_no_matching_field=True),
        mod_icon_path=AboutTextValue(
            "Textures/Icon",
            ignore_if_no_matching_field=True,
        ),
        url="https://example.invalid/mod",
        descriptions_by_version=(
            VersionedDescription("v1.5", "Old description"),
            VersionedDescription("v1.6", "Current description"),
        ),
        mod_dependencies=(
            AboutDependency(
                package_id="brrainz.harmony",
                display_name="Harmony",
                steam_workshop_url="steam://url/CommunityFilePage/2009463077",
                download_url="https://example.invalid/harmony",
                alternative_package_ids=("brrainz.harmony.dev",),
                alternative_package_ids_ignore_if_no_matching_field=True,
            ),
        ),
        mod_dependencies_by_version=(
            VersionedDependencyList(
                version="v1.6",
                dependencies=(
                    AboutDependency(
                        package_id="erdelf.humanoidalienraces",
                        display_name="Humanoid Alien Races",
                    ),
                ),
            ),
        ),
        load_before=("CETeam.CombatExtended",),
        load_before_by_version=(VersionedPackageIdList("v1.6", ("some.mod",)),),
        force_load_before=("forced.before",),
        load_after=("after.mod",),
        load_after_by_version=(VersionedPackageIdList("v1.5", ("after.by.version",)),),
        force_load_after=("forced.after",),
        incompatible_with=("bad.mod",),
        incompatible_with_by_version=(
            VersionedPackageIdList("v1.6", ("bad.versioned.mod",)),
        ),
    )


def test_load_about_xml_from_path() -> None:
    about_path = Path("tests") / "__tmp_about.xml"
    try:
        _ = about_path.write_text(
            """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <description>Description</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
""",
            encoding="utf-8",
        )

        about = load_about_xml(about_path)

        assert about.package_id == "author.mod"
    finally:
        about_path.unlink(missing_ok=True)


def test_reject_invalid_root_tag() -> None:
    with pytest.raises(AboutXmlError, match="expected root tag 'ModMetaData'"):
        _ = parse_about_xml("<NotModMetaData />")


def test_accept_alternate_root_tag_casing() -> None:
    about = parse_about_xml(
        """\
<ModMetadata>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetadata>
""",
    )

    assert about.package_id == "author.mod"


def test_reject_missing_required_fields() -> None:
    with pytest.raises(AboutXmlError, match="missing required tag"):
        _ = parse_about_xml(
            """\
<ModMetaData>
  <name>My Mod Name</name>
</ModMetaData>
""",
        )


def test_parse_missing_description_as_empty_string() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
""",
    )

    assert about.description == ""


def test_parse_missing_name_from_package_id_suffix() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>Ludeon.RimWorld.Anomaly</packageId>
  <author>Ludeon Studios</author>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
""",
    )

    assert about.name == "Anomaly"


def test_parse_missing_supported_versions_as_empty_tuple() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>Ludeon.RimWorld</packageId>
  <author>Ludeon Studios</author>
</ModMetaData>
""",
    )

    assert about.name == "RimWorld"
    assert about.supported_versions == ()


def test_ignore_unknown_top_level_tags() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <steamAppId>294100</steamAppId>
</ModMetaData>
""",
    )

    assert about.package_id == "author.mod"


def test_reject_both_author_forms() -> None:
    with pytest.raises(
        AboutXmlError, match="cannot contain both 'author' and 'authors'"
    ):
        _ = parse_about_xml(
            """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <authors>
    <li>Another Author</li>
  </authors>
  <description>Description</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
""",
        )


def test_parse_empty_optional_relationship_lists() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <description>Description</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <loadAfter />
  <loadBefore />
  <forceLoadAfter />
  <forceLoadBefore />
  <incompatibleWith />
</ModMetaData>
""",
    )

    assert about.load_after == ()
    assert about.load_before == ()
    assert about.force_load_after == ()
    assert about.force_load_before == ()
    assert about.incompatible_with == ()


def test_parse_empty_optional_url_as_none() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <description>Description</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <url></url>
</ModMetaData>
""",
    )

    assert about.url is None


def test_parse_empty_description_as_empty_string() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <description></description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
""",
    )

    assert about.description == ""


def test_parse_empty_optional_dependency_fields_as_none() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <description>Description</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <modDependencies>
    <li>
      <packageId>brrainz.harmony</packageId>
      <displayName></displayName>
      <steamWorkshopUrl></steamWorkshopUrl>
      <downloadUrl></downloadUrl>
    </li>
  </modDependencies>
</ModMetaData>
""",
    )

    assert about.mod_dependencies == (AboutDependency(package_id="brrainz.harmony"),)


def test_ignore_empty_optional_versioned_sections() -> None:
    about = parse_about_xml(
        """\
<ModMetaData>
  <packageId>author.mod</packageId>
  <name>My Mod Name</name>
  <author>Author</author>
  <description>Description</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <modDependenciesByVersion>
    <v1.5></v1.5>
    <v1.6>
      <li>
        <packageId>brrainz.harmony</packageId>
      </li>
    </v1.6>
  </modDependenciesByVersion>
  <loadAfterByVersion>
    <v1.5></v1.5>
    <v1.6>
      <li>after.mod</li>
    </v1.6>
  </loadAfterByVersion>
</ModMetaData>
""",
    )

    assert about.mod_dependencies_by_version == (
        VersionedDependencyList(
            version="v1.6",
            dependencies=(AboutDependency(package_id="brrainz.harmony"),),
        ),
    )
    assert about.load_after_by_version == (
        VersionedPackageIdList("v1.6", ("after.mod",)),
    )
