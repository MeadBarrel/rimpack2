# Mod List Spec

## Scope

`rimpack.listfile.ModList` represents a YAML file containing named packs and mod records.

Mod lists are git-tracked modpack files and must follow `specs/modpack-format.md`.

## Data Shape

Top-level YAML keys are pack names. Each pack contains a sequence of mod records.

Supported mod reference forms:

```yaml
core:
  - pid: ludeon.rimworld
  - wid: 123456789
  - loc: LocalFolderName
```

Optional record fields:

- `name`
- `before`
- `after`

`before` and `after` contain reference objects with the same supported reference forms.

Records should remain compact but explicit. Prefer adding optional fields only when they help users understand or control the modpack.

## Reference Identity

References match when both fields match:

- `kind`: `pid`, `wid`, or `loc`
- `reference`: string representation of the package ID, Workshop ID, or local folder

## Loading And Dumping

`ModList.load(path)`:

- reads UTF-8 YAML
- preserves source comments/formatting through `ruamel.yaml`
- validates into typed records with `typedload`

`ModList.dump(path)`:

- writes YAML using 2-space mappings and indented sequences
- preserves quotes and comments carried in the backing source where possible

CLI flows using `ModList` should avoid unrelated rewrites and preserve comments around packs and records when practical.

## Immutable Edits

`ModList` edit methods return a new `ModList` instance and do not mutate the original.

Supported edits:

- `with_added_pack(pack, comment=None)`
- `with_added_mod(pack, record, comment=None)`
- `with_removed_mod(reference, comment=None)`

## Errors

Expected validation errors are raised from `rimpack.exceptions`:

- `ModListPackAlreadyExistsError`
- `ModListPackDoesNotExistError`
- `ModListModAlreadyExistsError`
- `ModListModDoesNotExistError`

## Current Test Gap

There is currently no active `tests/test_listfile.py` in the repository. Add focused tests before changing this behavior.
