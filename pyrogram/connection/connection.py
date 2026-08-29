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

import asyncio
import logging
from typing import TYPE_CHECKING, Final

from pyrogram.session.internals import DataCenter

from .proxy import decode_mtproxy_secret, is_mtproxy
from .transport import TCP, TCPAbridged, TCPAbridgedO, TCPIntermediatePadded

if TYPE_CHECKING:
    from .proxy import Proxy

log = logging.getLogger(__name__)

# tdesktop's ``kTestModeDcIdShift``.
_TEST_MODE_DC_ID_SHIFT: Final[int] = 10000


def transport_class_for(proxy: Proxy | None, *, default: type[TCP] = TCPAbridged) -> type[TCP]:
    """The transport a proxy requires, or ``default`` when it requires none.

    An MTProxy secret decides the framing, not the caller: the padded
    intermediate is the only framing a ``dd`` or ``ee`` secret accepts, and a
    plain secret still needs a transport that can open an obfuscated2 stream.
    """
    if not is_mtproxy(proxy):
        return default

    if decode_mtproxy_secret(proxy["secret"]).padded:
        return TCPIntermediatePadded

    return TCPAbridgedO


def protocol_dc_id(dc_id: int, *, test_mode: bool, media: bool) -> int:
    """The dc id an obfuscated2 header carries, as tdesktop computes it.

    The media cluster is the negated dc id and test-mode servers get a fixed
    shift. Only a proxy ever reads this; a DC we dial by IP already knows which
    one it is.
    """
    shifted = dc_id + (_TEST_MODE_DC_ID_SHIFT if test_mode else 0)

    return -shifted if media else shifted


class Connection:
    MAX_CONNECTION_ATTEMPTS = 3

    def __init__(
        self,
        dc_id: int,
        test_mode: bool,
        ipv6: bool,
        proxy: Proxy,
        media: bool = False,
        protocol_factory: type[TCP] = TCPAbridged,
    ) -> None:
        self.dc_id = dc_id
        self.test_mode = test_mode
        self.ipv6 = ipv6
        self.proxy = proxy
        self.media = media

        # The proxy overrides whatever framing the caller asked for, so a proxy
        # is the only thing a caller has to pass to reach one.
        self.protocol_factory = transport_class_for(proxy, default=protocol_factory)

        if self.protocol_factory is not protocol_factory:
            log.debug(
                "This proxy requires %s, overriding %s",
                self.protocol_factory.__name__,
                protocol_factory.__name__,
            )

        self.address = DataCenter(dc_id, test_mode, ipv6, media)
        self.protocol: TCP | None = None
        self._protocol_dc_id = protocol_dc_id(dc_id, test_mode=test_mode, media=media)

    async def connect(self) -> None:
        for _i in range(Connection.MAX_CONNECTION_ATTEMPTS):
            self.protocol = self.protocol_factory(
                ipv6=self.ipv6, proxy=self.proxy, dc_id=self._protocol_dc_id
            )

            try:
                log.info("Connecting...")
                await self.protocol.connect(self.address)
            except OSError as e:
                log.warning("Unable to connect due to network issues: %s", e)
                await self.protocol.close()
                await asyncio.sleep(1)
            else:
                log.info(
                    "Connected! %s DC%s%s - IPv%s%s",
                    "Test" if self.test_mode else "Production",
                    self.dc_id,
                    " (media)" if self.media else "",
                    "6" if self.ipv6 else "4",
                    f" via MTProxy {self.proxy['hostname']}:{self.proxy['port']}"
                    if is_mtproxy(self.proxy)
                    else "",
                )
                break
        else:
            log.warning("Connection failed! Trying again...")
            raise ConnectionError

    async def close(self) -> None:
        await self.protocol.close()
        log.info("Disconnected")

    async def send(self, data: bytes) -> None:
        await self.protocol.send(data)

    async def recv(self) -> bytes | None:
        return await self.protocol.recv()
