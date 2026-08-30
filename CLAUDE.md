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
  not a ceiling**, so the version is now `3.2.3` and no longer pinned. Keep it `>=1.2.20`.

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

## Current state (2026-08-30)

- Branch `dev`, package `pyrogram`, `__version__` `3.2.3`.
- TL layer **229**. Every stage of `docs/dev/UPGRADE-PLAN.md` is done.
- Surface: **445 public `Client` methods**, **397 types**, 43 enums, 30 handlers,
  **121 filters**, 55 `Message` members. Every gap with Kurigram — methods, types, enums,
  filters, bound methods and parameters — is closed except what is deliberate (see below).
- Test suite: **5865 tests** across `tests/{unit,contract,integration}/`; coverage of the
  non-generated tree gated at 62 % by a ratchet in `.coveragerc`.
- Proxies: SOCKS4/5 and HTTP through `python-socks[asyncio]`, plus Telegram's own **MTProxy**
  (plain, `dd` and `ee`/fake-TLS secrets) as a native transport. `Client(proxy=...)` takes a dict
  or a `tg://proxy` / `t.me/proxy` link.
- Hooks: `pre-commit` (style) and `pre-push` (`pytest -m "not integration"`). Ruff has `B`
  (bugbear) enabled — mutable default arguments were a recurring defect in ported code.
- Types: `ty` runs as a **ratchet**, not a gate — `make types` / `dev_tools/type_ratchet.py`.
  The count in `dev_tools/type_baseline.txt` may not grow; `pyrogram/enums` is held at zero.
  Most findings are `resolve_peer` returning a union of input peers where a raw constructor wants
  one specific kind: right at runtime, wrong in the annotations. The other big share is
  structural: every `pyrogram/raw/base/*.py` defines `X = Union[...]` and then a `class X` that
  **shadows it**, so `raw.base.X` is a marker class raising `TypeError` on construction, not the
  union it documents. No constructor is an instance of it, so annotating a return with one is
  simply wrong — leave such returns to inference. Fixing this properly means changing
  `compiler/api/compiler.py`, which would drop findings tree-wide.
- Docs: `docs/source/api/**` is generated by `compiler/docs/compiler.py`, which **derives** the
  method, type and bound-method lists from the package. They used to be hand-written and drifted
  71 methods and 128 types behind. `tests/contract/test_docs_cover_the_api.py` holds the line.
- **Not published to PyPI, ever.** The distribution name is `Pyrogram` because the import name has
  to be `pyrogram`, and that name on PyPI belongs to the archived original. `pyproject.toml`
  carries the `Private :: Do Not Upload` classifier, which makes an upload fail rather than
  succeed by accident. Install from git.
- Rich messages send in both forms: `InputRichMessage(html=)`/`(markdown=)` for the thin
  text-only variant, and `InputRichMessage(blocks=)` for the structured one — tables, checklists
  (a `PageBlockList` whose items carry `checkbox`/`checked`; there is **no** checklist type in
  layer 229), collapsible sections, headings, anchors, nested quotations, collages, math, media.
  The send side reuses the read side's `RichBlock`/`RichText` classes through a single `_write`
  dispatcher mirroring `_parse`, so there is no parallel input hierarchy to drift.
  **The block path has never been run against a live server** — only round-tripped offline through
  our own parser. `tests/integration/test_send_rich_message_blocks.py` is the test to run when
  credentials are to hand.
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
- `test_every_method_builds_a_request.py` — calls 211 client methods and asserts each reaches a
  request. It stops at `invoke` rather than parsing a reply, which is what the older harness could
  not do: 75 methods skipped there as "needs more client than the stub provides", and a method
  that skips is one nobody has run. It found nine that raised on every call.
- `test_type_fields.py` — every type's fields against a Kurigram checkout (`KURIGRAM_PATH`).
  The parity checks before it compared **names**, so `Chat` counted as closed while missing 118
  fields and `User` 76. A name being present is not the same as it being right.
- `test_attribute_references.py` — every `raw.*`, `types.*`, `enums.*` chain resolves, at any
  depth, including enum members. `test_raw_references.py` only resolved the namespaces it knew,
  so `raw.pyrogram.ClientDHInnerData` never entered the checked set and broke every fresh login
  across 3.0.0 and 3.1.0. Docstrings count; `#` comments do not.
- `test_call_arity.py` — the positional count and keyword names of every
  `types.X.method(...)` call against the target's signature. `dispatcher.py` passed four
  arguments to a three-argument `CallbackQuery._parse`, so every inline-keyboard button press
  raised `TypeError` inside the handler worker and did nothing visible.
- `test_optional_raw_fields_are_guarded.py` — two schema checks, both for defects that raise
  inside a parser. First: no parser may iterate a raw field the schema marks optional, because
  an optional `Vector` arrives as `None` and Kurigram's parsers assume `[]`. Second: no parser
  may read a field no constructor its annotated input can hold declares, narrowing through
  `isinstance` on both arms. Between them they found `Thumbnail._parse` on every document
  without a thumbnail, `ChatPreview._parse` on every invite without a member preview, and
  `ForumTopicCreated._parse` on anything but a service message. Note that a **wrong annotation
  makes both checks pass vacuously**, so two were corrected as findings in their own right;
  the analysed-function floor exists for the same reason.
- `test_dispatcher_parsers.py` (unit, not contract) — builds a minimal live-shape fixture for
  every routed update type and asserts it parses. `test_every_routed_update_kind_has_a_test_here`
  greps the dispatcher's routing table and fails when a routed type has no fixture, which is the
  only reason the gaps got closed rather than found one production outage at a time.

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
