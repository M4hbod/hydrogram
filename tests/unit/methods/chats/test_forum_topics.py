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

"""Forum-topic methods: namespace and error propagation.

Two things are pinned here. The RPCs live in the ``messages`` namespace -- they were moved there by
Telegram, and calling ``raw.functions.channels.*`` raised ``AttributeError`` on every one of these
methods until 4e975991. And errors propagate: ``delete_forum_topic`` used to catch every exception,
``print`` it to stdout and return ``False``, which turned a ``FloodWait`` into a silent failure that
a retry loop would hammer straight through.
"""

from __future__ import annotations

import pytest

from pyrogram import raw
from pyrogram.methods.chats.close_forum_topic import CloseForumTopic
from pyrogram.methods.chats.create_forum_topic import CreateForumTopic
from pyrogram.methods.chats.delete_forum_topic import DeleteForumTopic
from pyrogram.methods.chats.get_forum_topics import GetForumTopics


class RecordingClient:
    """Captures the RPC instead of sending it."""

    def __init__(self, raises: Exception | None = None):
        self.raises = raises
        self.sent = []

    @staticmethod
    async def resolve_peer(_peer):
        return raw.types.InputPeerChannel(channel_id=1, access_hash=2)

    async def invoke(self, rpc, **_kwargs):
        self.sent.append(rpc)
        if self.raises is not None:
            raise self.raises
        if isinstance(rpc, raw.functions.messages.CreateForumTopic):
            # The method reads r.updates[1].message.action, so the reply has to have that shape.
            return raw.types.Updates(
                updates=[
                    raw.types.UpdateMessageID(id=1, random_id=1),
                    raw.types.UpdateNewChannelMessage(
                        message=raw.types.MessageService(
                            id=1,
                            peer_id=raw.types.PeerChannel(channel_id=1),
                            date=0,
                            action=raw.types.MessageActionTopicCreate(title="t", icon_color=0),
                        ),
                        pts=1,
                        pts_count=1,
                    ),
                ],
                users=[],
                chats=[],
                date=0,
                seq=0,
            )
        return raw.types.messages.AffectedHistory(pts=1, pts_count=1, offset=0)

    @staticmethod
    def rnd_id():
        return 1

    @staticmethod
    def guess_mime_type(_):  # pragma: no cover - unused, present for interface parity
        return None


async def test_delete_forum_topic_uses_the_messages_namespace():
    client = RecordingClient()
    await DeleteForumTopic.delete_forum_topic(client, chat_id=-100123, topic_id=7)

    (rpc,) = client.sent
    assert isinstance(rpc, raw.functions.messages.DeleteTopicHistory)
    assert rpc.top_msg_id == 7


async def test_close_forum_topic_uses_the_messages_namespace():
    client = RecordingClient()
    await CloseForumTopic.close_forum_topic(client, chat_id=-100123, topic_id=7)

    (rpc,) = client.sent
    assert isinstance(rpc, raw.functions.messages.EditForumTopic)
    assert rpc.closed is True


async def test_create_forum_topic_uses_the_messages_namespace():
    client = RecordingClient()
    await CreateForumTopic.create_forum_topic(client, chat_id=-100123, title="t")

    (rpc,) = client.sent
    assert isinstance(rpc, raw.functions.messages.CreateForumTopic)
    assert rpc.title == "t"
    assert isinstance(rpc.peer, raw.types.InputPeerChannel)


def test_the_moved_rpcs_take_peer_not_channel():
    """The messages.* variants renamed the argument; passing `channel` is a TypeError."""
    for rpc in (
        raw.functions.messages.DeleteTopicHistory,
        raw.functions.messages.EditForumTopic,
        raw.functions.messages.GetForumTopics,
    ):
        assert "peer" in rpc.__slots__
        assert "channel" not in rpc.__slots__


async def test_delete_forum_topic_propagates_errors():
    """Regression: it used to catch everything, print it, and return False.

    A swallowed FloodWait is the dangerous case -- the caller sees a plain ``False``, retries
    immediately, and makes the flood worse.
    """
    client = RecordingClient(raises=ConnectionError("boom"))

    with pytest.raises(ConnectionError, match="boom"):
        await DeleteForumTopic.delete_forum_topic(client, chat_id=-100123, topic_id=7)


async def test_delete_forum_topic_returns_true_on_success():
    client = RecordingClient()
    assert await DeleteForumTopic.delete_forum_topic(client, chat_id=-100123, topic_id=7) is True


async def test_sibling_methods_also_propagate():
    """Every forum-topic method should behave the same way; delete was the odd one out."""
    client = RecordingClient(raises=ConnectionError("boom"))

    with pytest.raises(ConnectionError):
        await CloseForumTopic.close_forum_topic(client, chat_id=-100123, topic_id=7)

    with pytest.raises(ConnectionError):
        await GetForumTopics.get_forum_topics(client, chat_id=-100123).__anext__()
