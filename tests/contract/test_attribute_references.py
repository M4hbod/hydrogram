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

"""Every dotted name hand-written code reaches for actually resolves.

The generalisation of ``test_raw_references``. That one resolved
``raw.types.X`` and ``raw.functions.X``; a typo that changed the *namespace* --
``raw.pyrogram.ClientDHInnerData`` -- was never entered into the checked set, so
it shipped, and it broke every DH key exchange, which is every fresh login. The
`test_no_unknown_raw_namespace` guard closes that for ``raw``.

This closes the rest of the shape: whatever the root, whatever the depth, the
chain must resolve. It covers what neither of those did -- ``enums.X.MEMBER``,
where a missing member is an ``AttributeError`` on the line that builds a
service message.

Docstrings count. A ``:obj:`~pyrogram.enums.ChatEvenAction.CREATED_FORUM_TOPIC```
is a broken doc link rather than a crash, but it is the same typo made in the
same place, and there is no reason to let one through while catching the other.
Commented-out lines do not: they are dead code, and message.py has TODO blocks
naming passport service types that were never implemented.
"""

from __future__ import annotations

import pathlib
import re

import pyrogram
from pyrogram import enums, filters, handlers, raw, types

PACKAGE = pathlib.Path(pyrogram.__file__).parent
GENERATED = PACKAGE / "raw"

ROOTS = {
    "raw": raw,
    "types": types,
    "enums": enums,
    "filters": filters,
    "handlers": handlers,
}

REFERENCE = re.compile(r"\b(?:pyrogram\.)?(raw|types|enums|filters|handlers)\.((?:\w+\.)*\w+)")

# Names that are locals or parameters shadowing a module name, or attributes of
# something that only looks like one of our namespaces. Each is a real line of
# code doing something legitimate, so they are named rather than pattern-matched.
IGNORED = {
    # `filters` and `handlers` as parameter names on the decorators and handlers
    "filters.__call__",
    "filters.write",
    "handlers.append",
    # `raw`'s own sub-namespaces reached through `types.`
    "types.messages.BotResults",
    "types.contacts.ImportedContacts",
    # private, so name-mangled at runtime
    "types.Message.__parse_reply",
}


def source_files():
    return sorted(path for path in PACKAGE.rglob("*.py") if GENERATED not in path.parents)


def resolve(root_name: str, dotted: str):
    obj = ROOTS[root_name]

    for part in dotted.split("."):
        obj = getattr(obj, part, None)

        if obj is None:
            return None

    return obj


def references():
    for path in source_files():
        text = path.read_text(encoding="utf-8")

        lines = text.splitlines()

        for match in REFERENCE.finditer(text):
            root_name, dotted = match.group(1), match.group(2)

            if f"{root_name}.{dotted}" in IGNORED:
                continue

            line = text[: match.start()].count("\n") + 1

            # A commented-out line is dead code -- message.py carries two TODO
            # blocks naming passport service types that are not implemented.
            # A docstring is published documentation and still counts.
            if lines[line - 1].lstrip().startswith("#"):
                continue

            yield str(path.relative_to(PACKAGE.parent)), line, root_name, dotted


REFERENCES = sorted(set(references()))


def test_the_sweep_found_references():
    assert len(REFERENCES) > 2000, f"only {len(REFERENCES)} references found; the scan is broken"


def test_every_dotted_reference_resolves():
    offenders = [
        f"{path}:{line} names {root}.{dotted}, which does not resolve"
        for path, line, root, dotted in REFERENCES
        if resolve(root, dotted) is None
    ]

    assert not offenders, "\n".join(offenders)


def test_every_enum_member_reference_resolves():
    """Called out separately because a missing member is a crash, not a bad link."""
    offenders = [
        f"{path}:{line} names enums.{dotted}"
        for path, line, root, dotted in REFERENCES
        if root == "enums" and "." in dotted and resolve(root, dotted) is None
    ]

    assert not offenders, "\n".join(offenders)
