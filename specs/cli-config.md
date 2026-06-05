# CLI And Config Spec

## Scope

This spec describes the active CLI behavior in `rimpack.main` and the YAML config parser used by that CLI.

All git-tracked modpack files created by CLI commands must follow `specs/modpack-format.md`.

## Commands

### `rimpack create-config`

Creates the default RimPack config file at:

```text
<platform user config dir>/rimpack/config.yml
```

Behavior:

- If the file already exists, print a message and leave it unchanged.
- Detect Steam root with `find_steam_root()`.
- Prompt for `RimWorld root` and `RimWorld workshop root`.
- Use detected defaults when available.
- Write YAML with:
  - `rimworld_root`
  - `workshop_root`

The active tests monkeypatch path discovery and verify that existing configs are not overwritten.

### `rimpack init`

Initializes a modpack skeleton in the current working directory.

Behavior:

- Read `config.yml` from the default RimPack config directory.
- If the config file is missing, print a friendly error and exit with status `1`.
- Detect DLCs by scanning `<rimworld_root>/Data/*/About/About.xml`.
- Parse each DLC `About.xml`.
- Convert DLC metadata to load-order sort items for RimWorld `1.6`.
- Sort package IDs with `sort_package_ids`.
- Create:
  - `pack.yml`
  - `modules/00_ludeon.yml`
  - `modules/10_core.yml`
- `pack.yml` should reference `modules/00_ludeon.yml` and `modules/10_core.yml` in that order.
- `00_ludeon.yml` should contain one `{pid: ...}` entry per detected DLC package ID.
- `10_core.yml` is currently a comment-only placeholder and loads as YAML `None`.
- Generated files should be deterministic, small, YAML-only, and safe to commit.
- The command should not embed absolute local Steam/RimWorld paths in modpack files.

## CLI Editing Principles

Future CLI commands that edit modpack files should:

- preserve comments and formatting when possible
- preserve unrelated ordering and content
- change the smallest practical YAML subtree
- keep files human-readable after repeated edits

## YAML Config Parser

`rimpack.parsers.config.Config` supports:

- `rimworld_root: Path | None`
- `workshop_root: Path | None`
- `Config.from_file(path)`
- `Config.parse(source)`

It uses `ruamel.yaml` and `typedload`.

## Known Gaps

- `rimpack.config.Config` is TOML-backed and separate from the YAML parser used by the active CLI.
- `Config.get_default_config_path()` in `rimpack.config` points to `config.toml`, while `rimpack.main` currently uses `config.yml`.
- Decide on one machine-local config format before expanding CLI features.
- Do not use the TOML-backed config model as precedent for git-tracked modpack files; modpack files are YAML.
