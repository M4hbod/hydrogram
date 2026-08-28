# Upgrade plan: layer 223 → 229, production-ready

Written 2026-08-28. Every number here was measured against this working tree, not estimated.

## Where we are

| | This repo | Kurigram `dev` (2.2.25) |
| --- | --- | --- |
| TL layer | 223 | 229 |
| Method files | 211 | 407 |
| Type files | 121 | 308 |
| Enum modules | 16 | 44 |
| Test files | 3 (39 tests) | 18 |
| Typing style | `__future__` annotations, PEP 604/585 | `typing.Optional/Union/List`, quoted |
| Python floor | 3.9 | 3.8 |
| Last upstream sync | `upstream/dev` @ `edb10c60` | — |

Branch `dev` @ `fe2caeff`, 14 commits ahead of `upstream/dev`. Load-bearing ones:
`28cd61aa` (custom-emoji + coloured keyboard buttons), `fe2caeff` (document-less `WallPaperNoFile`),
and the namespace stack (`868507da` rename, `5a878348` + `a2784cb9` `emoji.py`, `f81a62a4` version
pin). `pyrogram-rebrand` was merged into `dev` and deleted on 2026-08-28 — one branch from here on.

## Feasibility findings (measured, not assumed)

These were established by trial-compiling Kurigram's layer-229 `main_api.tl` with **this repo's**
compiler:

1. **The compiler handles layer 229 unchanged.** `make api` succeeded, `raw.all.layer == 229`,
   `import pyrogram` clean, existing 39 tests still green. The 528-line diff between the two
   `compiler/api/compiler.py` files is cosmetic/style, not capability.
2. **Only 19 high-level `raw.*` references break** under 229:
   - `raw.functions.channels.{CreateForumTopic, EditForumTopic, GetForumTopics, GetForumTopicsByID, DeleteTopicHistory, EditCreator}` — forum topic functions moved to the `messages.*` namespace.
   - 12 keyboard-button constructors — the `ButtonType` redesign (see below).
   - `raw.types.Wallpaper` in `types/user_and_chats/chat_background.py:94` — a pre-existing typo
     (`WallPaper` is the real name), latent only because annotations are lazy.
3. **Keyboards are the one genuinely hard change.** Layer 223 has 18 flat `= KeyboardButton;`
   constructors; layer 229 has 2, discriminated by `ButtonType` / `InlineButtonType`. Our
   custom-emoji/style feature is built on the flat shape. `style:flags.10?KeyboardButtonStyle`
   survives on the outer `keyboardButton`, so the feature is portable — but the code is a rewrite.
4. **TL delta is 240 new constructors, 72 changed.** Large but mechanical; the compiler absorbs it.
5. **The API-surface gap is the real work**, not the layer. 221 method files and 214 type files
   exist in Kurigram and not here: gifts/stars (44 methods), stories (21), business (5), payments,
   folders, checklists, suggested posts, web apps, privacy/account settings.

6. **Nothing has been CI-verified since 2026-04-10.** The last successful `Check style` run on
   `origin` is `edb10c60` (an upstream commit). None of the local work — the rename stack, the
   keyboard feature, the `WallPaperNoFile` fix — has been through CI, and `dev` was in fact
   failing `ruff format --check` on 5 files until 2026-08-28. Only the daily
   `Check MTProto API Schema Updates` job has been running, and it has been failing every day.
   Restoring a green pipeline is stage-0 work, not stage-6 polish.

Conclusion: **the layer bump is a day. The surface catch-up is the project.** Staging below
reflects that.

## Compatibility policy — decide once, here

Two questions govern everything downstream. Recorded here so no port commit decides them ad hoc.

**Q1. Do we adopt Bot-API-7 parameter objects?**
Kurigram replaced `reply_to_message_id`/`quote_text` with `reply_parameters`, and
`disable_web_page_preview` with `link_preview_options`.

- *Decision (owner, 2026-08-28):* **adopt outright, no deprecation shims.** The object parameters
  are the only spelling. Old flat parameters are removed, not deprecated.
- *Consequence:* smaller than it sounds. Kurigram's long deprecated tail (`reply_to_chat_id`,
  `reply_to_story_id`, `quote_text`, `quote_entities`) **does not exist in this repo at all** —
  measured, 0 occurrences. Only two parameters actually go away:

  | Removed | Replaced by | Files touched |
  | --- | --- | --- |
  | `reply_to_message_id` | `reply_parameters` | 26 (21 under `methods/`, plus `Message` + 4 keyboard/content types) |
  | `disable_web_page_preview` | `link_preview_options` | 6 |

  `Message` alone accounts for 117 occurrences across 18 bound `reply_*` methods in a 3965-line
  file. Stage 4.1 emits the exhaustive call-site list so the downstream sweep is mechanical.
- *Rationale:* the owner's bots are the only consumer, and the real cost of a shim is not code
  volume — a central `utils.normalize_reply_parameters()` helper plus one call per method would be
  roughly 20 lines and 26 call sites. The cost is that every send/edit signature and docstring
  carries dead parameters for as long as the shim lives. With only two parameters actually being
  removed, a clean break is cheaper than the noise.

**Q2. Which branch is the product?**
- *Decision (owner, 2026-08-28):* **one branch, `dev`, in the `pyrogram` namespace.**
  `pyrogram-rebrand` was fast-forwarded into `dev` (`20716e95..fe2caeff`) and deleted locally and
  on `origin`. It must not be recreated.
- *Consequence:* `upstream/dev` (hydrogram/hydrogram) is still `hydrogram`-namespaced, so a plain
  merge conflicts across the whole tree. Stage 0 builds the sync tooling that makes upstream merges
  possible at all.

**Q3. How far does this round go?**
- *Decision (owner, 2026-08-28):* **stages 0-2, then reassess.** Upstream sync tooling, the
  regression net, the layer bump and the keyboard rewrite. Stage 3 onward is explicitly deferred;
  the checkpoint is a green suite on layer 229. Q1's decision still governs stage 4.1 whenever it
  is picked up — it is recorded, not scheduled.

**Q4. Does CI matter?**
- *Decision (owner, 2026-08-28):* **yes, get it green and extend it.** Restoring the pipeline is
  stage-0 work, and stage 1 adds the coverage gate, a `windows-latest` leg and the scheduled schema
  drift check.

## Stages

Each stage has a hard exit criterion. Do not start stage N+1 until stage N's criterion holds.
**This round ends after stage 2** (Q3). Stages 3-6 are kept here as the standing plan, not as
committed work.

### Stage 0 — make upstream syncable again (small, unblocks everything)

`dev` is `pyrogram`-namespaced; `upstream/dev` is `hydrogram`-namespaced. `git merge upstream/dev`
now conflicts on essentially every file. Upstream is slow (8 commits in the last 180 days) but not
dead — `edb10c60` (session race condition) is a real fix we took, and there will be more.

Build `dev_tools/sync_upstream.py`:

1. `git fetch upstream`
2. Read the last synced upstream SHA from `dev_tools/.upstream-sync` (seed it with `edb10c60`).
3. For each new upstream commit, `git format-patch` it, rewrite the patch text through the same
   rename map used by `868507da` (`hydrogram` → `pyrogram`, `Hydrogram` → `Pyrogram`,
   `hydrogram.org` → `pyrogram.org`, `HydrogramNews` → `PyrogramNews`, and the file paths
   `hydrogram/...` → `pyrogram/...`), then `git am` it.
4. On conflict, stop and report the commit — never auto-resolve.
5. Record the new SHA.

Two details that must be encoded in the script, not remembered:

- **Do not let a sync revert the version pin.** `__version__` is `2.0.106` on purpose
  (`py-tgcalls>=2.3` requires `pyrogram>=1.2.20` and reads `__version__`). If an upstream commit
  touches `pyrogram/__init__.py`'s version line, drop that hunk and log it.
- **Do not let a sync delete `pyrogram/emoji.py`.** It has no upstream counterpart.

Also add `make sync-upstream` and a CI job that runs the script in dry-run mode weekly and opens an
issue when upstream has unsynced commits.

**Also in stage 0 — make the local checks automatic.** `.pre-commit-config.yaml` already wires
`ruff-check --fix`, `ruff-format`, `detect-private-key`, `end-of-file-fixer`, `check-toml`,
`check-yaml` and the NEWS-fragment name check. It had simply never been installed as a git hook, so
none of it ran. `pre-commit install` was run on 2026-08-28 and immediately reformatted 5 files that
had been sitting unformatted on `dev` (`pyrogram/emoji.py` plus four rename-commit leftovers) —
i.e. `dev` was failing its own `code-style.yml` gate. With the hook installed, `ruff format` and
`ruff check` no longer need to be run by hand; they run on every commit.

Remaining stage-0 work on top of that:

- Add `pre-commit install` to the setup path (`make dev-setup`, and a line in `CONTRIBUTING.md`)
  so a fresh clone is never in the state `dev` was just in.
- Add a `pre-push` stage running `pytest -m "not integration"`, so a broken commit cannot reach
  `origin`. Keep it off the commit stage — commits should stay fast.
- Add the stage-1 `raw`-reference check as a local pre-commit hook once it exists; it is fast and
  catches the highest-value class of breakage.
- Pin `rev:` bumps through `pre-commit autoupdate`, not by hand.

**Exit:** `make sync-upstream` replays every unsynced upstream commit onto `dev` with the rename
applied, `pytest` green afterwards, and the version pin plus `emoji.py` intact.

### Stage 1 — the regression net (the "future-proof" stage)

Nothing here changes library behaviour. Everything here is what makes the rest safe.

1. `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`, `--strict-markers`, marker registry.
2. `tests/conftest.py` with directory-derived markers and shared raw-object factories.
3. Restructure into `tests/{unit,contract,integration}/`.
4. Write Tier 1 from `docs/dev/TESTING.md`:
   - raw serialization round-trip (sampled + property-based over the TL grammar),
   - constructor-ID stability against `main_api.tl`,
   - **`raw` reference resolution** — the test that turned up the 19 breakages,
   - public API surface / mixin wiring,
   - `file_id` full matrix, markdown parser, filter combinators,
   - storage contract + session-string round-trip,
   - `utils` peer-id boundaries.
5. Coverage gate at 60 % excluding `pyrogram/raw/`.
6. CI: explicit `-m "not integration"`, coverage upload, windows leg, scheduled
   `make check-api-schema`.

**Exit:** `pytest` covers ≥60 % of the non-generated tree; the `raw`-reference test passes on 223
and correctly *fails* with 19 findings when pointed at a 229 build.

### Stage 2 — layer bump to 229

1. Replace `compiler/api/source/main_api.tl` with layer 229; refresh
   `compiler/errors/source/*.tsv`.
2. `make api`; fix the 19 breakages:
   - forum-topic functions → `raw.functions.messages.*`,
   - `raw.types.Wallpaper` → `WallPaper`,
   - keyboards → stage 2b.
3. **2b — keyboard rewrite.** `inline_keyboard_button.py`, `keyboard_button.py`, `login_url.py`
   move to `ButtonType` / `InlineButtonType` dispatch. Layer 229 splits inline from reply into two
   separate raw base types (`KeyboardButton` and the new `KeyboardInlineButton`), which is why this
   is a rewrite and not a re-point. Take Kurigram's dispatch **and** its five button kinds we lack
   (`requires_password`, `switch_inline_query_chosen_chat`, `copy_text`, `disabled`, `pay`); keep
   our `_raw_style()` / `_read_style()` helper split, which is better than their inlined version.
   The public Python API of `InlineKeyboardButton` and `KeyboardButton` **must not change**.
   `keyboardButtonStyle#4fdd3430` is identical at 223 and 229, so the custom-emoji/style feature
   carries over unchanged — the risk is entirely in the dispatch.
4. Keyboard round-trip tests (Tier 2) land in the same commit as the rewrite.

**Exit:** layer 229 compiled, full suite green, keyboard round-trip tests cover every button
variant including custom-emoji styles, and a real bot smoke-run sends and receives both keyboard
kinds.

---

*Everything below is deferred (Q3). Kept as the standing plan; not scheduled.*

### Stage 3 — enums and shared types

Port the 28 missing enums and the ~40 shared value types the later stages depend on
(`ReplyParameters`, `LinkPreviewOptions`, `TextQuote`, `MessageOrigin*`, `ExternalReplyInfo`,
`FormattedText`, `StarAmount`, `PaidMediaInfo`, `RestrictionReason`, …), each through
`docs/dev/PORTING.md`, each with a `_parse` unit test.

**Exit:** `types.__all__` contains every shared type the stage-4 method groups reference; enum
snapshot test in place.

### Stage 4 — API surface, by feature group

Ordered by value-to-risk. Each group is its own PR with its own tests and news fragment.

| # | Group | Methods | Notes |
| --- | --- | --- | --- |
| 4.1 | Bot-API-7 parameter migration | — | `reply_parameters` / `link_preview_options` replace the flat params outright, no shims (Q1). Ships with the exhaustive removed-parameter list for the downstream sweep |
| 4.2 | Message gaps | ~40 | `send_paid_media`, `send_checklist`, reactions read/view, scheduled messages, `search_posts`, translation |
| 4.3 | Chats & folders | ~36 | folders, invite links, accent colors, direct-message topics, forum topic pin/unpin |
| 4.4 | Stories | 21 | self-contained; needs `Story`, `StoryView`, `MediaArea` types |
| 4.5 | Gifts / stars / payments | ~44 | largest group; `Gift`, `GiftCollection`, `StarAmount`, auctions, invoices |
| 4.6 | Bots & business | ~32 | business connections, managed bots, pre-checkout/shipping, invoice links |
| 4.7 | Account, privacy, auth sessions | ~21 | `PrivacyRule` family, active sessions, TTLs |
| 4.8 | Handlers & decorators | 16 | `on_story`, `on_message_reaction`, `on_business_message`, boost/purchase handlers — needs dispatcher work |

**Exit per group:** methods wired into the mixin, `_parse` tests for every new type, docs build
clean, news fragment present.

### Stage 5 — connection layer (optional, isolated)

MTProxy + fake-TLS + web-proxy carrier, and the `pysocks` → `python-socks[asyncio]` swap. Kurigram
landed this on 2026-08-27 with its own unit + live test split; port both the code and the tests.
Independent of stages 2–4 — schedule it whenever, but not concurrently with them.

### Stage 6 — production hardening

1. Version scheme: adopt a real one (`3.0.0`). **This does not conflict with the pin**, contrary
   to what it looks like. `py-tgcalls` 2.3.3 declares `pyrogram>=1.2.20; extra == "pyrogram"` — a
   floor, no ceiling. Hydrogram's own `0.2.0` failed that floor, which is why `f81a62a4` pinned
   `2.0.106`; any version `>=1.2.20` works, so `3.0.0` is fine. Verify against the installed
   `py-tgcalls` before bumping, then drop the "pin" framing from `CLAUDE.md`.
   (Note for the record: `py-tgcalls` also declares `hydrogram>=0.1.4; extra == "hydrogram"`, so it
   supports Hydrogram natively. The binding constraint for the rename was `pykeyboard`, which does
   `from pyrogram.emoji import *`.)
2. Docs: `make docs` clean; rewrite `docs/source/hydrogram-vs-pyrogram.rst`; changelog via towncrier.
3. `py.typed` is already shipped — add a type-check gate (`ty` or `mypy`) to CI, even if only on a
   subset initially.
4. Publish: decide PyPI name. `pyrogram` on PyPI is taken by the archived original, so this fork
   cannot be published under that name. Either publish under a name we own, or keep it a private
   install (`git+https://…`), which is what it is today.
5. Tag, release notes, and a dependency-audit pass.

## Sequencing notes

- Stage 1 and stage 0 are independent — do them in parallel if convenient.
- Stage 2 depends on stage 1's `raw`-reference test to be worth anything.
- Stage 4 groups are independent of each other and can be parallelised across sessions, provided
  stage 3 has landed the shared types they import.
- Merge from `upstream/dev` before starting each stage; upstream hydrogram is slow (8 commits in
  the last 180 days) but not dead, and conflicts are cheapest when taken early.

## Risks

| Risk | Mitigation |
| --- | --- |
| Keyboard rewrite silently breaks existing bots | Round-trip tests land with the rewrite; public Python API frozen; smoke-run before merge |
| Session strings become unreadable | `SESSION_STRING_FORMAT` treated as a versioned public format, with a decode test per historical version |
| Ported code drifts back to Kurigram style | `docs/dev/PORTING.md` checklist + a ruff rule set that already rejects `Optional[`/quoted annotations |
| Scope explodes across 221 methods | Stage 4 is per-group PRs; a group can be skipped without blocking the rest |
| Upstream hydrogram diverges further, and the namespace split makes merging impossible | Stage 0 `sync_upstream.py` + weekly CI check; sync at every stage boundary |
| `py-tgcalls` version pin silently reverted by an upstream sync | Sync script drops version-line hunks and logs them; a contract test asserts `__version__ == "2.0.106"` |
| `pyrogram/emoji.py` deleted by an upstream sync (no upstream counterpart) | Sync script refuses deletions of it; import test in `tests/contract/` |
| Style checks silently rot again | `pre-commit install` is part of setup; `pre-push` runs the unit suite; CI is green before stage 1 closes |
| Adopting Bot-API-7 params outright breaks the owner's bots with no warning | Stage 4.1 emits the exhaustive removed-parameter list; do that sweep before the stage lands |
