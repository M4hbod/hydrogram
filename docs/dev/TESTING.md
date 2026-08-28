# Testing

## Why this document exists

As of 2026-08-28 the suite is **39 tests in 3 files** (`test_file_id.py`,
`filters/test_command.py`, `parser/test_html.py`). That is enough to prove the package imports and
not much else. The layer 223 → 229 upgrade touches serialization, keyboards, message parsing and
the connection layer — all of it currently unguarded.

Tests come **before** the upgrade, not after. A regression net built after a rewrite only proves
the rewrite is self-consistent.

## Layout

```
tests/
├── conftest.py                 # shared fixtures + directory-derived markers
├── unit/                       # no I/O, no network, no credentials — always run
│   ├── crypto/
│   ├── parser/
│   ├── filters/
│   ├── raw/                    # TL serialization round-trips
│   ├── session/
│   ├── storage/
│   ├── types/
│   └── utils/
├── contract/                   # the public surface must not drift silently
│   ├── test_public_api.py      # every symbol in __all__ imports; method mixins wired
│   ├── test_signatures.py      # snapshot of public method signatures
│   └── test_raw_references.py  # every raw.* reference in high-level code resolves
└── integration/                # needs network and/or a real session — opt-in only
    └── connection/
```

Markers are assigned from the directory in `conftest.py`, not by decorator — a directory cannot be
forgotten the way a decorator can:

| Directory | Marker | Runs in CI |
| --- | --- | --- |
| `tests/unit/` | `unit` | yes, always |
| `tests/contract/` | `contract` | yes, always |
| `tests/integration/` | `integration` | only when credentials are present |

Default command must never hit the network:

```bash
uv run pytest -q                    # unit + contract
uv run pytest -m integration        # opt-in, needs .env.test
```

## Required configuration

Add to `pyproject.toml` (currently missing — this is stage 1 work):

```toml
[tool.pytest.ini_options]
addopts = "-ra --strict-markers -m 'not integration'"
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "unit: no I/O, no network",
    "contract: public API surface guards",
    "integration: requires network and/or Telegram credentials",
]
```

`asyncio_mode = "auto"` matters: today an `async def test_*` would be silently collected and
skipped as a warning rather than run. Add it before writing any async test.

## What must be covered

Ranked by how much of the upgrade they protect.

### Tier 1 — must exist before any layer bump

| Area | What the test asserts |
| --- | --- |
| **Raw serialization round-trip** | For a representative sample of `raw.types` / `raw.functions`: `Type.read(BytesIO(obj.write()))` equals `obj`. Covers flags, optional vectors, nested constructors, `Bool`, `long`, `int128/256`, `bytes`, `string`. |
| **Constructor-ID stability** | Every `raw` class's `ID` matches the hash in `main_api.tl`. Catches a miscompiled TL immediately. |
| **`raw` reference resolution** | Walk every `.py` outside `pyrogram/raw/`, regex out `raw.(types\|functions\|base).X.Y`, assert each resolves. This is the single highest-value test for a layer bump: it turned up exactly 19 breakages when layer 229 was trial-compiled. |
| **Public API surface** | Import `pyrogram`; assert every name in `types.__all__`, `enums.__all__`, `filters` resolves; assert every `methods/**/xxx.py` class is a base of `Client`. |
| **`file_id` / `file_unique_id`** | Already partly covered — extend to every `FileType`, both directions. |
| **Parsers** | `test_html.py` exists; add `test_markdown.py` (Kurigram has one), plus entity offset/length correctness in UTF-16 units, nested and overlapping entities, and custom emoji entities. |
| **Filters** | Combinators (`&`, `\|`, `~`), `filters.command` with prefixes/case/mentions, update-attribute filters. |
| **Storage** | `BaseStorage` contract test parameterised over every backend; peer upsert/lookup by id, username, phone; session-string encode → decode round-trip for **each** historical `SESSION_STRING_FORMAT`. |
| **`utils`** | `get_peer_id` / `get_peer_type` / `get_channel_id` boundaries, `zero_datetime`, `timestamp_to_datetime`, `datetime_to_timestamp` round-trip. |

### Tier 2 — before shipping ported high-level code

| Area | What the test asserts |
| --- | --- |
| **Keyboards** | `InlineKeyboardMarkup` / `ReplyKeyboardMarkup` → `raw` → back, for every button variant, **including** our custom-emoji + style feature. This is the test that makes the layer-229 `ButtonType` redesign safe. |
| **Type `_parse` classmethods** | Each ported `types.X._parse(client, raw_obj)` fed a hand-built raw object, asserted field-by-field. No network. |
| **`Message` parsing** | The big one. Build `raw.types.Message` variants (media, service, reply, forward, topic, business, paid) and assert the parsed `Message`. |
| **Object protocol** | `str()`/`repr()`/`==` on every type; `eval(repr(obj))` round-trip; assert no `phone_number` and no raw MTProto blob leaks into `str()`. |
| **Enums** | Member names and values are frozen — a snapshot test, since renaming a member breaks users. |
| **Dispatcher** | Handler resolution order, filter short-circuit, `StopPropagation` / `ContinuePropagation`, `pyromod` listener interaction. |
| **Errors** | Generated exception tree: code → class mapping, `RPCError` subclass lookup, unknown-error fallback. |

### Tier 3 — integration, opt-in

Live tests read credentials from `.env.test` (git-ignored) and are skipped when absent. They cover
auth flow, DC migration, proxy transports and file upload/download against Telegram's **test**
DCs, never production. Never commit a session string or API hash.

## Conventions

- License header on every test file (see `AGENTS.md`).
- `from __future__ import annotations` — same rule as library code.
- One assertion subject per test; parameterise instead of looping.
- Fixtures build raw objects **by hand**. Do not record-and-replay Telegram responses into the repo;
  they go stale and can contain personal data.
- No `time.sleep`. No real sockets outside `tests/integration/`.
- A bug fix lands with a test that fails before the fix.

## Coverage

`pytest-cov` is already a dev dependency. `.coveragerc` does **not** exist yet — create it in
stage 1 with `pyrogram/raw/` and `pyrogram/errors/exceptions/` omitted. Target, enforced in CI once
stage 1 lands:

```bash
uv run pytest --cov=pyrogram --cov-report=term-missing \
  --cov-fail-under=60 \
  --cov-config=.coveragerc
```

`pyrogram/raw/` is excluded from coverage — it is generated and covered structurally by the
round-trip and constructor-ID tests instead. 60 % is the entry bar for the non-generated tree;
raise it as stages complete.

## Running them automatically

Style is handled by the pre-commit hook — do not run `ruff` by hand (see `CLAUDE.md`). Tests are
not on the commit stage, because commits must stay fast. Put them on `pre-push` instead:

```yaml
# .pre-commit-config.yaml
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest (unit + contract)
        entry: uv run pytest -q -m "not integration"
        language: system
        pass_filenames: false
        stages: [pre-push]
```

installed with `uv run pre-commit install --hook-type pre-push`. Once the stage-1
`raw`-reference check exists, add it to the **commit** stage — it is fast and catches the
highest-value class of breakage.

## CI

`.github/workflows/python.yml` runs `make api` then `uv run pytest` on
{ubuntu, macos} × py3.9–3.13, and has passed on every push. `code-style.yml` was failing on 5
unformatted files until `77b0dc1d`. Extend them to:

1. run `pytest -m "not integration"` explicitly,
2. upload coverage,
3. add a `windows-latest` leg (storage paths and `asyncio` event-loop policy differ),
4. add a scheduled job running `make check-api-schema` so layer drift is noticed within a day.
