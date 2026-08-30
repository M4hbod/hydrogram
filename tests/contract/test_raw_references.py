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

"""Every ``raw.*`` name used by hand-written code must exist in the compiled layer.

This is the cheapest high-value guard against a TL layer bump. Annotations are lazy and most
``raw`` references sit inside branches that only a live Telegram response reaches, so a renamed
or removed constructor does not fail at import -- it fails in production, months later, on one
message shape. Walking the source for ``raw.types.X`` / ``raw.functions.y.Z`` and resolving each
one turns that into a collection-time failure.

When layer 229 was trial-compiled against this tree, this check found exactly 19 broken
references: six forum-topic functions that moved from ``channels.*`` to ``messages.*``, twelve
keyboard-button constructors replaced by the ``ButtonType`` union, and one long-standing typo.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from pyrogram import raw

PACKAGE_ROOT = Path(raw.__file__).parent.parent
GENERATED = PACKAGE_ROOT / "raw"

# `raw.types.Foo`, `raw.functions.messages.SendMessage`, `raw.base.Update`.
REFERENCE_RE = re.compile(r"\braw\.(types|functions|base)((?:\.[A-Za-z_][A-Za-z0-9_]*)+)")

# Any `raw.<namespace>.<something>` at all, regardless of whether <namespace> is one this suite
# already knows to resolve. A typo'd namespace (`raw.pyrogram.Foo` for `raw.types.Foo`) does not
# match REFERENCE_RE above, so it silently never gets resolved-checked -- this is what actually
# shipped once. KNOWN_NAMESPACES is every namespace `raw` legitimately exposes to hand-written
# code; anything else here is a typo, not a new namespace.
NAMESPACE_RE = re.compile(r"\braw\.([A-Za-z_][A-Za-z0-9_]*)\.")
KNOWN_NAMESPACES = {"types", "functions", "base", "core"}


def source_files() -> list[Path]:
    return sorted(
        path
        for path in PACKAGE_ROOT.rglob("*.py")
        if GENERATED not in path.parents and path != GENERATED
    )


def references_in(path: Path) -> set[str]:
    return {
        f"raw.{match.group(1)}{match.group(2)}"
        for match in REFERENCE_RE.finditer(path.read_text(encoding="utf-8"))
    }


def resolves(dotted: str) -> bool:
    obj = raw
    for part in dotted.split(".")[1:]:
        obj = getattr(obj, part, None)
        if obj is None:
            return False
    return True


def unknown_namespaces_in(path: Path) -> set[str]:
    return {
        match.group(1)
        for match in NAMESPACE_RE.finditer(path.read_text(encoding="utf-8"))
        if match.group(1) not in KNOWN_NAMESPACES
    }


ALL_REFERENCES = sorted({ref for path in source_files() for ref in references_in(path)})
UNKNOWN_NAMESPACES = sorted({
    (str(path), ns) for path in source_files() for ns in unknown_namespaces_in(path)
})


def test_the_scan_found_something():
    """A regex that silently stops matching would make every other test here vacuous."""
    assert len(ALL_REFERENCES) > 300, (
        f"only {len(ALL_REFERENCES)} raw references found; the scan is probably broken"
    )


@pytest.mark.parametrize("reference", ALL_REFERENCES)
def test_raw_reference_resolves(reference):
    assert resolves(reference), (
        f"{reference} does not exist in the compiled layer {raw.all.layer}. "
        f"It was renamed, moved namespace, or removed."
    )


def test_no_unknown_raw_namespace():
    """Catches `raw.pyrogram.Foo`-style typos that REFERENCE_RE's fixed namespace list misses.

    Regression test for session/auth.py's `raw.pyrogram.ClientDHInnerData`, which does not exist
    (it should have been `raw.types.ClientDHInnerData`) and broke every DH key exchange, i.e.
    every fresh login, without failing any existing test.
    """
    assert not UNKNOWN_NAMESPACES, (
        f"raw.<X>.Y reference(s) use a namespace outside {sorted(KNOWN_NAMESPACES)}: "
        f"{UNKNOWN_NAMESPACES}. This is almost certainly a typo for one of types/functions/base."
    )


def test_no_source_file_is_syntactically_broken():
    """Cheap guard: the reference scan is textual, so it cannot notice a file that no longer parses."""
    for path in source_files():
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:  # pragma: no cover - only reached when something is broken
            pytest.fail(f"{path} does not parse: {exc}")
