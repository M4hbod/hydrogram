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

"""Every exported type obeys the `Object` protocol.

A ported type that imports cleanly can still be unusable: a constructor that raises, a `__str__`
that blows up on a nested value, an `__all__` entry pointing at something that is not a type. This
sweeps the whole public surface rather than trusting each port to have been checked by hand.

It is deliberately shallow -- construct, serialise, compare -- because that is what can be asserted
uniformly. Behaviour that depends on a specific raw constructor is tested next to that type.
"""

from __future__ import annotations

import inspect
import json

import pytest

from pyrogram import types
from pyrogram.types.object import Object

# `types.__all__` re-exports the submodules alongside the classes, so filter to classes.
EXPORTED = sorted(types.__all__)
CLASSES = [(n, getattr(types, n)) for n in EXPORTED if inspect.isclass(getattr(types, n, None))]

# Legitimately not Objects: pyromod internals, an Enum, the Update base, and a list subclass.
NOT_OBJECTS = {"Identifier", "List", "Listener", "ListenerTypes", "Update"}

# Types whose constructor needs a live client or a raw object to mean anything.
NEEDS_ARGS = {
    n
    for n, c in CLASSES
    if any(
        p.default is inspect.Parameter.empty
        for k, p in inspect.signature(c.__init__).parameters.items()
        if k not in {"self", "args", "kwargs"} and p.kind is not inspect.Parameter.VAR_KEYWORD
    )
}
CONSTRUCTIBLE = [(n, c) for n, c in CLASSES if n not in NEEDS_ARGS and n not in NOT_OBJECTS]


def test_the_surface_is_big_enough_to_be_meaningful():
    assert len(CLASSES) > 250, f"only {len(CLASSES)} exported classes; the scan is broken"


def test_enough_types_are_constructible_to_make_the_sweep_worthwhile():
    """Most ported types have required fields, so this is a floor, not a target."""
    assert len(CONSTRUCTIBLE) > 60, f"only {len(CONSTRUCTIBLE)} types take no required arguments"


@pytest.mark.parametrize(("name", "cls"), CLASSES, ids=[n for n, _ in CLASSES])
def test_every_exported_type_is_an_object(name, cls):
    if name in NOT_OBJECTS:
        pytest.skip(f"{name} is deliberately not an Object")
    assert issubclass(cls, Object), f"{name} does not derive from Object"


@pytest.mark.parametrize(("name", "cls"), CONSTRUCTIBLE, ids=[n for n, _ in CONSTRUCTIBLE])
def test_constructs_and_serialises(name, cls):
    obj = cls()

    text = str(obj)
    payload = json.loads(text)
    assert payload["_"] == name, f"str() reports {payload['_']!r}, not {name!r}"
    assert "raw" not in payload, "the raw MTProto object must never be serialised"

    assert repr(obj).startswith("pyrogram.types."), repr(obj)[:60]
    assert obj == cls(), "two default instances must compare equal"
