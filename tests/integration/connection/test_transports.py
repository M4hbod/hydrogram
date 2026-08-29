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

"""Live transport checks. Skipped unless credentials are in the environment.

Set ``PYROGRAM_TEST_SESSION_STRING`` to run the direct cases, and additionally
``PYROGRAM_TEST_PROXY`` (a ``tg://proxy`` or ``t.me/proxy`` link, or a
``tg://socks`` one) to run the proxy case. Nothing is written to disk: the
client runs from an in-memory session, which is the only form a session string
should ever be used in.
"""

from __future__ import annotations

import os

import pytest

from pyrogram import Client
from pyrogram.connection.proxy import parse_proxy_url
from pyrogram.connection.transport import (
    TCPAbridged,
    TCPAbridgedO,
    TCPFull,
    TCPIntermediate,
    TCPIntermediateO,
    TCPIntermediatePadded,
)

SESSION_STRING = os.environ.get("PYROGRAM_TEST_SESSION_STRING")
PROXY = os.environ.get("PYROGRAM_TEST_PROXY")

pytestmark = pytest.mark.skipif(
    not SESSION_STRING, reason="PYROGRAM_TEST_SESSION_STRING is not set"
)

TRANSPORTS = [
    TCPAbridged,
    TCPAbridgedO,
    TCPFull,
    TCPIntermediate,
    TCPIntermediateO,
    TCPIntermediatePadded,
]


async def signed_in(**kwargs) -> tuple[int, str, tuple[str, int]]:
    """Connect, ask the server who we are, and report how we got there."""
    app = Client("live", session_string=SESSION_STRING, in_memory=True, **kwargs)

    await app.start()
    try:
        me = await app.get_me()
        protocol = app.session.connection.protocol

        return me.id, type(protocol).__name__, protocol.writer.get_extra_info("peername")
    finally:
        await app.stop()


@pytest.mark.parametrize("factory", TRANSPORTS, ids=lambda f: f.__name__)
async def test_every_framing_transport_reaches_the_dc(factory):
    user_id, protocol, _peer = await signed_in(protocol_factory=factory)

    assert user_id
    assert protocol == factory.__name__


@pytest.mark.skipif(not PROXY, reason="PYROGRAM_TEST_PROXY is not set")
async def test_the_proxy_carries_the_session():
    user_id, _protocol, peer = await signed_in(proxy=PROXY)

    assert user_id

    # The connection lands on the proxy, not on a Telegram address: this is what
    # separates a proxy that is actually being used from one being ignored.
    assert peer[1] == parse_proxy_url(PROXY)["port"]


@pytest.mark.skipif(not PROXY, reason="PYROGRAM_TEST_PROXY is not set")
async def test_the_media_dc_is_reachable_through_the_proxy():
    # The media cluster is addressed by a negated dc id in the obfuscated2
    # header, so it exercises a code path the main DC never touches.
    app = Client("live", session_string=SESSION_STRING, in_memory=True, proxy=PROXY)

    await app.start()
    try:
        photos = [photo async for photo in app.get_chat_photos("me", limit=1)]

        if not photos:
            pytest.skip("the test account has no profile photo to download")

        downloaded = await app.download_media(photos[0].file_id, in_memory=True)

        assert downloaded.getvalue()
    finally:
        await app.stop()
