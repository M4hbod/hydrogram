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

"""The filters name every update type that carries the field they read.

A filter that takes ``update.chat`` off whatever it is handed raises
``AttributeError`` on the update types that have no chat -- inside the handler
worker, where it is logged and swallowed, so the handler simply never runs.
Naming the types instead makes the filter not match, which is the right answer.

These tests fail when a newly ported update type gains one of these fields and
the tuple is not extended, which is the only way the two can drift.
"""

from __future__ import annotations

import inspect

import pytest

from pyrogram import filters, types
from pyrogram.types.update import Update

FIELDS = {
    "from_user": filters._WITH_A_SENDER,
    "chat": filters._WITH_A_CHAT,
    "sender_chat": filters._WITH_A_SENDER_CHAT,
    "outgoing": filters._CAN_BE_OUTGOING,
}


def update_types():
    for name in types.__all__:
        cls = getattr(types, name)

        if inspect.isclass(cls) and issubclass(cls, Update) and cls is not Update:
            yield name, cls


UPDATE_TYPES = sorted(update_types())


def carries(cls, field: str) -> bool:
    return field in inspect.signature(cls.__init__).parameters


@pytest.mark.parametrize(("field", "named"), FIELDS.items())
def test_every_update_type_that_carries_the_field_is_named(field, named):
    missing = sorted(
        name for name, cls in UPDATE_TYPES if carries(cls, field) and cls not in named
    )

    assert not missing, f"these carry .{field} but are not in the tuple: {missing}"


@pytest.mark.parametrize(("field", "named"), FIELDS.items())
def test_no_named_type_is_missing_the_field(field, named):
    # A type named here but without the field would raise the AttributeError the
    # tuple exists to prevent.
    missing = sorted(cls.__name__ for cls in named if not carries(cls, field))

    assert not missing, f"these are named for .{field} but do not carry it: {missing}"


def test_a_callback_query_reaches_its_chat_through_its_message():
    # It has no chat of its own, but a filter on the chat a button was pressed in
    # is the obvious thing to want, so it goes through the message.
    assert not carries(types.CallbackQuery, "chat")
    assert types.CallbackQuery in filters._WITH_A_MESSAGE
