# Modpack Format Spec

## Product Intent

RimPack modpacks are meant to be stored in git. A modpack should be easy to inspect, review, merge, and edit without running RimPack.

The file format should optimize for:

- small repository size
- readable diffs
- deterministic generated output
- hand-editable text
- modular composition
- preservation of user comments and formatting where possible

## File Format

All git-tracked modpack files are YAML.

Do not introduce TOML, JSON, SQLite, binary lock files, generated archives, or opaque serialized data for modpack state unless a future spec explicitly carves out a non-modpack cache artifact.

Machine-local configuration may live outside the modpack repository, but it must not become part of the git-tracked modpack format.

## Modularity

Prefer a small root file that references focused module files.

Current initialized shape:

```text
pack.yml
modules/
  00_ludeon.yml
  10_core.yml
```

Expected properties:

- `pack.yml` declares module file paths.
- Module files contain related mod references.
- File names should sort in load/order intent where practical.
- Large generated single-file modpacks should be avoided.

## Human Editing

Users should be able to add, remove, reorder, and annotate mods directly in YAML.

Formats should favor explicit field names over compact encodings. Prefer:

```yaml
- pid: brrainz.harmony
  name: Harmony
  after:
    - pid: ludeon.rimworld
```

Avoid forms that require hidden indexes, generated IDs, or positional meaning outside normal YAML sequences.

## CLI Editing

CLI commands that modify modpack YAML should:

- parse and write with `ruamel.yaml` or another comment-preserving structured YAML API
- preserve comments, quoting, and ordering when possible
- make the smallest practical edit
- avoid rewriting unrelated files
- avoid reformatting entire files for a single logical change
- produce stable output across repeated runs

When formatting cannot be preserved, the command should still keep output readable and deterministic.

## Generated Content

Generated modpack files should be useful starting points, not opaque build artifacts.

Generated files should:

- include only data required by RimPack or useful to humans
- avoid embedding absolute machine-local paths
- avoid embedding transient Steam or filesystem state unless explicitly part of the modpack contract
- be safe to commit to git

## Open Questions

- Whether machine-local RimWorld/Steam paths should remain YAML config, migrate from the legacy TOML model, or be handled through environment variables.
- Whether a future lock file is needed for exact Workshop item versions. If added, it should still be YAML, deterministic, reviewable, and as small as practical.
