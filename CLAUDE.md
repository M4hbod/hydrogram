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
- `f81a62a4` — `__version__` was raised past the `py-tgcalls` floor. That package declares
  `pyrogram>=1.2.20; extra == "pyrogram"`, and Hydrogram's own `0.2.0` failed it. It is a **floor,
  not a ceiling**, so the version is now `3.0.0` and no longer pinned. Keep it `>=1.2.20`.

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

## Current state (2026-08-29)

- Branch `dev`, package `pyrogram`, `__version__` `3.0.0`.
- TL layer **229**. Stages 0-4 of `docs/dev/UPGRADE-PLAN.md` are done; stage 5 is not (see below).
- Surface: **441 public `Client` methods**, 431 method modules, 222 type modules, 43 enums,
  30 handlers. The method gap with Kurigram is closed.
- Test suite: **2946 tests** across `tests/{unit,contract,integration}/`; coverage of the
  non-generated tree gated at 55 % by a ratchet in `.coveragerc`.
- Hooks: `pre-commit` (style) and `pre-push` (`pytest -m "not integration"`). Ruff has `B`
  (bugbear) enabled — mutable default arguments were a recurring defect in ported code.
- `make sync-upstream` replays upstream Hydrogram commits through the namespace rename.
- When checking CI, always pass `-R M4hbod/hydrogram` to `gh` — with two remotes it resolves to
  `hydrogram/hydrogram` and reports upstream's failures as if they were ours.

### Contract tests worth knowing about

These encode the porting hazards that actually bit, and they are cheap to run:

- `test_await_consistency.py` — many `_parse` methods are **async in Kurigram and sync here**.
  Ported code arrives with the wrong `await`, which only fails when that branch runs. It found 44.
- `test_removed_parameters.py` — `reply_to_message_id` and `disable_web_page_preview` were removed
  outright; ported methods keep bringing them back.
- `test_raw_references.py` — every `raw.*` name resolves in the compiled layer.
- `test_rpc_construction.py` — drives methods with a recording client, so a renamed constructor
  fails offline instead of on a live call.

### Not done

- **Stage 5 (MTProxy / fake-TLS transports).** Attempted and reverted. Kurigram's `Connection`
  takes a resolved `server_address`/`port` where ours takes `ipv6`, so adopting it means porting
  `session.py` and `auth.py` too — both carrying local fixes — and there is no way to verify a
  proxy transport without a proxy to test against. The working transport was kept.
- **`advanced/recover_gaps`.** Needs an `update_state` table in SQLite storage, its accessors, and
  a migration for existing session files. A storage schema change, not a method port.
