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

"""Storage contract, exercised against the in-memory SQLite backend.

Session strings are user data with a long life: people paste them into config files and expect
them to keep working. ``SESSION_STRING_FORMAT`` is therefore a public wire format, not an
implementation detail, and the round-trip below is what makes changing it a deliberate act.
"""

from __future__ import annotations

import base64
import struct

import pytest

from pyrogram import raw
from pyrogram.storage import SQLiteStorage

AUTH_KEY = bytes(range(256))


@pytest.fixture
async def storage():
    store = SQLiteStorage("test", use_memory=True)
    await store.open()
    yield store
    await store.close()


async def populate(store: SQLiteStorage) -> None:
    await store.dc_id(2)
    await store.api_id(12345)
    await store.test_mode(False)
    await store.auth_key(AUTH_KEY)
    await store.user_id(777000)
    await store.is_bot(False)


# --- scalar accessors: each is a getter when called with no argument --------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dc_id", 4),
        ("api_id", 98765),
        ("test_mode", True),
        ("auth_key", AUTH_KEY),
        ("user_id", 1234567890),
        ("is_bot", True),
        ("date", 1700000000),
    ],
)
async def test_scalar_round_trip(storage, field, value):
    await getattr(storage, field)(value)
    assert await getattr(storage, field)() == value


# --- peer cache -------------------------------------------------------------


async def test_peer_can_be_looked_up_by_id_username_and_phone(storage):
    await storage.update_peers([(777000, 123456789, "user", "telegram", "+15551234567")])

    by_id = await storage.get_peer_by_id(777000)
    assert isinstance(by_id, raw.types.InputPeerUser)
    assert by_id.user_id == 777000
    assert by_id.access_hash == 123456789

    assert (await storage.get_peer_by_username("telegram")).user_id == 777000
    assert (await storage.get_peer_by_phone_number("+15551234567")).user_id == 777000


async def test_updating_a_peer_replaces_the_previous_access_hash(storage):
    await storage.update_peers([(777000, 111, "user", "telegram", None)])
    await storage.update_peers([(777000, 222, "user", "telegram", None)])
    assert (await storage.get_peer_by_id(777000)).access_hash == 222


async def test_unknown_peer_raises(storage):
    with pytest.raises(KeyError):
        await storage.get_peer_by_id(1)


@pytest.mark.parametrize(
    ("peer_type", "expected"),
    [
        ("user", raw.types.InputPeerUser),
        ("bot", raw.types.InputPeerUser),
        ("group", raw.types.InputPeerChat),
        ("channel", raw.types.InputPeerChannel),
        ("supergroup", raw.types.InputPeerChannel),
    ],
)
async def test_each_peer_type_maps_to_the_right_input_peer(storage, peer_type, expected):
    await storage.update_peers([(999, 42, peer_type, None, None)])
    assert isinstance(await storage.get_peer_by_id(999), expected)


# --- session strings --------------------------------------------------------


async def test_session_string_round_trips_through_a_new_storage(storage):
    await populate(storage)
    exported = await storage.export_session_string()

    restored = SQLiteStorage("restored", session_string=exported, use_memory=True)
    await restored.open()
    try:
        assert await restored.dc_id() == 2
        assert await restored.api_id() == 12345
        # SQLite has no boolean column type, so these come back as 0/1 rather than
        # False/True. Value equality is the contract; identity is not.
        assert bool(await restored.test_mode()) is False
        assert await restored.auth_key() == AUTH_KEY
        assert await restored.user_id() == 777000
        assert bool(await restored.is_bot()) is False
    finally:
        await restored.close()


async def test_session_string_is_url_safe_and_unpadded(storage):
    await populate(storage)
    exported = await storage.export_session_string()
    assert "=" not in exported, "padding must be stripped; it breaks copy-paste into URLs"
    assert "+" not in exported and "/" not in exported, "must use the url-safe alphabet"


async def test_session_string_format_is_the_documented_one(storage):
    """Changing SESSION_STRING_FORMAT invalidates every session string in the wild."""
    assert SQLiteStorage.SESSION_STRING_FORMAT == ">BI?256sQ?"

    await populate(storage)
    exported = await storage.export_session_string()
    raw_bytes = base64.urlsafe_b64decode(exported + "=" * (-len(exported) % 4))
    dc_id, api_id, test_mode, auth_key, user_id, is_bot = struct.unpack(
        SQLiteStorage.SESSION_STRING_FORMAT, raw_bytes
    )
    assert (dc_id, api_id, test_mode, auth_key, user_id, is_bot) == (
        2,
        12345,
        False,
        AUTH_KEY,
        777000,
        False,
    )
