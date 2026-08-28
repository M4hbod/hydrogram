# CLAUDE.md

Instructions for AI agents working in this repository. Read this before any code change.

## What this repo is

A hard fork of [Hydrogram](https://github.com/hydrogram/hydrogram) (itself a fork of the archived
[Pyrogram](https://github.com/pyrogram/pyrogram)), maintained privately by the repo owner.

**There is one working branch: `dev`.** The package directory is `pyrogram/` and the import name is
`pyrogram`. The former `pyrogram-rebrand` branch was fast-forwarded into `dev` on 2026-08-28 and
deleted; do not recreate it.

The `pyrogram` import name is deliberate — `py-tgcalls`, `pykeyboard` and other Pyrogram-only
packages import it by name. Three commits exist solely to keep those working:

- `868507da` — whole-tree `hydrogram` → `pyrogram` rename,
- `5a878348` + `a2784cb9` — `pyrogram/emoji.py`, needed by `pykeyboard`'s wildcard import,
- `f81a62a4` — `__version__` raised to `2.0.106`. `py-tgcalls` declares
  `pyrogram>=1.2.20; extra == "pyrogram"`, and Hydrogram's own `0.2.0` failed that floor. It is a
  **floor, not a ceiling** — any version `>=1.2.20` works, so this does not block a future `3.0.0`.

Do not "clean up" any of the three without checking the dependents first.

### Upstream is a different namespace

`upstream/dev` (hydrogram/hydrogram) still uses the `hydrogram` name, so a plain
`git merge upstream/dev` conflicts on essentially every file. Sync through
`dev_tools/sync_upstream.py` instead — see `docs/dev/UPGRADE-PLAN.md` § Stage 0. Never resolve a
tree-wide rename conflict by hand.

## Where the rules live

| Document | Covers |
| --- | --- |
| `AGENTS.md` | Code style, architecture patterns, method/type/filter conventions, release process |
| `docs/dev/PORTING.md` | **Mandatory** translation contract for code taken from Kurigram or any other fork |
| `docs/dev/TESTING.md` | Test layout, markers, what must be covered before a change lands |
| `docs/dev/UPGRADE-PLAN.md` | The staged layer 223 → 229 upgrade, with per-stage exit criteria |

`AGENTS.md` is the style source of truth. This file does not repeat it.

## Non-negotiables

1. **Never copy code verbatim from Kurigram.** Every ported file goes through
   `docs/dev/PORTING.md`. A file that still contains `Optional[`, `Union[`, `List[` or a quoted
   annotation has not been ported — it has been pasted.
2. **`pyrogram/raw/`, `pyrogram/errors/exceptions/` and `docs/source/api/**` are generated.**
   Edit `compiler/api/source/main_api.tl` or `compiler/errors/source/*.tsv`, then run `make api`.
   Never edit generated output.
3. **Every behaviour change needs a test.** See `docs/dev/TESTING.md`. Tests must not need network,
   credentials, or a Telegram account unless they live under `tests/integration/` and are marked.
4. **Do not run `ruff format` / `ruff check` by hand.** The pre-commit hook is installed and runs
   them (plus `detect-private-key`, `end-of-file-fixer`, `check-toml/yaml`, the NEWS-fragment name
   check) on every commit. Line length 99. If a fresh clone has no `.git/hooks/pre-commit`, run
   `uv run pre-commit install` once — that is the only manual step. `pre-commit run --all-files`
   exists for sweeping the whole tree after a large port.
5. **Public API changes need a `news/` fragment** (towncrier). See `AGENTS.md` § Release Process.
6. Keep support for Python 3.9. Kurigram targets 3.8+ with legacy typing; we target 3.9+ with
   `from __future__ import annotations`. The two are not interchangeable — see `docs/dev/PORTING.md`.
7. **Breaking API changes are allowed and are not shimmed.** The owner's own bots are the only
   consumer; a clean signature beats a compatibility tail. Announce the break in the news fragment.

## Fast commands

```bash
uv sync --all-extras --dev     # install
uv run pre-commit install      # once per clone; after this, style is automatic on commit
make api                       # regenerate raw layer + errors (required after TL edits)
uv run pytest -q               # unit tests
uv run pytest -m "not integration"   # explicitly skip live tests
uv run pre-commit run --all-files    # whole-tree sweep, e.g. after a large port
make check-api-schema          # diff local TL against Telegram's published schema
```

## Current state (2026-08-28)

- Branch `dev` @ `fe2caeff`, package `pyrogram`, `__version__` `2.0.106`.
- TL layer: **223**. Target: **229**.
- High-level surface: 211 method files / 121 type files / 16 enums.
  Kurigram at layer 229 has 407 / 308 / 44.
- Test suite: 39 tests across 3 files. This is the first thing being fixed.
- Pre-commit hook installed 2026-08-28; it reformatted 5 files that had been failing
  `code-style.yml` on `dev`. No commit since 2026-04-10 had been CI-verified.
- `make api` on Kurigram's layer-229 TL was verified to compile and import cleanly with this
  repo's compiler; only 19 high-level `raw.*` references break. See `docs/dev/UPGRADE-PLAN.md`.
