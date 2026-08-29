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
- TL layer **229**. Stages 0-5 of `docs/dev/UPGRADE-PLAN.md` are done; stage 6 is partial.
- Surface: **443 public `Client` methods**, **502 types**, 43 enums, 30 handlers,
  **121 filters**, 55 `Message` members. The method, type, enum, filter and parameter gaps with
  Kurigram are closed bar the 39 noted below, 25 of which are deliberate.
- Test suite: **5066 tests** across `tests/{unit,contract,integration}/`; coverage of the
  non-generated tree gated at 58 % by a ratchet in `.coveragerc`.
- Proxies: SOCKS4/5 and HTTP through `python-socks[asyncio]`, plus Telegram's own **MTProxy**
  (plain, `dd` and `ee`/fake-TLS secrets) as a native transport. `Client(proxy=...)` takes a dict
  or a `tg://proxy` / `t.me/proxy` link.
- Hooks: `pre-commit` (style) and `pre-push` (`pytest -m "not integration"`). Ruff has `B`
  (bugbear) enabled — mutable default arguments were a recurring defect in ported code.
- Types: `ty` runs as a **ratchet**, not a gate — `make types` / `dev_tools/type_ratchet.py`.
  The count in `dev_tools/type_baseline.txt` may not grow; `pyrogram/enums` is held at zero.
  Most findings are `resolve_peer` returning a union of input peers where a raw constructor wants
  one specific kind: right at runtime, wrong in the annotations.
- Docs: `docs/source/api/**` is generated by `compiler/docs/compiler.py`, which **derives** the
  method, type and bound-method lists from the package. They used to be hand-written and drifted
  71 methods and 128 types behind. `tests/contract/test_docs_cover_the_api.py` holds the line.
- **Not published to PyPI, ever.** The distribution name is `Pyrogram` because the import name has
  to be `pyrogram`, and that name on PyPI belongs to the archived original. `pyproject.toml`
  carries the `Private :: Do Not Upload` classifier, which makes an upload fail rather than
  succeed by accident. Install from git.
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
- `test_handlers_and_decorators.py` — ties each `on_x` decorator to its `Handler` and to the
  dispatcher's routing table. A parser that raises is logged and swallowed by the handler worker,
  so a broken one shows up as "that update type never arrives", never as an error.
- `test_type_references.py` — the sibling of `test_raw_references.py` for `types.*`. It found
  eight update types the dispatcher routed into classes that did not exist, which is why
  `@on_pre_checkout_query` and seven others silently never fired.
- `test_bound_method_delegation.py` — walks every `self._client.X(...)` in the type tree and
  fails when a keyword is not in `Client.X`'s signature. It found 13 bound methods that raised
  `TypeError` on every call.
- `test_filter_update_shapes.py` — the filters name the update types that carry each field they
  read. A filter that reads a field off an update without it dies inside the handler worker.
- `test_raw_keywords.py` — every keyword handed to a `raw.*` constructor is one it has, and every
  required field is passed. It found `pin_forum_topic` sending `channel=` where the field is
  `peer`, and `send_poll` omitting `Poll.hash`, both of which raised on every call.
- `test_parameters_are_used.py` — a method may not declare a parameter its own body never reads.
  A parameter accepted and dropped is worse than a missing one: the call succeeds and the caller
  believes the option took effect.

### Not done

- **The `Client` parameter gap is closed except for what is deliberate.** `parse_mode` on
  `send_contact`/`send_dice`/`send_location`/`send_venue`/`send_video_note`/`send_media_group`/
  `send_inline_bot_result`/`copy_media_group` exists in Kurigram to parse `quote_text`, which is
  removed here; `show_caption_above_media` is expressed through
  `link_preview_options.show_above_text`, the same wire field. The remainder are client lifecycle
  differences (`run`/`start`/`stop`/`restart`/`terminate`/`on_error`/`on_raw_update`) and two
  session extras on `invoke`.
  Never re-add `reply_to_message_id`, `quote_text`, `quote_entities`, `quote_offset`,
  `reply_to_chat_id`, `reply_to_story_id` or `disable_web_page_preview`; Kurigram carries them as
  deprecated shims and they are removed here on purpose.
- **Fake-TLS (`ee`) MTProxy has never been run against a live proxy** — only against the stand-in
  in `tests/unit/connection/test_fake_tls.py`, which answers the greeting the way a real proxy
  would. Plain and `dd` secrets *are* live-verified. If an `ee` proxy is ever to hand, run it.
- **Kurigram's `web_proxy_carrier.py` is deliberately not ported.** It is the client half of their
  own WEB relay scheme, not a Telegram protocol.
