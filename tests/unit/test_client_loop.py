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

"""``Client.loop`` must be whichever loop is running now.

It was a ``functools.cached_property``, so the first access pinned a loop onto
the instance for the object's life. An app that starts the client once to read
something, stops it, and starts it again under a different
``run_until_complete`` then does its socket I/O against the first loop:

    RuntimeError: got Future <Future pending> attached to a different loop

raised from ``Session.send``, which does ``client.loop.run_in_executor(...)``.

The clients here are built inside a running loop on purpose: on Python 3.9
``asyncio.Lock()`` binds to the current loop as it is constructed, so
``Client()`` itself needs one.
"""

from __future__ import annotations

import asyncio

from pyrogram import Client
from pyrogram.dispatcher import Dispatcher


def fresh_client() -> Client:
    return Client("loop-test", api_id=1, api_hash="0" * 32, in_memory=True)


async def test_the_loop_is_the_one_actually_running():
    client = fresh_client()

    assert client.loop is asyncio.get_running_loop()


async def test_the_loop_is_not_pinned_to_the_first_reader():
    """The property must resolve per access, not cache."""
    client = fresh_client()

    first = client.loop

    # A second loop, driven from a worker thread so this one stays running.
    def in_another_loop():
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(asyncio.sleep(0, client.loop))
        finally:
            loop.close()

    second = await asyncio.get_running_loop().run_in_executor(None, in_another_loop)

    assert first is asyncio.get_running_loop()
    assert second is not first, "Client.loop is pinned to the loop that first read it"


async def test_the_loop_bound_primitives_are_rebuilt_per_connect():
    """What made the second start fail even once `loop` followed the running one."""
    client = fresh_client()

    before = (
        client.file_lock,
        client.save_file_semaphore,
        client.updates_watchdog_event,
    )

    client.rebuild_loop_bound_state()

    after = (
        client.file_lock,
        client.save_file_semaphore,
        client.updates_watchdog_event,
    )

    for old, new in zip(before, after):
        assert old is not new, f"{type(old).__name__} was reused across connects"


async def test_the_dispatcher_queue_is_rebuilt_per_start():
    client = fresh_client()
    dispatcher = Dispatcher(client)
    client.no_updates = True  # keep start() from spawning workers

    first = dispatcher.updates_queue
    await dispatcher.start()

    assert dispatcher.updates_queue is not first
