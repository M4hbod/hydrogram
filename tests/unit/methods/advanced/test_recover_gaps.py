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

"""``recover_gaps`` against a scripted server.

The failure this guards is not a crash: it is a loop that asks the same counter
forever, or a stored counter that moves when it should not, either of which only
shows up as duplicated or missing updates hours later.
"""

from __future__ import annotations

import asyncio

import pytest

from pyrogram import raw
from pyrogram.errors import ChannelPrivate, PersistentTimestampOutdated
from pyrogram.methods.advanced.recover_gaps import RecoverGaps
from pyrogram.storage import SQLiteStorage, UpdateState

CHANNEL_ID = -1001234567890


def message(message_id: int) -> raw.types.Message:
    return raw.types.Message(
        id=message_id,
        peer_id=raw.types.PeerUser(user_id=7),
        date=1700000000,
        message="hi",
    )


class Dispatcher:
    def __init__(self):
        self.updates_queue = asyncio.Queue()

    def queued(self) -> list:
        return list(self.updates_queue._queue)


class ScriptedClient(RecoverGaps):
    """Answers each invoke() with the next scripted reply, in order."""

    def __init__(self, storage, replies):
        self.storage = storage
        self.dispatcher = Dispatcher()
        self.replies = list(replies)
        self.requests = []

    async def invoke(self, request):
        self.requests.append(request)
        reply = self.replies.pop(0)

        if isinstance(reply, Exception):
            raise reply

        return reply

    async def resolve_peer(self, peer_id):
        return raw.types.InputPeerChannel(channel_id=1234567890, access_hash=0)


@pytest.fixture
async def storage():
    store = SQLiteStorage("test", use_memory=True)
    await store.open()
    yield store
    await store.close()


async def test_nothing_stored_means_nothing_to_recover(storage):
    client = ScriptedClient(storage, [])

    assert await client.recover_gaps() == (0, 0)
    assert client.requests == []


async def test_a_difference_is_replayed_through_the_dispatcher(storage):
    await storage.set_update_state(UpdateState(0, pts=10, qts=0, date=100, seq=1))

    client = ScriptedClient(
        storage,
        [
            raw.types.updates.Difference(
                new_messages=[message(1), message(2)],
                new_encrypted_messages=[],
                other_updates=[
                    raw.types.UpdateReadMessagesContents(messages=[1], pts=1, pts_count=1)
                ],
                chats=[],
                users=[],
                state=raw.types.updates.State(pts=42, qts=0, date=200, seq=9, unread_count=0),
            )
        ],
    )

    assert await client.recover_gaps() == (2, 1)
    assert len(client.dispatcher.queued()) == 3

    # The counter must land on what the server reported, or the same window is
    # asked for again on the next start.
    assert await storage.get_update_states() == [UpdateState(0, 42, 0, 200, 9)]


async def test_the_account_wide_state_asks_for_the_plain_difference(storage):
    await storage.set_update_state(UpdateState(0, pts=10, date=100))

    client = ScriptedClient(storage, [raw.types.updates.DifferenceEmpty(date=300, seq=4)])

    await client.recover_gaps()

    assert isinstance(client.requests[0], raw.functions.updates.GetDifference)

    # An empty difference still advances the clock the next call is made from.
    assert await storage.get_update_states() == [UpdateState(0, 10, None, 300, 4)]


async def test_a_channel_state_asks_for_the_channel_difference(storage):
    await storage.set_update_state(UpdateState(CHANNEL_ID, pts=10, date=100))

    client = ScriptedClient(
        storage, [raw.types.updates.ChannelDifferenceEmpty(pts=11, final=True)]
    )

    await client.recover_gaps()

    assert isinstance(client.requests[0], raw.functions.updates.GetChannelDifference)
    assert await storage.get_update_states() == [UpdateState(CHANNEL_ID, 11, None, 100, None)]


async def test_a_slice_is_followed_until_the_server_says_it_is_done(storage):
    await storage.set_update_state(UpdateState(0, pts=10, date=100))

    client = ScriptedClient(
        storage,
        [
            raw.types.updates.DifferenceSlice(
                new_messages=[message(1)],
                new_encrypted_messages=[],
                other_updates=[],
                chats=[],
                users=[],
                intermediate_state=raw.types.updates.State(
                    pts=20, qts=0, date=150, seq=2, unread_count=0
                ),
            ),
            raw.types.updates.Difference(
                new_messages=[message(2)],
                new_encrypted_messages=[],
                other_updates=[],
                chats=[],
                users=[],
                state=raw.types.updates.State(pts=30, qts=0, date=200, seq=3, unread_count=0),
            ),
        ],
    )

    assert await client.recover_gaps() == (2, 0)
    assert [r.pts for r in client.requests] == [10, 20]


async def test_a_slice_that_does_not_advance_is_not_asked_for_again(storage):
    # A server that keeps handing back the same counter would otherwise be asked
    # forever: this is an infinite loop, not a slow recovery.
    await storage.set_update_state(UpdateState(0, pts=10, date=100))

    stuck = raw.types.updates.DifferenceSlice(
        new_messages=[message(1)],
        new_encrypted_messages=[],
        other_updates=[],
        chats=[],
        users=[],
        intermediate_state=raw.types.updates.State(pts=10, qts=0, date=100, seq=1, unread_count=0),
    )

    client = ScriptedClient(storage, [stuck, stuck])

    assert await client.recover_gaps() == (1, 0)
    assert len(client.requests) == 1


async def test_a_too_long_difference_jumps_the_counter_and_asks_again(storage):
    await storage.set_update_state(UpdateState(0, pts=10, date=100))

    client = ScriptedClient(
        storage,
        [
            raw.types.updates.DifferenceTooLong(pts=500),
            raw.types.updates.DifferenceEmpty(date=200, seq=5),
        ],
    )

    await client.recover_gaps()

    assert [r.pts for r in client.requests] == [10, 500]


async def test_a_chat_we_can_no_longer_see_is_forgotten(storage):
    # Otherwise its dead counter is retried on every single start.
    await storage.set_update_state(UpdateState(CHANNEL_ID, pts=10, date=100))

    client = ScriptedClient(storage, [ChannelPrivate(None)])

    assert await client.recover_gaps() == (0, 0)
    assert await storage.get_update_states() == []


async def test_an_outdated_timestamp_is_retried(storage):
    await storage.set_update_state(UpdateState(0, pts=10, date=100))

    client = ScriptedClient(
        storage,
        [PersistentTimestampOutdated(None), raw.types.updates.DifferenceEmpty(date=200, seq=5)],
    )

    await client.recover_gaps()

    assert len(client.requests) == 2


async def test_only_the_named_chats_are_recovered(storage):
    await storage.set_update_state([
        UpdateState(0, pts=10, date=100),
        UpdateState(CHANNEL_ID, pts=10, date=200),
    ])

    client = ScriptedClient(storage, [raw.types.updates.DifferenceEmpty(date=300, seq=1)])

    await client.recover_gaps(0)

    assert len(client.requests) == 1
    assert isinstance(client.requests[0], raw.functions.updates.GetDifference)
