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

from __future__ import annotations

import logging
import os
from struct import pack, unpack

from .tcp import INTERMEDIATE_PADDED_OBFUSCATE_TAG, TCP, Proxy

log = logging.getLogger(__name__)


class TCPIntermediatePadded(TCP):
    """Intermediate framing with random padding on every packet.

    This is the framing a ``dd``-prefixed MTProxy secret asks for: the padding
    is what stops the packet lengths themselves from identifying the protocol.
    ``TCP.mtproxy_secret`` refuses to build a header for such a secret with any
    other framing, so this class is the only way to use one.
    """

    OBFUSCATE_TAG = INTERMEDIATE_PADDED_OBFUSCATE_TAG

    def __init__(self, ipv6: bool, proxy: Proxy, dc_id: int | None = None) -> None:
        super().__init__(ipv6, proxy, dc_id)

    async def connect(self, address: tuple[str, int]) -> None:
        await super().connect(address)

        if self.is_mtproxy:
            # The obfuscated2 header written while dialing already carries the tag.
            return

        await TCP.send(self, INTERMEDIATE_PADDED_OBFUSCATE_TAG)

    async def send(self, data: bytes, *args) -> None:
        padding = os.urandom(os.urandom(1)[0] & 0x0F)

        await super().send(pack("<i", len(data) + len(padding)) + data + padding)

    async def recv(self, length: int = 0) -> bytes | None:
        length = await super().recv(4)

        if length is None:
            return None

        length = unpack("<i", length)[0]
        data = await super().recv(length)

        if data is None:
            return None

        # A short packet is a transport-level answer, not a padded message: a
        # 4-byte error code, or the 8-byte quick-ack form that opens with
        # 0xffffffff. Neither carries padding to strip.
        if length < 24:
            if length >= 8 and data[:4] == b"\xff\xff\xff\xff":
                return data[:8]

            return data[:4]

        # An encrypted message opens with a non-zero auth_key_id, and its true
        # length is a multiple of 16 past the 24-byte plaintext prologue.
        # Unencrypted messages carry no padding at all.
        if data[:8] != b"\x00" * 8:
            strip = (length - 24) % 16

            if strip:
                data = data[:-strip]

        return data
