#  Pyrogram - Telegram MTProto API Client Library for Python
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

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pyrogram.session import Session


@pytest.mark.asyncio
async def test_stop_cancels_inflight_packet_before_it_can_touch_next_connection():
    session = Session(
        SimpleNamespace(loop=asyncio.get_running_loop(), disconnect_handler=None),
        dc_id=5,
        auth_key=bytes(256),
        test_mode=False,
    )
    entered = asyncio.Event()
    release = asyncio.Event()
    finished = asyncio.Event()
    mutated = []

    async def handle_packet(_):
        entered.set()
        try:
            await release.wait()
            mutated.append(True)
            session.stored_msg_ids.append(123)
        finally:
            finished.set()

    session.connection = SimpleNamespace(
        recv=AsyncMock(side_effect=[b"packet", None]), close=AsyncMock()
    )
    session.handle_packet = handle_packet
    session.recv_task = asyncio.create_task(session.recv_worker())
    await asyncio.wait_for(entered.wait(), 1)
    await session.stop()
    release.set()
    await asyncio.wait_for(finished.wait(), 1)

    assert not mutated, "an old connection's packet handler survived stop()"
    assert session.stored_msg_ids == []
