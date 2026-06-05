# Load Order Spec

## Scope

`rimpack.toposort` converts RimWorld metadata relationships into a stable package-ID order.

## Sort Item Semantics

`ToposortItem(item, before=..., after=...)` means:

- `item` must appear before every item in `before`.
- `item` must appear after every item in `after`.
- References to missing items are ignored.

Duplicate input items raise `ValueError`.

Self-cycles and graph cycles raise `CycleError`.

## Stable Ordering

`stable_toposort(items)` should preserve the original order as much as possible while satisfying dependencies.

When multiple items are ready, priority is based on original position and the earliest dependent the item directly unblocks.

## Package ID Sorting

`sort_package_ids(items)`:

- sorts case-insensitively
- preserves the original package ID casing in the returned list
- raises through `stable_toposort` when lowercased package IDs collide

`restore_original_order(original, shuffled_lower)` restores casing and duplicate order from the original list.

## RimWorld Metadata Conversion

`mod_to_sort_item(about, rimworld_version)` creates a `ToposortItem[str]` from `AboutModMetadata`.

The item is `about.package_id`.

Dependencies added to `after`:

- `modDependencies`
- matching `modDependenciesByVersion`
- `loadAfter`
- matching `loadAfterByVersion`
- `forceLoadAfter`

Dependencies added to `before`:

- `loadBefore`
- matching `loadBeforeByVersion`
- `forceLoadBefore`

Version matching uses `normalize_rimworld_version`, so `1.6.2` matches `v1.6`.

## Version Normalization

`normalize_rimworld_version(raw)`:

- ignores leading `v`
- ignores text after the first space
- keeps only major and minor version components
- returns a float like `1.6`
