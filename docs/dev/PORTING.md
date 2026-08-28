# Porting code from Kurigram (and other Pyrogram forks)

This is a **contract**, not a suggestion. Code that lands in this repo must read as if it were
written here. A reviewer must not be able to tell which files were ported.

Reference snapshot used to write this document: `KurimuzonAkuma/pyrogram@dev`, version `2.2.25`,
TL layer 229 (2026-08-27).

---

## 0. Why the two codebases differ at all

Both forks descend from `pyrogram/pyrogram` 2.0.106, then diverged:

- **Kurigram** kept Pyrogram's original 3.8-compatible style and spent its effort on API surface.
  It is ~2× larger than us (407 vs 211 method files, 308 vs 121 type files) and 6 layers ahead.
- **Hydrogram** kept the API surface small and spent its effort on modernising the codebase:
  `from __future__ import annotations`, PEP 604/585 types, keyword-only arguments, `TYPE_CHECKING`
  blocks, ruff-enforced style, absolute imports.

So Kurigram is our **source of behaviour**, never our source of style.

---

## 1. Typing

Kurigram targets Python 3.8 and uses `typing` generics with quoted forward references.
We target 3.9+ and rely on `from __future__ import annotations`, which makes every annotation lazy.

Every ported file **must** start its import block with:

```python
from __future__ import annotations
```

Translation table — apply mechanically:

| Kurigram | Hydrogram |
| --- | --- |
| `Optional[int]` | `int \| None` |
| `Optional["types.Message"]` | `types.Message \| None` |
| `Union[int, str]` | `int \| str` |
| `Optional[Union[int, str]]` | `int \| str \| None` |
| `List["types.MessageEntity"]` | `list[types.MessageEntity]` |
| `Dict[str, int]` | `dict[str, int]` |
| `Tuple[int, ...]` | `tuple[int, ...]` |
| `Callable` from `typing` | `from collections.abc import Callable` |
| `self: "pyrogram.Client"` | `self: pyrogram.Client` |
| `client: Optional["pyrogram.Client"] = None` | `client: pyrogram.Client = None` |
| `AsyncGenerator["types.Message", None]` | `AsyncGenerator[types.Message, None]` (from `collections.abc`) |

Quoted annotations are **banned** in new and ported code — `from __future__ import annotations`
makes them redundant and ruff's `UP037` flags them.

> **The tree is not yet uniform.** 268 of 445 non-generated modules carry
> `from __future__ import annotations`; the rest are pre-modernisation upstream files.
> `pyrogram/types/object.py` is the one you will hit first — it still uses `import typing` +
> `typing.TYPE_CHECKING` + a quoted `"pyrogram.Client"`. Do not copy that shape, and do not treat
> it as licence to skip the rule. Modernise a legacy file only when you are already editing it for
> another reason, never as a drive-by.

`Optional[X] = None` where `X` is a union of concrete types keeps `| None`; do **not** drop it just
because the default is `None`. The one exception we inherit from upstream is `client:
pyrogram.Client = None` on `Object.__init__`, which is left as-is for compatibility.

## 2. Imports

- **Absolute imports only.** `from ..object import Object` → `from pyrogram.types.object import Object`.
  Ruff `TID252` enforces this.
- Anything used **only in annotations** goes in a `TYPE_CHECKING` block:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

import pyrogram
from pyrogram import enums, raw, types, utils

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
```

  `pyrogram`, `raw`, `types`, `utils`, `enums` are usually needed at runtime in method modules —
  keep them at module level there. In pure type modules they are frequently annotation-only; move
  them under `TYPE_CHECKING` when they are.
- Kurigram sprinkles `log = logging.getLogger(__name__)` into modules that never log. Drop it
  unless the ported body actually calls `log.*`.
- Kurigram's import ordering is inconsistent. Do not preserve it; ruff `I` (isort) decides, with
  `known-first-party = ["pyrogram"]`.

## 3. Signatures

Kurigram method signatures are fully positional and have accumulated a long tail of
backwards-compatibility parameters at the end (`reply_to_message_id`, `reply_to_chat_id`,
`reply_to_story_id`, `quote_text`, …) that shadow the modern ones.

Our rule:

1. Required parameters are positional (`self`, `chat_id`, `text`).
2. **Everything else is keyword-only** — insert a bare `*,` after the required block.
3. **Do not port the deprecated tail.** Port the modern parameter (`reply_parameters`,
   `link_preview_options`) only. If a legacy alias must be kept for our own compatibility, that is
   a deliberate decision recorded in `docs/dev/UPGRADE-PLAN.md`, not a silent copy.
4. Preserve parameter *order* of the modern block where it is meaningful, otherwise group logically.

Example — Kurigram:

```python
async def send_message(
    self: "pyrogram.Client",
    chat_id: Union[int, str],
    text: str,
    parse_mode: Optional["enums.ParseMode"] = None,
    entities: Optional[List["types.MessageEntity"]] = None,
    link_preview_options: Optional["types.LinkPreviewOptions"] = None,
    ...
    reply_to_message_id: Optional[int] = None,   # legacy tail
    reply_to_chat_id: Optional[Union[int, str]] = None,
) -> "types.Message":
```

Ported:

```python
async def send_message(
    self: pyrogram.Client,
    chat_id: int | str,
    text: str,
    *,
    parse_mode: enums.ParseMode | None = None,
    entities: list[types.MessageEntity] | None = None,
    link_preview_options: types.LinkPreviewOptions | None = None,
    ...
) -> types.Message:
```

## 4. License headers

Kurigram files carry a single line:

```
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
```

Our headers carry both holders. **Ported files are derivative works — keep Dan's line.**

For a file ported from Kurigram (existing upstream lineage):

```python
#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Pyrogram <https://pyrogram.org>
#
#  This file is part of Pyrogram.
#  ... (rest of the LGPL block, see AGENTS.md)
```

For a genuinely new file written here from scratch, only the second copyright line.

The project name in the header is `Pyrogram` throughout this repo, including in files inherited
from Hydrogram — the `868507da` rename covered them. Copy the header from a neighbouring file
rather than typing it, and never reintroduce `Hydrogram` branding.

## 5. Directory and module mapping

Kurigram reorganised several packages. Map, do not mirror:

| Kurigram path | This repo |
| --- | --- |
| `types/input_content/input_media_*.py` | `types/input_media/input_media_*.py` |
| `types/input_content/input_*_message_content.py` | `types/input_message_content/` |
| `types/input_content/input_privacy_rule_*.py` | new package `types/input_privacy_rule/` (create it) |
| `storage/storage.py` (`Storage`) | `storage/base.py` (`BaseStorage`) |
| `types/messages_and_media/forum_topic*.py` | `types/user_and_chats/forum_topic*.py` (ours) |
| `types/messages_and_media/chat_background.py` | `types/user_and_chats/chat_background.py` (ours) |

Where we already have a file at a different path, **keep our path**. Moving files is a separate,
explicitly-scoped commit — never bundled into a port.

## 6. `__init__.py` wiring

Every ported symbol needs three edits, and forgetting one is the most common porting bug:

1. `from .thing import Thing` in the subpackage `__init__.py`
2. `"Thing"` appended to that file's `__all__` — **alphabetically sorted**
3. re-export from the parent (`pyrogram/types/__init__.py`, `pyrogram/enums/__init__.py`)

For methods, the fourth edit is the mixin:

```python
# pyrogram/methods/messages/__init__.py
from .send_checklist import SendChecklist

class Messages(
    ...,
    SendChecklist,
):
    pass
```

`tests/contract/test_public_api.py` (see `docs/dev/TESTING.md`) exists specifically to catch a
missed step.

## 7. Behavioural differences to watch

These are places where a naive copy compiles but misbehaves.

### 7.1 `Object.default` — attribute hiding

Kurigram's `Object.default` hides a `raw` attribute and masks `phone_number`:

```python
attributes_to_hide = {"raw"}
attributes_to_mask = {"phone_number"}
```

Ours masks `phone_number` only, because we do not attach `.raw` to high-level objects. If you port
a Kurigram type that stores `self.raw = ...`, you must either drop that attribute or extend
`Object.default` deliberately — do not let a raw MTProto blob leak into `str(obj)`.

### 7.2 Keyboard buttons were redesigned in layer 229

This is the largest single breaking change between 223 and 229.

Layer 223 (ours) has 18 flat constructors, each carrying `style:flags.10?KeyboardButtonStyle`:

```
keyboardButtonUrl#d80c25ec flags:# style:flags.10?KeyboardButtonStyle text:string url:string = KeyboardButton;
keyboardButtonCallback#e62bc960 flags:# requires_password:flags.0?true style:flags.10?KeyboardButtonStyle text:string data:bytes = KeyboardButton;
```

Layer 229 replaces that with **two separate base types**, each carrying a discriminator union:

```
# reply keyboards
keyboardButton#2f67a72f flags:# style:flags.10?KeyboardButtonStyle text:string type:ButtonType = KeyboardButton;
buttonTypeDefault#c9dd90e9 = ButtonType;
buttonTypeRequestPhone#df3d36f9 = ButtonType;          # 7 ButtonType constructors total

# inline keyboards — a base type that does not exist at layer 223
keyboardInlineButton#11c1a322 flags:# style:flags.10?KeyboardButtonStyle text:string type:InlineButtonType = KeyboardInlineButton;
inlineButtonTypeCallback#2955bc38 flags:# requires_password:flags.0?true data:bytes = InlineButtonType;
inlineButtonTypeCopy#b41d3272 copy_text:string = InlineButtonType;
inlineButtonTypeDisabled#a438619d = InlineButtonType;   # 12 InlineButtonType constructors total
```

The split of inline from reply into distinct bases is the part that makes this a rewrite: at 223
both kinds share `raw.base.KeyboardButton`, so `read()` cannot simply be re-pointed.

### What is *not* at risk

`keyboardButtonStyle#4fdd3430` is **byte-identical between layer 223 and 229**:

```
keyboardButtonStyle#4fdd3430 flags:# bg_primary:flags.0?true bg_danger:flags.1?true bg_success:flags.2?true icon:flags.3?long = KeyboardButtonStyle;
```

Our feature commit `28cd61aa` was itself ported from Kurigram and its style logic is behaviourally
identical to theirs — same `ButtonStyle` enum, same `bg_*` mapping, same `str(icon)` round-trip.
The style/custom-emoji feature survives the layer bump untouched. Only the dispatch around it moves.

### What we are actually missing

Kurigram's `InlineKeyboardButton` supports five button kinds we do not:
`requires_password`, `switch_inline_query_chosen_chat`, `copy_text`, `disabled`, and `pay`
(ours has `# self.pay = pay` sitting commented out). Take these in the same pass.

### A bug of ours to fix on the way through

`pyrogram/types/bots_and_keyboards/login_url.py:82` — `LoginUrl.write()` takes no `style`
parameter, so `InlineKeyboardButton.write()` computes `style = self._raw_style()` and then silently
drops it on the `login_url` branch. Style and custom-emoji icon are lost on login-url buttons. This
is independent of the layer and can be fixed at 223.

### How to do the port

- Take Kurigram's `type`-based dispatch and its five extra button kinds.
- **Keep our `_raw_style()` / `_read_style()` helper split** — Kurigram inlines that logic into
  `read()`; our factoring is better and survives the rewrite.
- `inline_keyboard_button.py`, `keyboard_button.py` and `login_url.py` are rewritten together.
- The public `InlineKeyboardButton` / `KeyboardButton` Python API must not change shape. Users' bot
  code is the compatibility boundary, not the raw layer.

### 7.3 Bot-API-7 parameter objects

Kurigram replaced flat parameters with objects:

| Old (ours today) | New (Kurigram / layer 229 era) |
| --- | --- |
| `reply_to_message_id`, `reply_to_chat_id`, `quote_text`, `quote_entities` | `reply_parameters: types.ReplyParameters` |
| `disable_web_page_preview` | `link_preview_options: types.LinkPreviewOptions` |

Adopting these is a **breaking change for downstream bots**, and the decision is already made:
**adopt outright, no deprecation shims** (`docs/dev/UPGRADE-PLAN.md` § Compatibility policy, Q1).
So when porting, drop the flat parameter entirely rather than keeping it alongside — but record
every parameter you remove, because stage 4.1 collects them into the downstream migration list.

### 7.4 Connection layer

Kurigram depends on `python-socks[asyncio]`; we depend on `pysocks`. Kurigram additionally ships
`connection/proxy.py`, `transport/tcp/faketls_records.py`, `transport/tcp/web_proxy_carrier.py`
and `tcp_intermediate_padded.py`, none of which we have. Porting MTProxy/fake-TLS means porting the
dependency change too — treat it as its own stage, with its own tests.

### 7.5 Storage

Kurigram's `Storage` base and ours (`BaseStorage`) have compatible method sets but different
names and a different `SESSION_STRING_FORMAT` history. Session strings are user data: any change
to `SESSION_STRING_FORMAT` is a breaking change requiring a migration path and a test that reads a
string produced by the previous format.

## 8. Docstrings

Keep Kurigram's prose — it is accurate and matches Telegram's own wording — but normalise:

- `List of :obj:`~pyrogram.types.X`` stays as-is (this is Sphinx markup, not a Python annotation).
- Keep the `.. include:: /_includes/usable-by/{users,bots,users-bots}.rst` directive; both forks use
  the same include paths.
- Keep `Parameters:` / `Returns:` / `Raises:` / `Example:` section order.
- Reflow to 99 columns only where the line is code; leave long prose lines alone (`E501` is ignored
  in CI's ruff invocation and docstring prose is not reflowed by `ruff format`).
- Cross-references stay `:obj:`~pyrogram.types.X`` — this repo's import name is `pyrogram`, the
  same as Kurigram's, so Kurigram's docstring references need no rewriting.

## 9. Enums

Kurigram has 28 enums we lack (`ProxyScheme`, `PrivacyKey`, `StickerType`, `GiftType`,
`MessageOriginType`, …). Port them as `pyrogram/enums/<name>.py` using our existing pattern
(`AutoName` base where applicable), export in `pyrogram/enums/__init__.py`, and add to `__all__`.

Enum *values* are part of the public API. Never rename a member during a port.

## 10. Porting checklist

Run this before opening a PR for any ported file:

- [ ] `from __future__ import annotations` present
- [ ] No `Optional[`, `Union[`, `List[`, `Dict[`, `Tuple[` from `typing`
- [ ] No quoted annotations
- [ ] Annotation-only imports inside `TYPE_CHECKING`
- [ ] Absolute imports only
- [ ] `*` separator before optional parameters
- [ ] Deprecated parameter tail dropped
- [ ] Dual copyright header, matching the branch's project name
- [ ] Symbol wired into subpackage `__init__.py`, `__all__` (sorted), parent re-export, and the
      method mixin if it is a method
- [ ] `pre-commit run --all-files` clean (the git hook covers this on commit)
- [ ] `uv run pytest -q` green
- [ ] Test added covering the new behaviour (`docs/dev/TESTING.md`)
- [ ] `news/<n>.feature.rst` fragment added
