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

"""`utils.get_reply_to` — the single place a send call decides what it is replying to.

Layer 229 has four `InputReplyTo` constructors and `ReplyParameters` maps onto them field for
field, so the job is dispatch rather than translation. Every send method routes through here, which
makes a mistake here a mistake everywhere.
"""

from __future__ import annotations

import pytest

from pyrogram import enums, raw, types, utils
from pyrogram.parser import Parser


class FakeClient:
    """Resolves peers; nothing else is reachable from get_reply_to."""

    def __init__(self):
        self.resolved = []
        # Quote text goes through the real parser; it is the same code a live client uses.
        self.parser = Parser(None)
        self.parse_mode = enums.ParseMode.DEFAULT

    async def resolve_peer(self, peer_id):
        self.resolved.append(peer_id)
        if peer_id is None:
            # The real client would go to storage.get_peer_by_id(None) and raise. Making the
            # stub loud here is the point: get_reply_to must never call it with None.
            raise AssertionError("resolve_peer(None) must never be called")
        return raw.types.InputPeerUser(user_id=777000, access_hash=1)


async def test_nothing_to_reply_to_is_none():
    assert await utils.get_reply_to(FakeClient()) is None


async def test_a_thread_id_alone_still_produces_a_reply_header():
    """Replying to the topic's root message is how a message is scoped to a forum topic."""
    reply_to = await utils.get_reply_to(FakeClient(), None, message_thread_id=42)
    assert isinstance(reply_to, raw.types.InputReplyToMessage)
    assert reply_to.reply_to_msg_id == 42
    assert reply_to.top_msg_id == 42


async def test_a_plain_message_reply():
    reply_to = await utils.get_reply_to(FakeClient(), types.ReplyParameters(message_id=5))
    assert isinstance(reply_to, raw.types.InputReplyToMessage)
    assert reply_to.reply_to_msg_id == 5
    assert reply_to.reply_to_peer_id is None


async def test_a_reply_inside_a_thread_carries_both_ids():
    reply_to = await utils.get_reply_to(
        FakeClient(), types.ReplyParameters(message_id=5), message_thread_id=42
    )
    assert reply_to.reply_to_msg_id == 5
    assert reply_to.top_msg_id == 42


async def test_a_cross_chat_reply_resolves_the_peer():
    client = FakeClient()
    reply_to = await utils.get_reply_to(client, types.ReplyParameters(message_id=5, chat_id="me"))
    assert reply_to.reply_to_peer_id is not None
    assert client.resolved == ["me"]


async def test_a_same_chat_reply_never_resolves_a_peer():
    """Regression: resolve_peer(None) raises, so it must be called only when chat_id is set."""
    client = FakeClient()
    await utils.get_reply_to(client, types.ReplyParameters(message_id=5))
    assert client.resolved == []


async def test_a_story_reply():
    reply_to = await utils.get_reply_to(
        FakeClient(), types.ReplyParameters(story_id=9, chat_id="me")
    )
    assert isinstance(reply_to, raw.types.InputReplyToStory)
    assert reply_to.story_id == 9


async def test_a_story_reply_without_a_chat_is_rejected():
    """inputReplyToStory has no optional peer; a story is always in someone's profile."""
    with pytest.raises(ValueError, match="chat_id is required"):
        await utils.get_reply_to(FakeClient(), types.ReplyParameters(story_id=9))


async def test_an_ephemeral_message_reply():
    reply_to = await utils.get_reply_to(
        FakeClient(), types.ReplyParameters(ephemeral_message_id=11)
    )
    assert isinstance(reply_to, raw.types.InputReplyToEphemeralMessage)
    assert reply_to.id == 11


async def test_a_checklist_task_reply():
    reply_to = await utils.get_reply_to(
        FakeClient(), types.ReplyParameters(message_id=5, checklist_task_id=3)
    )
    assert reply_to.todo_item_id == 3


async def test_a_poll_option_reply_is_encoded_to_bytes():
    """poll_option is `bytes` on the wire, but a str in the public API."""
    reply_to = await utils.get_reply_to(
        FakeClient(), types.ReplyParameters(message_id=5, poll_option_id="opt-1")
    )
    assert reply_to.poll_option == b"opt-1"


async def test_a_quote_is_parsed_into_text_and_entities():
    reply_to = await utils.get_reply_to(
        FakeClient(),
        types.ReplyParameters(message_id=5, quote="**bold**", quote_position=7),
    )
    assert reply_to.quote_text == "bold"
    assert reply_to.quote_entities
    assert reply_to.quote_offset == 7


async def test_no_quote_leaves_the_quote_fields_unset():
    reply_to = await utils.get_reply_to(FakeClient(), types.ReplyParameters(message_id=5))
    assert reply_to.quote_text is None
    assert reply_to.quote_entities is None


async def test_story_wins_over_message_id():
    """A ReplyParameters carrying both is ambiguous; story is checked first and documented so."""
    reply_to = await utils.get_reply_to(
        FakeClient(), types.ReplyParameters(message_id=5, story_id=9, chat_id="me")
    )
    assert isinstance(reply_to, raw.types.InputReplyToStory)
