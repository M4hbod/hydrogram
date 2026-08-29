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

"""A bound method may only pass keywords the client method actually accepts.

``message.reply_photo(...)`` is a shortcut that fills in ``chat_id`` and
``reply_parameters`` and hands the rest to ``Client.send_photo``. When the client
method's signature moves and the shortcut does not, the call raises
``TypeError: got an unexpected keyword argument`` -- but only for whoever calls
that one shortcut, which is how a bound method can sit broken for a whole
release. This walks the call in the source instead of waiting for a user.
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

import pyrogram
from pyrogram import types

TYPES_ROOT = pathlib.Path(types.__file__).parent


def delegating_calls():
    """Every `self._client.X(...)` call, with the keywords it passes."""
    for path in sorted(TYPES_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func = node.func

            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "_client"
                and isinstance(func.value.value, ast.Name)
                and func.value.value.id == "self"
            ):
                keywords = sorted({kw.arg for kw in node.keywords if kw.arg is not None})
                yield (
                    str(path.relative_to(TYPES_ROOT.parent.parent)),
                    node.lineno,
                    func.attr,
                    tuple(keywords),
                )


CALLS = sorted(set(delegating_calls()))


def test_the_sweep_found_calls():
    assert len(CALLS) > 100, f"only {len(CALLS)} delegating calls found; the scan is broken"


@pytest.mark.parametrize(
    ("path", "line", "method", "keywords"),
    CALLS,
    ids=[f"{path.split('/')[-1]}:{line}:{method}" for path, line, method, _ in CALLS],
)
def test_the_client_method_accepts_every_keyword(path, line, method, keywords):
    fn = getattr(pyrogram.Client, method, None)

    if fn is None:
        pytest.fail(f"{path}:{line} calls Client.{method}, which does not exist")

    parameters = inspect.signature(fn).parameters

    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values()):
        pytest.skip(f"Client.{method} takes **kwargs")

    unexpected = [name for name in keywords if name not in parameters]

    assert not unexpected, (
        f"{path}:{line} passes {unexpected} to Client.{method}, which does not accept them"
    )
