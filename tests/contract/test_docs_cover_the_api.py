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

"""The generated API pages cover the public surface.

The lists behind these pages used to be written by hand, and drifted: 71 methods
and 128 types had no page by the time anyone looked. They are derived from the
package now, and this is what keeps the derivation honest -- a method in a group
the compiler does not know about, or a type in a new subpackage, silently
vanishes from the docs otherwise.
"""

from __future__ import annotations

import inspect
import pathlib

import pytest

import pyrogram
import pyrogram.enums
from compiler.docs.compiler import (
    METHOD_SECTIONS,
    TYPE_SECTIONS,
    client_methods_by_group,
    types_by_group,
)
from pyrogram import types

PACKAGE = pathlib.Path(pyrogram.__file__).parent

# Machinery, not API: nothing here is something a caller reaches for, and each
# is named rather than matched by a pattern so a new one has to be considered.
INTERNAL_METHODS = {
    "authorize",
    "business_connection_session",
    "fetch_peers",
    "get_file",
    "get_session",
    "guess_extension",
    "guess_mime_type",
    "handle_download",
    "handle_updates",
    "load_plugins",
    "load_session",
    "updates_watchdog",
}

# Base classes and the list container, which live at the root of types/ rather
# than in one of the documented groups.
UNGROUPED_TYPES = {"List", "Object", "Update"}


def test_every_method_group_has_a_section():
    groups = {
        path.name
        for path in (PACKAGE / "methods").iterdir()
        if path.is_dir() and not path.name.startswith("__")
    }

    assert not groups - set(METHOD_SECTIONS), (
        f"these method groups have no docs section: {sorted(groups - set(METHOD_SECTIONS))}"
    )


def test_every_type_group_has_a_section():
    groups = {
        path.name
        for path in (PACKAGE / "types").iterdir()
        if path.is_dir() and not path.name.startswith("__")
    }

    assert not groups - set(TYPE_SECTIONS), (
        f"these type groups have no docs section: {sorted(groups - set(TYPE_SECTIONS))}"
    )


def test_every_public_client_method_is_documented():
    documented = {name for names in client_methods_by_group().values() for name in names}
    public = {
        name
        for name in dir(pyrogram.Client)
        if not name.startswith("_") and callable(getattr(pyrogram.Client, name, None))
    }

    undocumented = sorted(public - documented - INTERNAL_METHODS)

    assert not undocumented, f"no docs page for: {undocumented}"


def test_every_exported_type_is_documented():
    documented = {name for names in types_by_group().values() for name in names}
    # __all__ also carries the submodule re-exports ruff maintains; only the
    # classes get a page.
    exported = {name for name in types.__all__ if name[0].isupper()}

    undocumented = sorted(exported - documented - UNGROUPED_TYPES)

    assert not undocumented, f"no docs page for: {undocumented}"


@pytest.mark.parametrize("name", sorted(n for n in types.__all__ if n[0].isupper()))
def test_every_capitalised_name_in_all_is_a_class(name):
    """``__all__`` also carries the submodule names, which ruff maintains.

    ``from pyrogram.types import *`` therefore binds both ``animation`` the
    module and ``Animation`` the class. They differ in case and nothing
    shadows anything, so this checks the half that is meant to be classes and
    leaves the re-exports alone rather than fighting the formatter over them.
    """
    assert inspect.isclass(getattr(types, name)), f"types.{name} is not a class"


def test_every_enum_is_documented():
    """The enum pages are generated too, and were 29 behind before they were."""
    pages = {path.stem for path in (PACKAGE.parent / "docs/source/api/enums").glob("*.rst")}

    undocumented = sorted(set(pyrogram.enums.__all__) - pages)

    assert not undocumented, f"no docs page for: {undocumented}"
