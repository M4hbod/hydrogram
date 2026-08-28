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

"""The public surface must not drift silently.

Porting a type or method takes four edits -- the module, the subpackage ``__init__``, its
``__all__``, and (for methods) the mixin the ``Client`` inherits. Forgetting one produces a symbol
that exists on disk, is documented, and cannot be reached. These tests make that a failure rather
than a support question.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path

import pytest
from packaging.version import Version

import pyrogram
from pyrogram import emoji, enums, filters, types
from pyrogram.methods import Methods

PACKAGE_ROOT = Path(pyrogram.__file__).parent


@pytest.mark.parametrize("name", sorted(types.__all__))
def test_every_exported_type_resolves(name):
    assert getattr(types, name, None) is not None, (
        f"types.__all__ lists {name!r} but pyrogram.types has no such attribute"
    )


@pytest.mark.parametrize("name", sorted(enums.__all__))
def test_every_exported_enum_resolves(name):
    assert getattr(enums, name, None) is not None


def test_types_all_is_sorted():
    """Keeping __all__ sorted is what stops two ports from conflicting on the same line."""
    assert list(types.__all__) == sorted(types.__all__)


def test_enums_all_is_sorted():
    assert list(enums.__all__) == sorted(enums.__all__)


def method_modules() -> list[str]:
    root = PACKAGE_ROOT / "methods"
    return sorted(
        module.name
        for module in pkgutil.walk_packages([str(root)], "pyrogram.methods.")
        if not module.ispkg and not module.name.rsplit(".", 1)[-1].startswith("_")
    )


METHOD_MODULES = method_modules()


def test_method_scan_found_something():
    assert len(METHOD_MODULES) > 150, f"only {len(METHOD_MODULES)} method modules found"


@pytest.mark.parametrize("module_name", METHOD_MODULES)
def test_method_class_is_wired_into_the_client(module_name):
    """Every methods/<category>/<name>.py class must be a base of Client.

    A method file that is never added to its category mixin is dead code: importable, documented,
    and absent from the Client.
    """
    module = importlib.import_module(module_name)
    classes = [
        obj
        for _, obj in inspect.getmembers(module, inspect.isclass)
        if obj.__module__ == module_name
    ]
    if not classes:
        pytest.skip(f"{module_name} defines no class of its own")

    unwired = [cls.__name__ for cls in classes if not issubclass(Methods, cls)]
    assert not unwired, (
        f"{unwired} defined in {module_name} but not inherited by Methods; "
        f"add it to the category mixin in methods/<category>/__init__.py"
    )


def test_client_exposes_every_wired_method():
    """The mixin chain must actually produce callables on the Client."""
    missing = [
        name
        for name in dir(Methods)
        if not name.startswith("_") and not hasattr(pyrogram.Client, name)
    ]
    assert not missing


def test_filters_module_exposes_the_documented_builtins():
    for name in (
        "command",
        "private",
        "group",
        "channel",
        "text",
        "photo",
        "regex",
        "user",
        "chat",
    ):
        assert hasattr(filters, name), f"filters.{name} is missing"


def test_version_is_a_string_py_tgcalls_will_accept():
    """py-tgcalls declares `pyrogram>=1.2.20`; Hydrogram's own 0.2.0 failed that floor."""
    assert Version(pyrogram.__version__) >= Version("1.2.20"), (
        f"__version__ is {pyrogram.__version__}; py-tgcalls requires >=1.2.20"
    )


def test_emoji_module_is_present_for_pykeyboard():
    """pykeyboard does `from pyrogram.emoji import *`; the module has no upstream counterpart."""
    constants = [name for name in dir(emoji) if name.isupper()]
    assert len(constants) > 3000, f"pyrogram.emoji only exports {len(constants)} constants"
