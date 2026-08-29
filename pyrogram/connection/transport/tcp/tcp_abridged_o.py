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

from .tcp import ABRIDGED_OBFUSCATE_TAG, TCP, Proxy

log = logging.getLogger(__name__)


class TCPAbridgedO(TCP):
    """Abridged framing inside an obfuscated2 stream."""

    OBFUSCATE_TAG = ABRIDGED_OBFUSCATE_TAG

    def __init__(self, ipv6: bool, proxy: Proxy, dc_id: int | None = None) -> None:
        super().__init__(ipv6, proxy, dc_id)

    async def connect(self, address: tuple[str, int]) -> None:
        await super().connect(address)

        if not self.is_mtproxy:
            # An MTProxy connection is already obfuscated -- under the proxy's
            # secret, and with the header written while dialing.
            await self._open_obfuscated2(None)

    async def send(self, data: bytes, *args) -> None:
        length = len(data) // 4

        await super().send(
            (bytes([length]) if length <= 126 else b"\x7f" + length.to_bytes(3, "little")) + data
        )

    async def recv(self, length: int = 0) -> bytes | None:
        length = await super().recv(1)

        if length is None:
            return None

        if length == b"\x7f":
            length = await super().recv(3)

            if length is None:
                return None

        return await super().recv(int.from_bytes(length, "little") * 4)
