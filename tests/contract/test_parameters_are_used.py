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

"""A parameter a method accepts must reach the request it builds.

Adding a parameter to a signature is the easy half; wiring it into the RPC is
the half that gets forgotten, and the result is worse than a missing parameter
-- the call succeeds, the caller believes the option took effect, and nothing
says otherwise. This reads each method's own body and checks the name is used.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

import pyrogram

METHODS_ROOT = pathlib.Path(pyrogram.__file__).parent / "methods"

# Parameters whose whole job is to be handed to something else, and which a
# reader would not expect to see named again in the body.
PASSTHROUGH = {"self", "args", "kwargs"}

# Deliberately inert: accepted for signature compatibility with a sibling
# method, or consumed by a decorator rather than the body.
ALLOWED_UNUSED: dict[str, set[str]] = {}


def public_methods():
    for path in sorted(METHODS_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                if item.name.startswith("_"):
                    continue

                # An @overload stub is a signature with no body to use anything.
                if any(
                    getattr(d, "id", getattr(d, "attr", None)) == "overload"
                    for d in item.decorator_list
                ):
                    continue

                yield path.relative_to(METHODS_ROOT.parent.parent), item


CASES = [(str(path), fn.name, fn) for path, fn in public_methods()]


def used_names(fn: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)} | {
        kw.arg for n in ast.walk(fn) if isinstance(n, ast.Call) for kw in n.keywords if kw.arg
    }


@pytest.mark.parametrize(("path", "name", "fn"), CASES, ids=[f"{name}" for _, name, _ in CASES])
def test_every_parameter_reaches_the_body(path, name, fn):
    declared = (
        {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
        - PASSTHROUGH
        - ALLOWED_UNUSED.get(name, set())
    )

    unused = sorted(declared - used_names(fn))

    assert not unused, f"{path}:{fn.lineno} {name}() accepts {unused} and never uses them"
