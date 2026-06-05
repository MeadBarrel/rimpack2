# About.xml Spec

## Scope

`rimpack.mod.about` parses RimWorld mod metadata from `About.xml` into immutable dataclasses.

## Accepted Roots

The parser accepts either root tag:

- `ModMetaData`
- `ModMetadata`

Any other root raises `AboutXmlError`.

## Required Fields

Required:

- `packageId`
- one of `author` or `authors`

Optional:

- `name`, derived from the package ID suffix when absent
- `description`, defaulting to an empty string when absent or empty
- `supportedVersions`, defaulting to an empty tuple when absent

The parser rejects files containing both `author` and `authors`.

## Authors

`author` is parsed as comma-separated text.

`authors` is parsed as a list of `li` elements.

Both forms produce `tuple[str, ...]`.

## Optional Metadata

Supported optional sections include:

- `modVersion`
- `modIconPath`
- `url`
- `descriptionsByVersion`
- `modDependencies`
- `modDependenciesByVersion`
- `loadBefore`
- `loadBeforeByVersion`
- `forceLoadBefore`
- `loadAfter`
- `loadAfterByVersion`
- `forceLoadAfter`
- `incompatibleWith`
- `incompatibleWithByVersion`

Unknown top-level tags are ignored.

## Dependency Entries

Each `modDependencies/li` entry requires `packageId`.

Optional dependency fields:

- `displayName`
- `steamWorkshopUrl`
- `downloadUrl`
- `alternativePackageIds`

Empty optional dependency fields are parsed as `None`.

## Versioned Sections

Versioned sections use the child tag name as the version key, for example `v1.6`.

Empty optional versioned entries are ignored for:

- `modDependenciesByVersion`
- `loadAfterByVersion`
- related versioned package-id sections

## Validation

The parser raises `AboutXmlError` for:

- invalid XML
- unsupported root tags
- duplicate top-level tags, except the accepted author forms are handled specially
- required text tags with child elements
- required text tags that are empty
- list tags containing non-`li` children
- boolean attributes other than `True` or `False`
- unsupported dependency child tags

## Filesystem Loader

`load_about_xml(path)` reads UTF-8 text and delegates to `parse_about_xml`.
