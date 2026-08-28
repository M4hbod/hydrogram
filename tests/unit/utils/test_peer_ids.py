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

"""Peer id packing.

Telegram numbers users, chats and channels in three disjoint ranges of one signed integer space,
and the library moves between the raw ids and the packed ones constantly. An off-by-one at a range
boundary sends a message to the wrong chat, so the boundaries are worth pinning explicitly rather
than testing a couple of ids in the middle.
"""

from __future__ import annotations

import pytest

from pyrogram import raw, utils
from pyrogram.utils import MAX_CHANNEL_ID, MAX_USER_ID, MIN_CHANNEL_ID, MIN_CHAT_ID


def test_user_peer_id_is_the_raw_id():
    assert utils.get_peer_id(raw.types.PeerUser(user_id=123)) == 123


def test_chat_peer_id_is_negated():
    assert utils.get_peer_id(raw.types.PeerChat(chat_id=123)) == -123


def test_channel_peer_id_is_offset_from_the_top_of_the_range():
    assert utils.get_peer_id(raw.types.PeerChannel(channel_id=123)) == MAX_CHANNEL_ID - 123


def test_channel_id_round_trips():
    packed = utils.get_peer_id(raw.types.PeerChannel(channel_id=987654321))
    assert utils.get_channel_id(packed) == 987654321


def test_unknown_peer_type_is_rejected():
    with pytest.raises(ValueError, match="Peer type invalid"):
        utils.get_peer_id(
            raw.types.PeerLocated(peer=raw.types.PeerUser(user_id=1), expires=0, distance=0)
        )


@pytest.mark.parametrize(
    ("peer_id", "expected"),
    [
        (1, "user"),
        (MAX_USER_ID, "user"),
        (-1, "chat"),
        (MIN_CHAT_ID, "chat"),
        (MIN_CHANNEL_ID, "channel"),
        (MAX_CHANNEL_ID - 1, "channel"),
    ],
)
def test_peer_type_at_the_range_boundaries(peer_id, expected):
    assert utils.get_peer_type(peer_id) == expected


@pytest.mark.parametrize("peer_id", [0, MAX_USER_ID + 1, MIN_CHAT_ID - 1, MIN_CHANNEL_ID - 1])
def test_peer_type_rejects_ids_outside_every_range(peer_id):
    with pytest.raises(ValueError, match="Peer id invalid"):
        utils.get_peer_type(peer_id)


def test_the_three_ranges_do_not_overlap():
    """A user id and a channel id must never pack to the same integer."""
    assert MAX_USER_ID > 0
    assert MIN_CHAT_ID < 0
    assert MIN_CHANNEL_ID < MAX_CHANNEL_ID <= MIN_CHAT_ID


@pytest.mark.parametrize(
    "peer",
    [
        raw.types.PeerUser(user_id=7),
        raw.types.PeerChat(chat_id=7),
        raw.types.PeerChannel(channel_id=7),
    ],
)
def test_raw_peer_id_is_always_the_undecorated_id(peer):
    assert utils.get_raw_peer_id(peer) == 7
