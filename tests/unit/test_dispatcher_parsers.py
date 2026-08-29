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

"""The dispatcher's routing table, driven with real raw updates.

A parser that raises is caught and logged by the handler worker, so a broken one
does not stop the client -- it just means that update type never reaches a
handler. That is why these are asserted here rather than noticed in production.
"""

from __future__ import annotations

import inspect

import pytest

import pyrogram
from pyrogram import enums, raw
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers import (
    ChatMemberUpdatedHandler,
    DeletedMessagesHandler,
    InlineQueryHandler,
    UserStatusHandler,
)


@pytest.fixture
def dispatcher():
    return Dispatcher(pyrogram.Client("test", api_id=1, api_hash="x", in_memory=True))


async def dispatch(dispatcher: Dispatcher, update, users=None, chats=None):
    """Exactly what handler_worker does with one update."""
    parser = dispatcher.update_parsers[type(update)]
    parsed = parser(update, users or {}, chats or {})

    return await parsed if inspect.isawaitable(parsed) else parsed


async def test_deleted_messages_are_parsed(dispatcher):
    update = raw.types.UpdateDeleteMessages(messages=[11, 12], pts=1, pts_count=2)

    parsed, handler = await dispatch(dispatcher, update)

    assert handler is DeletedMessagesHandler
    assert [message.id for message in parsed] == [11, 12]
    assert parsed[0].chat is None


async def test_deleted_channel_messages_carry_their_chat(dispatcher):
    update = raw.types.UpdateDeleteChannelMessages(
        channel_id=1234567890, messages=[7], pts=1, pts_count=1
    )

    parsed, _handler = await dispatch(dispatcher, update)

    assert parsed[0].chat.id == -1001234567890
    assert parsed[0].chat.type is enums.ChatType.CHANNEL


async def test_user_status_is_parsed(dispatcher):
    update = raw.types.UpdateUserStatus(user_id=7, status=raw.types.UserStatusOnline(expires=0))

    parsed, handler = await dispatch(dispatcher, update)

    assert handler is UserStatusHandler
    assert parsed.id == 7
    assert parsed.status is enums.UserStatus.ONLINE


async def test_inline_query_is_parsed(dispatcher):
    user = raw.types.User(id=7, first_name="Test", access_hash=0)
    update = raw.types.UpdateBotInlineQuery(
        query_id=1,
        user_id=7,
        query="search",
        offset="",
        peer_type=raw.types.InlineQueryPeerTypePM(),
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: user})

    assert handler is InlineQueryHandler
    assert parsed.query == "search"
    assert parsed.from_user.id == 7


async def test_chat_member_update_is_parsed(dispatcher):
    user = raw.types.User(id=7, first_name="Test", access_hash=0)
    update = raw.types.UpdateChatParticipant(
        chat_id=99,
        date=1700000000,
        actor_id=7,
        user_id=7,
        qts=1,
        new_participant=raw.types.ChatParticipant(user_id=7, inviter_id=7, date=1700000000),
    )

    chat = raw.types.Chat(
        id=99, title="Group", photo=None, participants_count=1, date=1700000000, version=1
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: user}, chats={99: chat})

    assert handler is ChatMemberUpdatedHandler
    assert parsed.chat.id == -99
