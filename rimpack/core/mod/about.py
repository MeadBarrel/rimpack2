from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from rimpack.core.exceptions import AboutXmlError as AboutXmlError


@dataclass(frozen=True)
class AboutTextValue:
    value: str
    ignore_if_no_matching_field: bool = False


@dataclass(frozen=True)
class AboutDependency:
    package_id: str
    display_name: str | None = None
    steam_workshop_url: str | None = None
    download_url: str | None = None
    alternative_package_ids: tuple[str, ...] = ()
    alternative_package_ids_ignore_if_no_matching_field: bool = False


@dataclass(frozen=True)
class VersionedDescription:
    version: str
    description: str


@dataclass(frozen=True)
class VersionedDependencyList:
    version: str
    dependencies: tuple[AboutDependency, ...]


@dataclass(frozen=True)
class VersionedPackageIdList:
    version: str
    package_ids: tuple[str, ...]


@dataclass(frozen=True)
class AboutModMetadata:
    package_id: str
    name: str
    authors: tuple[str, ...]
    description: str
    supported_versions: tuple[str, ...]
    mod_version: AboutTextValue | None = None
    mod_icon_path: AboutTextValue | None = None
    url: str | None = None
    descriptions_by_version: tuple[VersionedDescription, ...] = ()
    mod_dependencies: tuple[AboutDependency, ...] = ()
    mod_dependencies_by_version: tuple[VersionedDependencyList, ...] = ()
    load_before: tuple[str, ...] = ()
    load_before_by_version: tuple[VersionedPackageIdList, ...] = ()
    force_load_before: tuple[str, ...] = ()
    load_after: tuple[str, ...] = ()
    load_after_by_version: tuple[VersionedPackageIdList, ...] = ()
    force_load_after: tuple[str, ...] = ()
    incompatible_with: tuple[str, ...] = ()
    incompatible_with_by_version: tuple[VersionedPackageIdList, ...] = ()


def parse_about_xml(xml_text: str) -> AboutModMetadata:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise AboutXmlError(f"invalid XML: {exc}") from exc

    if root.tag not in {"ModMetaData", "ModMetadata"}:
        raise AboutXmlError(
            f"expected root tag 'ModMetaData', found {root.tag!r}",
        )

    scalar_values: dict[str, str] = {}
    authors_from_scalar: tuple[str, ...] | None = None
    authors_from_list: tuple[str, ...] | None = None
    supported_versions: tuple[str, ...] | None = None
    mod_version: AboutTextValue | None = None
    mod_icon_path: AboutTextValue | None = None
    descriptions_by_version: tuple[VersionedDescription, ...] = ()
    mod_dependencies: tuple[AboutDependency, ...] = ()
    mod_dependencies_by_version: tuple[VersionedDependencyList, ...] = ()
    load_before: tuple[str, ...] = ()
    load_before_by_version: tuple[VersionedPackageIdList, ...] = ()
    force_load_before: tuple[str, ...] = ()
    load_after: tuple[str, ...] = ()
    load_after_by_version: tuple[VersionedPackageIdList, ...] = ()
    force_load_after: tuple[str, ...] = ()
    incompatible_with: tuple[str, ...] = ()
    incompatible_with_by_version: tuple[VersionedPackageIdList, ...] = ()

    seen_children: set[str] = set()

    for child in root:
        if child.tag in seen_children and child.tag not in {
            "author",
            "authors",
        }:
            raise AboutXmlError(f"duplicate top-level tag {child.tag!r}")
        seen_children.add(child.tag)

        match child.tag:
            case "packageId" | "name":
                scalar_values[child.tag] = _parse_text_node(child)
            case "description":
                scalar_values[child.tag] = _parse_optional_text_node(child) or ""
            case "url":
                url = _parse_optional_text_node(child)
                if url is not None:
                    scalar_values[child.tag] = url
            case "author":
                if authors_from_scalar is not None:
                    raise AboutXmlError("duplicate top-level tag 'author'")
                authors_from_scalar = _parse_author_text(child)
            case "authors":
                if authors_from_list is not None:
                    raise AboutXmlError("duplicate top-level tag 'authors'")
                authors_from_list = _parse_string_list(child)
            case "supportedVersions":
                supported_versions = _parse_string_list(child)
            case "modVersion":
                mod_version = _parse_optional_text_value(child)
            case "modIconPath":
                mod_icon_path = _parse_optional_text_value(child)
            case "descriptionsByVersion":
                descriptions_by_version = _parse_descriptions_by_version(child)
            case "modDependencies":
                mod_dependencies = _parse_dependency_list(child, allow_empty=True)
            case "modDependenciesByVersion":
                mod_dependencies_by_version = _parse_versioned_dependencies(child)
            case "loadBefore":
                load_before = _parse_string_list(child, allow_empty=True)
            case "loadBeforeByVersion":
                load_before_by_version = _parse_versioned_package_ids(child)
            case "forceLoadBefore":
                force_load_before = _parse_string_list(child, allow_empty=True)
            case "loadAfter":
                load_after = _parse_string_list(child, allow_empty=True)
            case "loadAfterByVersion":
                load_after_by_version = _parse_versioned_package_ids(child)
            case "forceLoadAfter":
                force_load_after = _parse_string_list(child, allow_empty=True)
            case "incompatibleWith":
                incompatible_with = _parse_string_list(child, allow_empty=True)
            case "incompatibleWithByVersion":
                incompatible_with_by_version = _parse_versioned_package_ids(child)
            case _:
                continue

    if authors_from_scalar is not None and authors_from_list is not None:
        raise AboutXmlError("About.xml cannot contain both 'author' and 'authors'")

    authors = authors_from_scalar or authors_from_list
    if authors is None:
        raise AboutXmlError("missing required tag 'author' or 'authors'")

    missing_scalar_tags: list[str] = []
    if "packageId" not in scalar_values:
        missing_scalar_tags.append("packageId")
    if missing_scalar_tags:
        missing_list = ", ".join(repr(tag) for tag in missing_scalar_tags)
        raise AboutXmlError(f"missing required tag(s): {missing_list}")

    package_id = scalar_values["packageId"]
    resolved_name = scalar_values.get("name", _derive_name_from_package_id(package_id))
    resolved_supported_versions = supported_versions or ()

    return AboutModMetadata(
        package_id=package_id,
        name=resolved_name,
        authors=authors,
        description=scalar_values.get("description", ""),
        supported_versions=resolved_supported_versions,
        mod_version=mod_version,
        mod_icon_path=mod_icon_path,
        url=scalar_values.get("url"),
        descriptions_by_version=descriptions_by_version,
        mod_dependencies=mod_dependencies,
        mod_dependencies_by_version=mod_dependencies_by_version,
        load_before=load_before,
        load_before_by_version=load_before_by_version,
        force_load_before=force_load_before,
        load_after=load_after,
        load_after_by_version=load_after_by_version,
        force_load_after=force_load_after,
        incompatible_with=incompatible_with,
        incompatible_with_by_version=incompatible_with_by_version,
    )


def load_about_xml(path: Path) -> AboutModMetadata:
    return parse_about_xml(path.read_text(encoding="utf-8"))


def _parse_text_node(element: ElementTree.Element) -> str:
    if list(element):
        raise AboutXmlError(f"tag {element.tag!r} must not contain child elements")
    text = (element.text or "").strip()
    if not text:
        raise AboutXmlError(f"tag {element.tag!r} must not be empty")
    return text


def _parse_optional_text_node(element: ElementTree.Element) -> str | None:
    if list(element):
        raise AboutXmlError(f"tag {element.tag!r} must not contain child elements")
    text = (element.text or "").strip()
    return text or None


def _parse_author_text(element: ElementTree.Element) -> tuple[str, ...]:
    author_text = _parse_text_node(element)
    authors = tuple(part.strip() for part in author_text.split(",") if part.strip())
    if not authors:
        raise AboutXmlError("tag 'author' must contain at least one author")
    return authors


def _derive_name_from_package_id(package_id: str) -> str:
    return package_id.rsplit(".", maxsplit=1)[-1]


def _parse_string_list(
    element: ElementTree.Element,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    values: list[str] = []
    for child in element:
        if child.tag != "li":
            raise AboutXmlError(
                f"tag {element.tag!r} must only contain 'li' elements",
            )
        value = _parse_optional_text_node(child)
        if value is None:
            if allow_empty:
                continue
            raise AboutXmlError(f"tag {child.tag!r} must not be empty")
        values.append(value)
    if not values and not allow_empty:
        raise AboutXmlError(f"tag {element.tag!r} must contain at least one entry")
    return tuple(values)


def _parse_optional_text_value(element: ElementTree.Element) -> AboutTextValue | None:
    value = _parse_optional_text_node(element)
    if value is None:
        return None
    return AboutTextValue(
        value=value,
        ignore_if_no_matching_field=_parse_bool_attr(
            element,
            "IgnoreIfNoMatchingField",
        ),
    )


def _parse_bool_attr(element: ElementTree.Element, name: str) -> bool:
    raw_value = element.get(name)
    if raw_value is None:
        return False
    if raw_value == "True":
        return True
    if raw_value == "False":
        return False
    raise AboutXmlError(
        f"attribute {name!r} on tag {element.tag!r} must be 'True' or 'False'",
    )


def _parse_descriptions_by_version(
    element: ElementTree.Element,
) -> tuple[VersionedDescription, ...]:
    items: list[VersionedDescription] = []
    for child in element:
        items.append(
            VersionedDescription(
                version=child.tag,
                description=_parse_text_node(child),
            ),
        )
    if not items:
        raise AboutXmlError(
            "tag 'descriptionsByVersion' must contain at least one entry"
        )
    return tuple(items)


def _parse_dependency_list(
    element: ElementTree.Element,
    *,
    allow_empty: bool = False,
) -> tuple[AboutDependency, ...]:
    dependencies: list[AboutDependency] = []
    for child in element:
        if child.tag != "li":
            raise AboutXmlError(
                f"tag {element.tag!r} must only contain 'li' elements",
            )
        dependencies.append(_parse_dependency(child))
    if not dependencies and not allow_empty:
        raise AboutXmlError(f"tag {element.tag!r} must contain at least one entry")
    return tuple(dependencies)


def _parse_dependency(element: ElementTree.Element) -> AboutDependency:
    package_id: str | None = None
    display_name: str | None = None
    steam_workshop_url: str | None = None
    download_url: str | None = None
    alternative_package_ids: tuple[str, ...] = ()
    alternative_package_ids_ignore_if_no_matching_field = False

    for child in element:
        if child.tag == "packageId":
            package_id = _parse_text_node(child)
        elif child.tag == "displayName":
            display_name = _parse_optional_text_node(child)
        elif child.tag == "steamWorkshopUrl":
            steam_workshop_url = _parse_optional_text_node(child)
        elif child.tag == "downloadUrl":
            download_url = _parse_optional_text_node(child)
        elif child.tag == "alternativePackageIds":
            alternative_package_ids = _parse_string_list(child)
            alternative_package_ids_ignore_if_no_matching_field = _parse_bool_attr(
                child,
                "IgnoreIfNoMatchingField",
            )
        else:
            raise AboutXmlError(
                f"unsupported dependency tag {child.tag!r} in 'modDependencies'",
            )

    if package_id is None:
        raise AboutXmlError("dependency entry is missing required tag 'packageId'")

    return AboutDependency(
        package_id=package_id,
        display_name=display_name,
        steam_workshop_url=steam_workshop_url,
        download_url=download_url,
        alternative_package_ids=alternative_package_ids,
        alternative_package_ids_ignore_if_no_matching_field=(
            alternative_package_ids_ignore_if_no_matching_field
        ),
    )


def _parse_versioned_dependencies(
    element: ElementTree.Element,
) -> tuple[VersionedDependencyList, ...]:
    groups: list[VersionedDependencyList] = []
    for child in element:
        dependencies = _parse_dependency_list(child, allow_empty=True)
        if not dependencies:
            continue
        groups.append(
            VersionedDependencyList(
                version=child.tag,
                dependencies=dependencies,
            ),
        )
    return tuple(groups)


def _parse_versioned_package_ids(
    element: ElementTree.Element,
) -> tuple[VersionedPackageIdList, ...]:
    groups: list[VersionedPackageIdList] = []
    for child in element:
        package_ids = _parse_string_list(child, allow_empty=True)
        if not package_ids:
            continue
        groups.append(
            VersionedPackageIdList(
                version=child.tag,
                package_ids=package_ids,
            ),
        )
    return tuple(groups)
