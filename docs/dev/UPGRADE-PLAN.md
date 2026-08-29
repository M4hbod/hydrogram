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

6. **CI runs on the fork and is half-green.** Measured on `M4hbod/hydrogram`, not upstream:
   the `Pyrogram` workflow (`python.yml`, `make api` + `pytest`) has **passed on every push**,
   including `fe2caeff` on 2026-08-28. The `Check style` workflow has **failed on every push**
   since the rename stack landed, for one reason — `5 files would be reformatted, 466 files
   already formatted`, the same 5 files `77b0dc1d` has now fixed. That commit should turn it
   green.
   (The daily `Check MTProto API Schema Updates` failures belong to **upstream**
   `hydrogram/hydrogram`, not to this fork; `gh` resolves to upstream unless `-R` is passed.)
   So stage-0 CI work is *extension*, not resurrection.

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
- *Decision (owner, 2026-08-28):* **yes, get it green and extend it.** The one red check is fixed
  by `77b0dc1d`; stage 0 adds the coverage gate, a `windows-latest` leg and a scheduled schema
  drift check of our own.

## Stages

Each stage has a hard exit criterion. Do not start stage N+1 until stage N's criterion holds.
**This round ends after stage 2** (Q3). Stages 3-6 are kept here as the standing plan, not as
committed work.

### Stage 0 — tooling — **DONE 2026-08-28**

`dev` is `pyrogram`-namespaced; `upstream/dev` is `hydrogram`-namespaced, so `git merge
upstream/dev` conflicts on essentially every file. Upstream is slow (8 commits in the last 180
days) but not dead — `edb10c60` was a real session fix we took.

**What shipped:**

1. **`dev_tools/sync_upstream.py`** — replays upstream commits as rewritten patches.
   `git format-patch` → case-preserving `hydrogram`→`pyrogram` substitution → `git am --3way`,
   recording the last synced SHA in `dev_tools/.upstream-sync` and folding that update into the
   replayed commit. `--check` (exit 1 on drift), `--dry-run`, `--limit`, `--no-fetch` and
   `--upstream-ref` for testing. Conflicts stop the run and leave the rewritten patch on disk.

   Two guards are encoded rather than remembered: `pyrogram/emoji.py` cannot be deleted, and a
   `__version__` bump cannot drag us under the `py-tgcalls` floor.

   **The version guard took two attempts, and the reason is worth keeping.** Rewriting the
   version change into a *context* line keeps the hunk line counts valid but makes the patch fail
   anyway — upstream's context reads `0.2.1.dev` and our file reads `2.0.106`, so the context
   assertion fails. Applying first and restoring afterwards fails too: with `--3way` the version
   line is a genuine three-way conflict (base `0.2.1.dev`, ours `2.0.106`, theirs the new value)
   and `git am` stops before anything can be restored. What works is dropping the **whole file
   chunk** for `pyrogram/__init__.py` when its only change is the version line — no line-count
   arithmetic, no context to mismatch. A chunk that changes anything else is kept, and the
   conflict is left for a human.

   Verified end to end against a synthetic upstream commit that touched both `hydrogram/utils.py`
   and `__version__`: the rename applied, the probe function landed as `pyrogram`, the pin held at
   `2.0.106`, and the state file advanced.

2. **Hooks in the setup path.** `make dev-setup` installs dependencies and both git hooks.
   `pre-commit` runs style on commit; a new `pre-push` stage runs `pytest -m "not integration"`,
   so commits stay fast but nothing broken reaches the remote. `CONTRIBUTING.md` now says not to
   run Ruff by hand.

3. **CI.** `code-style.yml` now runs `pre-commit run --all-files`, so CI and the local hook cannot
   disagree about what "clean" means. `python.yml` gains a `windows-latest` leg (trimmed to the
   ends of the Python range) and a coverage job, and calls the compiler directly rather than
   through `make`, which Windows runners do not have. A new `drift.yml` asks weekly whether
   Telegram has published a newer TL layer or upstream has unsynced commits; both checks report
   and exit 1 without writing anything.

4. **Supporting fixes.** `dev_tools/check_api_schema_updates.py` gained `--check` — it previously
   had no read-only mode and rewrote the schema as a side effect of "checking". `requests` was
   used by `dev_tools/` but only present transitively; it is now declared. `[tool.uv]
   dev-dependencies` moved to `[dependency-groups]`, silencing a deprecation warning on every uv
   invocation. `.coveragerc` added.

**Exit criteria met:** `make sync-upstream-check` reports cleanly against the real remote, the
replay path is verified against a synthetic commit, both hooks are installed, and the style
pipeline is green.

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
5. Coverage gate, ratcheted to the measured floor, excluding `pyrogram/raw/`.
6. CI: explicit `-m "not integration"`, coverage upload, windows leg, scheduled
   `make check-api-schema`.

**Exit:** the `raw`-reference test passes, and coverage of the non-generated tree is gated at the
measured floor so it cannot silently regress.

### Stage 2 — layer bump to 229 — **DONE 2026-08-28**

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

**What happened.** `make check-api-schema` fetches the authoritative schema from tdesktop, and its
layer 229 is constructor-for-constructor identical to Kurigram's copy (2465 both, zero diff) — so
Kurigram's file was not needed at all. After `make api`, the `raw`-reference contract test reported
exactly **12** breakages rather than the 19 predicted: the six forum-topic functions and the
`WallPaper` typo had already been fixed in stage 1, leaving only the keyboards.

The keyboard rewrite went as planned. `read()` now dispatches on `b.type`, `InlineKeyboardMarkup`
emits `KeyboardInlineButtonRow`, and `LoginUrl.write()` returns an `InlineButtonType` rather than a
whole button — which is also what makes the style-dropping bug structurally impossible to
reintroduce. All twelve `InlineButtonType` variants are handled; previously `copy_text`, `pay` and
`disabled` buttons had no `read()` branch and vanished from parsed markup, so those are now exposed
as constructor parameters too, along with `requires_password`.

**Exit criteria met:** layer 229 compiled, 1266 tests green, coverage 54 %, and the keyboard tests
cover every button kind against write, read and style/custom-emoji preservation.

**Live smoke-run (2026-08-28).** Done, against production Telegram, with a user session and a
bot:

- Layer 229 negotiates and authorises; `get_me`, `send_message`, `get_chat_history` all work.
- `message.date` comes back timezone-aware UTC, and `date > zero_datetime()` returns `True` rather
  than raising — the fix in `699e609c` confirmed on a real message.
- **Keyboard write path**: a bot sent all eight modellable button kinds (`callback_data`, `url`,
  `switch_inline_query`, `switch_inline_query_current_chat`, `copy_text`, `web_app`, `user_id`,
  `disabled`) and read every one back intact, with `style=DANGER` preserved on all eight.
- **Keyboard read path**: a keyboard produced by Telegram's own Bot API parsed correctly through
  the layer-229 `InlineButtonType` dispatch, `copy_text` included — a kind that had no `read()`
  branch before stage 2 and would previously have vanished from the parsed markup.
- Two documentation errors found and corrected: `style` does **not** require Premium (it worked
  from a non-Premium bot owner), and `icon_custom_emoji_id` is accepted and then silently dropped
  by the server, with no error, when it will not be honoured.

Not covered live: `login_url` (needs a configured domain), `pay` (needs an invoice), `callback_game`
(needs a registered game), and the forum-topic namespace migration (needs a forum supergroup).

---

*Everything below is deferred (Q3). Kept as the standing plan; not scheduled.*

### Stage 3 — enums and shared types — **PARTIALLY DONE 2026-08-28**

**Done:**

- **All 28 missing enums** (`3a4dd645`). Public set 15 → 43. Member names and values are frozen by
  a snapshot test, because renaming either is a breaking change nothing else in the suite would
  notice — no library code depends on the spelling, but user code and stored configs do.
- **`ReplyParameters` and `LinkPreviewOptions`** (`0c544686`) — the two types stage 4.1 needs.

**Deliberately not done.** The original plan listed ~40 shared types. Most of them are not
*shared*: they are the leaves of a specific stage-4 group, and porting them now would mean
importing that group's subtree with nothing to exercise it.

`ExternalReplyInfo` is the clearest case — it references about twenty types this fork does not have
(`Checklist`, `Giveaway`, `GiveawayWinners`, `Invoice`, `PaidMediaInfo`, `Story`, the
`MessageMedia*` family), so it belongs to whichever group brings those in. `TextQuote` and the
`MessageOrigin` family are portable today but have no consumer until the message-parsing work in
stage 4.2.

**Revised exit criterion:** stage 3 is complete for a given stage-4 group when that group's shared
types are in place. The enums — which are self-contained and cost nothing while unused — are done
for all groups.

**Next:** stage 4.1 (the Bot-API-7 parameter migration) is now unblocked. It is the only stage-4
item whose scope is already decided, and it touches 26 files plus `Message`'s 18 bound `reply_*`
methods.

### Stage 4 — API surface

Re-planned 2026-08-29 against measured dependency data, which contradicted the original grouping.

**What the measurement changed.** The first version of this stage assumed each feature group could
be ported independently. That is *mostly* true — of the 94 types the remaining 221 methods need,
only 31 are wanted by more than one group — but it missed the real bottleneck. `Message` is the hub
every group writes into, and it is the largest single piece of work in the project:

| | ours | Kurigram | gap |
| --- | --- | --- | --- |
| `message.py` lines | 3,965 | 10,537 | 2.7× |
| attributes | 79 | 168 | **99** |
| bound methods | 35 | 75 | **42** |
| `filters.py` filters | 53 | 74 | **21** |

So groups are cheap and `Message` is expensive, and almost every group needs a slice of `Message`
before its methods parse anything. Sequencing has to reflect that.

#### Cost per group (measured)

"New types" is the transitive closure of `types.X` references, stopping at types we already own.

| Group | Methods | New types | Types/method | Notes |
| --- | --- | --- | --- | --- |
| decorators | 16 | 0 | 0.00 | needs 16 handler classes + dispatcher wiring, not types |
| advanced | 1 | 0 | 0.00 | `recover_gaps` |
| chats | 36 | 4 | 0.11 | folders, accent colours, direct-message topics |
| users | 6 | 1 | 0.17 | `Birthday` |
| messages | 41 | 10 | 0.24 | checklists, suggested posts, paid media, AI text |
| bots | 27 | 9 | 0.33 | invoices, managed bots, pre-checkout/shipping |
| contacts | 3 | 2 | 0.67 | |
| premium | 3 | 2 | 0.67 | boosts |
| phone | 1 | 1 | 1.00 | `GroupCallMember` |
| payments | 44 | 45 | 1.02 | gifts, stars, auctions — the largest group |
| stories | 21 | 26 | 1.24 | self-contained otherwise |
| account | 10 | 16 | 1.60 | privacy rules, sessions, TTLs |
| auth | 6 | 6 | 1.00 | active sessions, phone-number change |
| folders | 1 | 4 | 4.00 | fold into `chats` |
| business | 5 | 24 | 4.80 | mostly the shared gift cluster |
| **total** | **221** | **94** | | deduped union |

#### Stage 4.0 — shared foundation

The 31 types wanted by more than one group. Doing these first stops three groups each porting the
same gift cluster.

- **`FormattedText`** — 6 groups. The single most-shared type; port first.
- **Gift cluster (21 types)** — `Gift`, `GiftAttribute`, `GiftAuction`, `AuctionState{,Active,Finished}`,
  `AuctionBid`, `AuctionRound`, `GiftResalePrice{,Star,Ton}`, `GiftResaleParameters`,
  `GiftPurchaseLimit`, `UpgradedGiftAttributeRarity{,Epic,Legendary,PerMille,Rare,Uncommon}`,
  `UpgradedGiftOriginalDetails`. Wanted by business + payments + stories.
- **Suggested posts (4)** — `SuggestedPostParameters`, `SuggestedPostPrice{,Star,Ton}` (bots + messages).
- **Invoicing (2)** — `Invoice`, `LabeledPrice` (bots + payments).
- **Folders (2)** — `Folder`, `FolderInviteLink` (chats + folders).
- **`Birthday`** (payments + users).

**Exit:** all 31 exported with `_parse` unit tests; no group needs to port a type another group
already ported.

#### Stage 4.1 — Bot-API-7 parameter migration

Scope already decided (Q1: adopt outright, no shims). Unblocked — `ReplyParameters` and
`LinkPreviewOptions` landed in `0c544686`.

`reply_to_message_id` → `reply_parameters` across 26 files, `disable_web_page_preview` →
`link_preview_options` across 6, plus `Message`'s 18 bound `reply_*` methods. **Breaking, with no
`DeprecationWarning` to guide the sweep.** Ship the exhaustive removed-parameter list with it so the
downstream fix is a grep rather than a hunt.

**Exit:** no `reply_to_message_id` or `disable_web_page_preview` outside a news fragment; contract
test asserts both are gone from every public signature.

#### Stage 4.2 — the `Message` spine

The expensive one, and the gate on everything after it. 99 attributes and 42 bound methods.

Do it as **one commit per attribute cluster**, not one commit for `Message`: service messages,
forwards/origins, checklists, paid media, suggested posts, business, giveaways, stories. Each
cluster lands with `_parse` tests built from hand-made raw objects.

**Exit:** `Message` parses every `raw.types.Message` and `MessageService` variant the layer defines;
`test_message_parsing` covers each cluster; no attribute is set but undocumented.

#### Stage 4.3 — groups, cheapest first

Order is by types/method, which is also roughly ascending risk. Each is its own PR with tests and a
news fragment, and each is independently skippable.

1. **advanced** (1 method) — trivial, do it with anything.
2. **decorators + handlers** (16 methods, 16 handler classes, 0 new types) — `on_story`,
   `on_message_reaction`, `on_business_message`, boost/purchase handlers. Needs dispatcher work and
   21 new filters; no type porting at all.
3. **chats + folders** (37 methods, 4 types) — best value in the project.
4. **users** (6), **contacts** (3), **premium** (3), **phone** (1) — small and independent.
5. **messages** (41 methods, 10 types) — large but cheap per method; depends on 4.2.
6. **bots** (27 methods, 9 types).
7. **auth** (6) and **account** (10, 16 types) — privacy rules and session management.
8. **stories** (21 methods, 26 types) — self-contained once the gift cluster exists.
9. **payments** (44 methods, 45 types) — largest and last; gifts, stars, auctions.
10. **business** (5 methods, 24 types) — cheapest last, because 21 of its 24 types are the gift
    cluster from 4.0, leaving only 3 of its own.

**Exit per group:** methods wired into the mixin, `_parse` tests for every new type, docs build
clean, news fragment present, coverage ratchet raised.

### Stage 5 — connection layer — **ATTEMPTED AND REVERTED 2026-08-29**

Porting `connection/proxy.py`, `faketls_records.py`, `web_proxy_carrier.py` and
`tcp_intermediate_padded.py` also requires Kurigram's `Connection`, and its constructor takes a
resolved `server_address` / `port` where ours takes `ipv6` — the DC lookup moved to the caller. So
adopting it means porting `session.py` and `auth.py` as well, both of which carry local fixes (the
monotonic interval timers, the connect/disconnect hooks).

That is a transport refactor touching every connection the client makes, in exchange for MTProxy
and fake-TLS support that cannot be verified without a proxy server to test against. The working
transport was kept and the port reverted; the `pysocks` → `python-socks[asyncio]` swap went back
with it.

**To do it properly:** port `connection/`, `session/session.py` and `session/auth.py` as one unit,
re-apply the local fixes on top, and stand up a proxy (or use `tests/integration/` with real
credentials) before merging. It is genuinely independent of everything else, so it can be done
whenever.

### Stage 6 — release hardening — **PARTIALLY DONE 2026-08-29**

1. **Version → `3.0.0`** — done. Verified against `py-tgcalls` 2.3.3, which declares
   `pyrogram>=1.2.20`: a floor, not a ceiling, so the old `2.0.106` pin was never a ceiling either.
2. **Docs** — the generated API pages under `docs/source/api/**` need regenerating for the 441-method
   surface (`make docs`). Not done.
3. **Type gate** — `ty`/`mypy` in CI on a subset. Not done.
4. **PyPI name** — the owner's decision. `pyrogram` belongs to the archived original, so this fork
   publishes under a name we own or stays a git install, which is what it is today.
5. **Tag and release notes** — `towncrier` fragments are in `news/` and ready to build.

## Sequencing notes

- **Stage 4.0 before any group.** Three groups want the same 21-type gift cluster; porting it once
  is the whole point of having a shared stage.
- **Stage 4.2 (`Message`) gates 4.3 items 5 onward.** chats, users, contacts, premium, phone and
  the decorators can land before it; messages, bots, stories, payments and business cannot parse
  their results without it.
- **Groups are independent of each other.** Only 31 of 94 types are shared, and stage 4.0 absorbs
  all of them, so after that the remaining groups touch disjoint type sets. They can be done in any
  order, dropped individually, or parallelised across sessions.
- **Stage 5 is independent of stage 4 entirely** but should not run concurrently with it: it
  changes the transport every other test runs through.
- **Sync upstream at every stage boundary** — `make sync-upstream-check` is cheap and conflicts are
  cheapest when taken early.
- Raise the coverage ratchet at the end of each stage; never lower it to make a build pass.

## Risks

| Risk | Mitigation |
| --- | --- |
| Keyboard rewrite silently breaks existing bots | Round-trip tests land with the rewrite; public Python API frozen; smoke-run before merge |
| Session strings become unreadable | `SESSION_STRING_FORMAT` treated as a versioned public format, with a decode test per historical version |
| Ported code drifts back to Kurigram style | `docs/dev/PORTING.md` checklist + a ruff rule set that already rejects `Optional[`/quoted annotations |
| Scope explodes across 221 methods | Stage 4 is per-group PRs; measured type closure shows groups are disjoint after 4.0, so any group can be skipped without blocking the rest |
| `Message` becomes an unreviewable mega-commit | 4.2 is split one commit per attribute cluster (service, forwards, checklists, paid media, suggested posts, business, giveaways, stories), each with `_parse` tests |
| A ported type silently stops being reachable | `tests/contract/test_public_api.py` fails when a symbol is in `__all__` but unwired, and when a method class is not a `Client` base |
| Upstream hydrogram diverges further, and the namespace split makes merging impossible | Stage 0 `sync_upstream.py` + weekly CI check; sync at every stage boundary |
| `py-tgcalls` version pin silently reverted by an upstream sync | Sync script drops version-line hunks and logs them; a contract test asserts `__version__ == "2.0.106"` |
| `pyrogram/emoji.py` deleted by an upstream sync (no upstream counterpart) | Sync script refuses deletions of it; import test in `tests/contract/` |
| Style checks silently rot again | `pre-commit install` is part of setup; `pre-push` runs the unit suite; CI is green before stage 1 closes |
| Adopting Bot-API-7 params outright breaks the owner's bots with no warning | Stage 4.1 emits the exhaustive removed-parameter list; do that sweep before the stage lands |
