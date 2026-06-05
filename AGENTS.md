# AGENTS.md

Guidance for coding agents working in this repository.

## Project Overview

RimPack is a Python 3.12 command-line mod manager for RimWorld. Its primary product goal is to make modpacks easy to store in git, review in diffs, edit by hand, and compose from small modular files.

Core design constraints:

- Modpack files are YAML files.
- Modpack files should stay small and human-readable.
- Modpacks should be modular; prefer multiple focused files over one generated blob.
- CLI commands that edit YAML should preserve formatting, comments, key order, and quoting when practical.
- Generated files should be deterministic so git diffs stay meaningful.

The current code focuses on:

- reading and writing RimPack config files
- initializing a modpack skeleton from installed RimWorld DLC metadata
- parsing RimWorld `About.xml` mod metadata
- representing and editing YAML mod lists
- resolving Steam Workshop items into local mod folders
- sorting package IDs from RimWorld load-order relationships

The package entry point is `rimpack = "rimpack.main:main"`.

## Repository Layout

- `rimpack/main.py`: Typer CLI commands.
- `rimpack/config.py`: TOML config model and Steam/RimWorld path discovery helpers.
- `rimpack/parsers/config.py`: YAML config parser currently used by the active CLI.
- `rimpack/mod/about.py`: `About.xml` parser and metadata dataclasses.
- `rimpack/mod/modfolder.py`: mod-folder validation and loading.
- `rimpack/listfile.py`: YAML mod-list model and immutable edit helpers.
- `rimpack/toposort.py`: stable dependency-aware sorting for package IDs.
- `rimpack/steamworks.py`: Steamworks client wrapper and Workshop resolution.
- `tests/`: pytest suite and fixture data.
- `specs/`: lightweight behavior specs for current code.

## Development Commands

Use `uv` for local development:

```powershell
uv sync --dev
uv run pytest
uv run ruff check .
uv run basedpyright
```

Run the CLI through the installed script or module path:

```powershell
uv run rimpack --help
uv run rimpack create-config
uv run rimpack init
```

In the Codex sandbox, `uv run rimpack ...` may fail with an access-denied error while opening uv's user cache, for example `C:\Users\lai\AppData\Local\uv\cache\sdists-v9\.git`. If that happens, rerun the same command with normal shell permissions; this is a sandbox/cache access issue, not a RimPack CLI failure.

## Coding Conventions

- Target Python 3.12 or newer.
- Prefer dataclasses for small immutable domain records when that matches existing code.
- Keep file path handling on `pathlib.Path`.
- Preserve YAML comments/formatting with `ruamel.yaml` when editing YAML-backed files.
- Do not introduce TOML, JSON, or generated binary formats for modpack state.
- Keep environment or machine-local config separate from git-tracked modpack files.
- Keep pure parsing/sorting logic independent of Steam, filesystem, and CLI prompts.
- Raise domain exceptions from `rimpack.exceptions` for expected validation failures.
- Add focused pytest coverage for new behavior and regression fixes.

## Current Stability Notes

- `rimpack.main` currently writes and reads YAML config files named `config.yml` through `rimpack.parsers.config.Config`.
- `rimpack.config.Config` is a separate TOML-backed config model with disabled tests in `tests/_test_config.py`.
- Treat the TOML-backed config path as legacy or unsettled until the config format is decided; do not use it as precedent for modpack files.
- Some APIs are skeletal or incomplete, including parts of `rimpack.resolve`, `rimpack.packfile`, and `rimpack.parsers.module`.
- Some old tests are disabled by leading underscores. Do not assume disabled tests describe the active CLI contract unless you reactivate or update them deliberately.

## Test Guidance

- For CLI behavior, use `typer.testing.CliRunner`.
- For filesystem behavior, use `tmp_path` and fixtures from `tests/conftest.py`.
- For mod metadata, prefer compact inline XML in tests unless fixture data is specifically needed.
- For Steam Workshop resolution, fake the Steamworks object rather than requiring Steam or network access.
- For order-sensitive behavior, assert exact output order.
- For CLI tests that edit modpack content, set up a real modpack shape with `pack.yml` and module files under `modules/`; do not use loose module/list YAML files in the cwd unless the behavior explicitly targets loose files.
- After changing Python code or tests, run focused `ruff` and `basedpyright` checks on the touched files in addition to any focused pytest run.

## Specs

Behavior specs live in `specs/`:

- `specs/cli-config.md`
- `specs/modpack-format.md`
- `specs/about-xml.md`
- `specs/mod-list.md`
- `specs/load-order.md`
- `specs/steam-workshop.md`

When behavior changes, update the nearest spec in the same change as the code and tests.
