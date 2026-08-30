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

"""A login from nothing: the DH exchange, run for real.

``Auth.create()`` had no test of any kind. Every other test starts from a
session string or a session file, and both skip authorization entirely -- which
is exactly why ``raw.pyrogram.ClientDHInnerData`` shipped in 3.0.0 and 3.1.0 and
was only found when a bot was started without a session file on disk.

The static guards in ``tests/contract/`` catch the name that caused it. This
catches the class they cannot: anything that makes the exchange itself fail,
whatever the reason.

Needs ``PYROGRAM_TEST_API_ID``, ``PYROGRAM_TEST_API_HASH`` and
``PYROGRAM_TEST_BOT_TOKEN``. Nothing is written to disk: the session is in
memory, which is also what forces the fresh authorization.
"""

from __future__ import annotations

import os

import pytest

from pyrogram import Client
from pyrogram.session import Auth

API_ID = os.environ.get("PYROGRAM_TEST_API_ID")
API_HASH = os.environ.get("PYROGRAM_TEST_API_HASH")
BOT_TOKEN = os.environ.get("PYROGRAM_TEST_BOT_TOKEN")

pytestmark = pytest.mark.skipif(
    not (API_ID and API_HASH and BOT_TOKEN),
    reason="PYROGRAM_TEST_API_ID, PYROGRAM_TEST_API_HASH and PYROGRAM_TEST_BOT_TOKEN are not set",
)


def fresh_client() -> Client:
    # No session string and no file, so storage starts empty and load_session()
    # has to call Auth.create().
    return Client(
        "fresh-auth",
        api_id=int(API_ID),
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True,
    )


async def test_a_login_from_nothing_produces_a_usable_session():
    app = fresh_client()

    await app.start()
    try:
        me = await app.get_me()

        assert me.is_bot
        assert me.id

        # 2048-bit key, the output of the exchange that was broken.
        assert len(await app.storage.auth_key()) == 256
    finally:
        await app.stop()


async def test_auth_create_returns_a_key_on_its_own():
    """Auth.create() apart from the client, so a failure points at the exchange."""
    app = fresh_client()

    await app.connect()
    try:
        auth_key = await Auth(
            app, await app.storage.dc_id(), await app.storage.test_mode()
        ).create()

        assert len(auth_key) == 256
    finally:
        await app.disconnect()
