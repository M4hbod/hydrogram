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

"""The SOCKS/HTTP path: what the dict turns into before python-socks dials it."""

from __future__ import annotations

import asyncio

import pytest
from python_socks import ProxyType

from pyrogram.connection.proxy import DIALED_SCHEMES
from pyrogram.connection.transport.tcp import tcp as tcp_module
from pyrogram.connection.transport.tcp.tcp import TCP, proxy_type_by_scheme


class FakeSocket:
    def is_closing(self) -> bool:
        return False

    async def drain(self) -> None:
        pass

    async def read(self, length: int) -> bytes:
        return b""


@pytest.fixture
def dialed(monkeypatch):
    """Capture what SocksProxy was built with, without opening anything."""
    calls: list[dict] = []

    class FakeSocksProxy:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        async def connect(self, *, dest_host, dest_port, timeout):
            calls[-1]["destination"] = (dest_host, dest_port)
            calls[-1]["timeout"] = timeout

            return object()

    async def open_connection(*args, **kwargs):
        return FakeSocket(), FakeSocket()

    monkeypatch.setattr(tcp_module, "SocksProxy", FakeSocksProxy)
    monkeypatch.setattr(asyncio, "open_connection", open_connection)

    return calls


@pytest.mark.parametrize(
    ("scheme", "expected"),
    [
        ("socks4", ProxyType.SOCKS4),
        ("SOCKS5", ProxyType.SOCKS5),
        ("http", ProxyType.HTTP),
    ],
)
async def test_the_scheme_picks_the_proxy_type(dialed, scheme, expected):
    proxy = {"scheme": scheme, "hostname": "proxy.invalid", "port": 1080}
    transport = TCP(ipv6=False, proxy=proxy)

    await transport.connect(("149.154.167.51", 443))

    assert dialed[0]["proxy_type"] is expected
    assert dialed[0]["host"] == "proxy.invalid"
    assert dialed[0]["port"] == 1080
    assert dialed[0]["destination"] == ("149.154.167.51", 443)


async def test_credentials_are_passed_as_fields_not_a_url(dialed):
    # A URL round trip would drop a username that comes without a password and
    # unquote both, so a credential holding "@", ":" or "%" would not survive.
    proxy = {
        "scheme": "socks5",
        "hostname": "proxy.invalid",
        "port": 1080,
        "username": "user@example",
        "password": "p:a%ss",
    }
    transport = TCP(ipv6=False, proxy=proxy)

    await transport.connect(("149.154.167.51", 443))

    assert dialed[0]["username"] == "user@example"
    assert dialed[0]["password"] == "p:a%ss"


async def test_a_dialed_proxy_leaves_the_stream_unobfuscated(dialed):
    # SOCKS and HTTP are tunnels: the transport speaks to the DC exactly as it
    # would directly, with no obfuscated2 header and no ciphers armed.
    transport = TCP(ipv6=False, proxy={"scheme": "socks5", "hostname": "h", "port": 1})

    await transport.connect(("149.154.167.51", 443))

    assert transport.encrypt is None
    assert transport.decrypt is None
    assert transport.records is None


async def test_an_unknown_scheme_is_refused(dialed):
    transport = TCP(ipv6=False, proxy={"scheme": "wireguard", "hostname": "h", "port": 1})

    with pytest.raises(ValueError, match="Unknown proxy type"):
        await transport.connect(("149.154.167.51", 443))


def test_every_dialed_scheme_has_a_python_socks_type():
    assert set(proxy_type_by_scheme) == set(DIALED_SCHEMES)
