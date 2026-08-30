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

"""Start, stop, and start again under a different event loop.

A common app shape: a throwaway client cycle at import time to read one thing
(a bot's own username, say), then the real start under the app's own
``run_until_complete``. Those are two different loops.

``Client.loop`` was a ``cached_property``, so the second cycle did its socket
I/O against the first, dead loop and died in ``Session.send`` with "got Future
attached to a different loop". The dispatcher's update queue and the client's
locks and semaphores had the same affinity for the same reason.

Live because that is where it bit: the unit test in
``tests/unit/test_client_loop.py`` pins the property itself, this pins the whole
start path.
"""

from __future__ import annotations

import asyncio
import os

import pytest

from pyrogram import Client

SESSION_STRING = os.environ.get("PYROGRAM_TEST_SESSION_STRING")

pytestmark = pytest.mark.skipif(
    not SESSION_STRING, reason="PYROGRAM_TEST_SESSION_STRING is not set"
)


def test_a_client_can_be_started_again_on_a_second_loop():
    client = Client("two-cycles", session_string=SESSION_STRING, in_memory=True)

    async def cycle():
        await client.start()
        try:
            return (await client.get_me()).id
        finally:
            await client.stop()

    # Deliberately not asyncio.run twice in one call: two explicit loops, which
    # is what run_until_complete in two modules produces.
    first_loop = asyncio.new_event_loop()
    try:
        first = first_loop.run_until_complete(cycle())
    finally:
        first_loop.close()

    second_loop = asyncio.new_event_loop()
    try:
        second = second_loop.run_until_complete(cycle())
    finally:
        second_loop.close()

    assert first == second
