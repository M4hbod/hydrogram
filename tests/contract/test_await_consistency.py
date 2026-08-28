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

"""No `await` on a parser that is not a coroutine, and none missing on one that is.

Kurigram made many `_parse` methods async that are synchronous here, so ported code arrives with
`await types.User._parse(...)` -- which raises ``TypeError: object User can't be used in 'await'
expression`` the first time that branch runs. It cannot be caught by importing the module, and the
branches are often reachable only with a specific message shape, so it survives casual testing.

A single sweep of the source catches every one. This found 44 of them across the stage-4.2 port.
"""

from __future__ import annotations

import inspect
import pathlib
import re

from pyrogram import types

PACKAGE = pathlib.Path(types.__file__).parent.parent
# The prefix is optional because call sites spell it both `types.X` and `pyrogram.types.X`.
AWAITED = re.compile(r"(await\s+)?(?:pyrogram\.)?\btypes\.(\w+)\.(_parse\w*)\(")


def source_files():
    generated = PACKAGE / "raw"
    return sorted(
        p for p in PACKAGE.rglob("*.py") if generated not in p.parents and p != generated
    )


def parser(cls_name: str, meth: str):
    cls = getattr(types, cls_name, None)
    if cls is None or not inspect.isclass(cls):
        return None
    fn = inspect.getattr_static(cls, meth, None)
    return fn.__func__ if isinstance(fn, staticmethod) else fn


def call_sites():
    for path in source_files():
        text = path.read_text(encoding="utf-8")
        for match in AWAITED.finditer(text):
            awaited, cls_name, meth = match.group(1), match.group(2), match.group(3)
            fn = parser(cls_name, meth)
            if fn is None or not inspect.isfunction(fn):
                continue
            line = text[: match.start()].count("\n") + 1
            yield path.relative_to(PACKAGE.parent), line, cls_name, meth, bool(awaited), fn


SITES = list(call_sites())


def test_the_sweep_found_call_sites():
    assert len(SITES) > 100, f"only {len(SITES)} parser call sites found; the scan is broken"


def test_no_synchronous_parser_is_awaited():
    offenders = [
        f"{path}:{line} awaits types.{cls}.{meth}"
        for path, line, cls, meth, awaited, fn in SITES
        if awaited and not inspect.iscoroutinefunction(fn)
    ]
    assert not offenders, "\n".join(offenders)


def test_no_coroutine_parser_is_left_unawaited():
    offenders = [
        f"{path}:{line} does not await types.{cls}.{meth}"
        for path, line, cls, meth, awaited, fn in SITES
        if not awaited and inspect.iscoroutinefunction(fn)
    ]
    assert not offenders, "\n".join(offenders)
