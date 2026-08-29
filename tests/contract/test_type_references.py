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

"""Every ``types.X`` named in hand-written code exists.

The sibling of ``test_raw_references.py``, for the other half of the namespace.
A ``types.X`` that does not exist raises ``AttributeError`` only when its line
runs -- and in the dispatcher's routing table that means the handler worker logs
it and moves on, so the symptom is an update type that never arrives. Eight
types were in that state: ``PreCheckoutQuery``, ``ShippingQuery``,
``MessageReactionUpdated``, ``MessageReactionCountUpdated``, ``ChatBoostUpdated``,
``BusinessConnection``, ``ManagedBotUpdated`` and ``PurchasedPaidMedia``.
"""

from __future__ import annotations

import pathlib
import re

from pyrogram import types

PACKAGE = pathlib.Path(types.__file__).parent.parent

# `types.X` and `pyrogram.types.X`, but only where X is a class name -- the
# lowercase attribute accesses are instances and are not what this guards.
REFERENCE = re.compile(r"(?<!raw\.)(?:pyrogram\.)?\btypes\.([A-Z]\w*)")

# Names that appear inside a string or a docstring rather than as code. Kept
# explicit so a genuinely missing type cannot hide behind a broad rule.
IGNORED_FILES = {"pyrogram/types/__init__.py"}


def source_files():
    generated = PACKAGE / "raw"

    return sorted(
        path
        for path in PACKAGE.rglob("*.py")
        if generated not in path.parents
        and str(path.relative_to(PACKAGE.parent)) not in IGNORED_FILES
    )


def references():
    for path in source_files():
        text = path.read_text(encoding="utf-8")

        for match in REFERENCE.finditer(text):
            line = text[: match.start()].count("\n") + 1
            yield path.relative_to(PACKAGE.parent), line, match.group(1)


REFERENCES = sorted(set(references()))


def test_the_sweep_found_references():
    assert len(REFERENCES) > 500, (
        f"only {len(REFERENCES)} type references found; the scan is broken"
    )


def test_every_referenced_type_resolves():
    offenders = [
        f"{path}:{line} names types.{name}, which does not exist"
        for path, line, name in REFERENCES
        if not hasattr(types, name)
    ]

    assert not offenders, "\n".join(offenders)
