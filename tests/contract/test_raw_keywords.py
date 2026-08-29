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

"""Every keyword handed to a raw constructor is one that constructor accepts.

``test_raw_references.py`` proves the name resolves; this proves the call would
go through. Raw types take keyword-only arguments, so a wrong or stale field
name is a ``TypeError`` raised the first time that branch runs -- which for a
send method means the first time somebody uses that one option.
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

import pyrogram
from pyrogram import raw

PACKAGE = pathlib.Path(pyrogram.__file__).parent


def resolve(dotted: str):
    obj = raw

    for part in dotted.split("."):
        obj = getattr(obj, part, None)

        if obj is None:
            return None

    return obj


def dotted_name(node: ast.AST) -> str | None:
    parts = []

    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value

    if not isinstance(node, ast.Name) or node.id != "raw":
        return None

    return ".".join(reversed(parts))


def raw_calls():
    generated = PACKAGE / "raw"

    for path in sorted(PACKAGE.rglob("*.py")):
        if generated in path.parents:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = dotted_name(node.func)

            if name is None or not name.startswith(("types.", "functions.")):
                continue

            keywords = tuple(sorted({kw.arg for kw in node.keywords if kw.arg is not None}))

            if keywords:
                yield str(path.relative_to(PACKAGE.parent)), node.lineno, name, keywords


CALLS = sorted(set(raw_calls()))


def test_the_sweep_found_calls():
    assert len(CALLS) > 500, f"only {len(CALLS)} raw calls found; the scan is broken"


@pytest.mark.parametrize(
    ("path", "line", "name", "keywords"),
    CALLS,
    ids=[f"{name}:{line}" for _, line, name, _ in CALLS],
)
def test_the_raw_constructor_accepts_every_keyword(path, line, name, keywords):
    cls = resolve(name)

    if cls is None:
        pytest.fail(f"{path}:{line} names raw.{name}, which does not exist")

    parameters = inspect.signature(cls.__init__).parameters
    unexpected = [kw for kw in keywords if kw not in parameters]

    assert not unexpected, (
        f"{path}:{line} passes {unexpected} to raw.{name}, which has no such field"
    )
