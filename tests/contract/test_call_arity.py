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

"""Calls into our own types pass a number of arguments the target accepts.

``CallbackQuery._parse`` takes ``(client, callback_query, users)``. The
dispatcher called it with ``chats`` as a fourth. Every inline-keyboard button
press raised ``TypeError`` inside ``handler_worker``, which logs and swallows,
so nothing crashed -- the buttons just did nothing. A canary ran through
startup, auth and an hour of traffic before a button press found it.

The existing guards could not see it. ``test_await_consistency`` checks whether
a call is awaited, not how many arguments it passes;
``test_bound_method_delegation`` checks keywords against ``Client`` methods, not
positionals against type methods; and ``test_dispatcher_parsers`` had a
live-shape test for every update kind gained in the layer-229 port except this
one, because callback queries predate that port.

Positional count is the half that was unguarded, so this guards it.
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import pyrogram
from pyrogram import types

PACKAGE = pathlib.Path(pyrogram.__file__).parent
GENERATED = PACKAGE / "raw"


def source_files():
    return sorted(path for path in PACKAGE.rglob("*.py") if GENERATED not in path.parents)


def target(class_name: str, method: str):
    cls = getattr(types, class_name, None)

    if cls is None or not inspect.isclass(cls):
        return None

    fn = inspect.getattr_static(cls, method, None)
    fn = fn.__func__ if isinstance(fn, staticmethod) else fn

    return fn if inspect.isfunction(fn) else None


def calls():
    """`types.X.method(...)` calls, with how many positionals they pass."""
    for path in source_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - guarded elsewhere
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue

            owner = node.func.value

            # types.X.method(...) / pyrogram.types.X.method(...)
            if not isinstance(owner, ast.Attribute) or not owner.attr[:1].isupper():
                continue

            yield (
                str(path.relative_to(PACKAGE.parent)),
                node.lineno,
                owner.attr,
                node.func.attr,
                len(node.args),
                tuple(kw.arg for kw in node.keywords if kw.arg),
            )


CALLS = sorted(set(calls()))


def test_the_sweep_found_calls():
    assert len(CALLS) > 100, f"only {len(CALLS)} calls found; the scan is broken"


def test_no_call_passes_more_positionals_than_the_target_takes():
    offenders = []

    for path, line, class_name, method, given, _keywords in CALLS:
        fn = target(class_name, method)

        if fn is None:
            continue

        parameters = list(inspect.signature(fn).parameters.values())

        if any(p.kind is p.VAR_POSITIONAL for p in parameters):
            continue

        accepts = len([
            p for p in parameters if p.kind in {p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD}
        ])

        if given > accepts:
            offenders.append(
                f"{path}:{line} passes {given} positionals to types.{class_name}.{method}, "
                f"which takes {accepts}"
            )

    assert not offenders, "\n".join(offenders)


def test_no_call_passes_a_keyword_the_target_lacks():
    offenders = []

    for path, line, class_name, method, _given, keywords in CALLS:
        fn = target(class_name, method)

        if fn is None:
            continue

        parameters = inspect.signature(fn).parameters

        if any(p.kind is p.VAR_KEYWORD for p in parameters.values()):
            continue

        unexpected = [name for name in keywords if name not in parameters]

        if unexpected:
            offenders.append(f"{path}:{line} passes {unexpected} to types.{class_name}.{method}")

    assert not offenders, "\n".join(offenders)
