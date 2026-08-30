#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Pyrogram <https://pyrogram.org>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

"""Every type carries the fields Kurigram's does.

The parity checks that came before this one compared *names* -- method names,
type names, enum class names. ``Chat`` exists in both trees, so a name-based
diff scored it closed while ours was missing 118 of its fields and ``User`` 76.
That is the same blindness that let ``raw.pyrogram.ClientDHInnerData`` ship:
checking that a name is present is not checking that it is right.

The reference tree is a Kurigram checkout. Without one the test skips rather
than pretends -- an unmeasured gap must not read as a closed one.

Set ``KURIGRAM_PATH`` to a checkout to run it.
"""

from __future__ import annotations

import ast
import inspect
import os
import pathlib

import pytest

from pyrogram import types

KURIGRAM = os.environ.get("KURIGRAM_PATH", "/tmp/kuri")
REFERENCE = pathlib.Path(KURIGRAM) / "pyrogram" / "types"

pytestmark = pytest.mark.skipif(
    not REFERENCE.is_dir(),
    reason=f"no Kurigram checkout at {KURIGRAM}; set KURIGRAM_PATH",
)

# Fields deliberately absent, with the reason. Anything not listed here is a gap.
DELIBERATE: dict[str, set[str]] = {
    # Bot API 7 replaced this with link_preview_options.
    "InputTextMessageContent": {"disable_web_page_preview"},
}


def reference_fields() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}

    for path in REFERENCE.rglob("*.py"):
        if "__pycache__" in str(path):
            continue

        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - reference tree is not ours to fix
            continue

        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                continue

            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    arguments = item.args

                    found[node.name] = {
                        argument.arg for argument in arguments.args + arguments.kwonlyargs
                    } - {"self"}

    return found


def our_fields(name: str) -> set[str] | None:
    cls = getattr(types, name, None)

    if cls is None or not inspect.isclass(cls):
        return None

    try:
        return set(inspect.signature(cls.__init__).parameters) - {"self"}
    except (ValueError, TypeError):  # pragma: no cover - builtins have no signature
        return None


REFERENCE_FIELDS = reference_fields()


def test_the_reference_tree_was_read():
    assert len(REFERENCE_FIELDS) > 200, (
        f"only {len(REFERENCE_FIELDS)} reference types found; the checkout looks wrong"
    )


def test_every_type_carries_the_reference_fields():
    gaps = {}

    for name, expected in sorted(REFERENCE_FIELDS.items()):
        ours = our_fields(name)

        if ours is None:
            continue

        missing = sorted(expected - ours - DELIBERATE.get(name, set()))

        if missing:
            gaps[name] = missing

    total = sum(len(missing) for missing in gaps.values())
    report = "\n".join(f"  {name}: {missing}" for name, missing in gaps.items())

    assert not gaps, f"{total} fields missing across {len(gaps)} types:\n{report}"
