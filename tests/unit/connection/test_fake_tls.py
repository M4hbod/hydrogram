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

"""The fake-TLS greeting and record layer, driven against a stand-in proxy.

No socket is opened: the transport's reader and writer are replaced by a pair
that hands whatever the client writes to a coroutine playing the proxy, and
hands whatever the proxy answers back to the client.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import struct

import pytest

from pyrogram.connection.transport.tcp.faketls_records import (
    APPLICATION_DATA_PREFIX,
    CHANGE_CIPHER_SPEC,
    RECORD_HEADER_SIZE,
    RECORD_LENGTH_SIZE,
)
from pyrogram.connection.transport.tcp.tcp import TCP
from pyrogram.connection.transport.tcp.tcp_intermediate_padded import TCPIntermediatePadded
from pyrogram.crypto import aes

KEY = bytes(range(16))
DOMAIN = "www.example.com"
SECRET = "ee" + KEY.hex() + DOMAIN.encode().hex()
PROXY = {"scheme": "MTPROXY", "hostname": "proxy.invalid", "port": 443, "secret": SECRET}

_RANDOM_SLICE = slice(11, 43)


def hello_digest(hello: bytes) -> bytes:
    """The HMAC the client should have put in the greeting's random field."""
    zeroed = hello[: _RANDOM_SLICE.start] + bytes(32) + hello[_RANDOM_SLICE.stop :]

    return hmac.new(KEY, zeroed, hashlib.sha256).digest()


def build_server_hello(client_random: bytes, *, secret: bytes = KEY) -> bytes:
    """A reply whose own random field authenticates it, as a real proxy builds one."""
    body = bytearray(b"\x03\x03" + bytes(32) + b"\x20" + b"\x01" * 32 + b"\x13\x01\x00")
    handshake = b"\x02" + len(body).to_bytes(3, "big") + bytes(body)
    first = b"\x16\x03\x03" + len(handshake).to_bytes(2, "big") + handshake
    payload = b"\x99" * 16
    second = (
        CHANGE_CIPHER_SPEC
        + APPLICATION_DATA_PREFIX
        + len(payload).to_bytes(RECORD_LENGTH_SIZE, "big")
        + payload
    )

    response = bytearray(first + second)
    digest = hmac.new(secret, client_random + bytes(response), hashlib.sha256).digest()
    response[_RANDOM_SLICE] = digest

    return bytes(response)


def unwrap_records(wire: bytes) -> bytes:
    """The payload carried by a run of application-data records."""
    assert wire.startswith(CHANGE_CIPHER_SPEC)
    wire = wire[len(CHANGE_CIPHER_SPEC) :]

    payload = bytearray()

    while wire:
        assert wire[: len(APPLICATION_DATA_PREFIX)] == APPLICATION_DATA_PREFIX
        length = int.from_bytes(wire[len(APPLICATION_DATA_PREFIX) : RECORD_HEADER_SIZE], "big")
        payload += wire[RECORD_HEADER_SIZE : RECORD_HEADER_SIZE + length]
        wire = wire[RECORD_HEADER_SIZE + length :]

    return bytes(payload)


class FakeProxy:
    """Answers the greeting, then records everything that follows."""

    def __init__(self, *, authentic: bool = True, answer_with: bytes | None = None) -> None:
        self.authentic = authentic
        self.answer_with = answer_with

        self.greeting: bytes | None = None
        self.stream = bytearray()
        self.inbox = asyncio.Queue()
        self._pending = bytearray()

    # -- the writer half the transport writes into --------------------------

    def write(self, data: bytes) -> None:
        if self.greeting is None:
            self.greeting = bytes(data)
            self._answer_greeting()
            return

        self.stream += data

    async def drain(self) -> None:
        pass

    def is_closing(self) -> bool:
        return False

    def close(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass

    # -- the reader half the transport reads out of -------------------------

    async def read(self, length: int) -> bytes:
        chunk = bytes(self._pending[:length])
        del self._pending[:length]

        return chunk

    def _answer_greeting(self) -> None:
        random = self.greeting[_RANDOM_SLICE]
        secret = KEY if self.authentic else bytes(16)

        self._pending += (
            self.answer_with
            if self.answer_with is not None
            else build_server_hello(random, secret=secret)
        )


def dial(proxy: FakeProxy, monkeypatch) -> None:
    """Hand the real _connect_via_direct our stand-in instead of a socket."""

    async def open_connection(*args, **kwargs):
        return proxy, proxy

    monkeypatch.setattr(asyncio, "open_connection", open_connection)


async def connected(proxy: FakeProxy, monkeypatch, secret: str = SECRET) -> TCPIntermediatePadded:
    transport = TCPIntermediatePadded(ipv6=False, proxy={**PROXY, "secret": secret}, dc_id=2)
    dial(proxy, monkeypatch)
    await transport.connect(("unused", 0))

    return transport


async def test_the_greeting_is_a_client_hello_for_the_secrets_domain(monkeypatch):
    proxy = FakeProxy()
    await connected(proxy, monkeypatch)

    assert proxy.greeting.startswith(b"\x16\x03\x01")
    assert DOMAIN.encode() in proxy.greeting

    # The record's own length field has to agree with what was written, or the
    # proxy drops the connection before it ever looks at the digest.
    declared = int.from_bytes(proxy.greeting[3:5], "big")
    assert declared == len(proxy.greeting) - 5


async def test_the_greeting_is_authenticated_with_the_secret(monkeypatch):
    proxy = FakeProxy()
    await connected(proxy, monkeypatch)

    # The last four bytes carry the clock XORed in, so only the first 28 are a
    # plain digest -- and a wrong secret would break all 32.
    assert hello_digest(proxy.greeting)[:28] == proxy.greeting[_RANDOM_SLICE][:28]


async def test_a_proxy_that_does_not_know_the_secret_is_refused(monkeypatch):
    proxy = FakeProxy(authentic=False)

    with pytest.raises(OSError, match="without knowing the proxy secret"):
        await connected(proxy, monkeypatch)


async def test_a_reply_that_is_not_a_server_hello_is_refused(monkeypatch):
    proxy = FakeProxy(answer_with=b"HTTP/1.1 400 Bad Request\r\n\r\n")

    with pytest.raises(OSError, match="not answered with a ServerHello"):
        await connected(proxy, monkeypatch)


async def test_the_obfuscated2_header_rides_inside_the_first_record(monkeypatch):
    # A lone 64-byte record right after a TLS handshake is a shape nothing else
    # produces, which is the whole reason it is prepended rather than sent alone.
    proxy = FakeProxy()
    transport = await connected(proxy, monkeypatch)

    assert transport.records is not None
    assert proxy.stream == b""

    await transport.send(b"\x11" * 40)

    payload = unwrap_records(bytes(proxy.stream))
    assert len(payload) > 64


async def test_what_the_proxy_reads_back_is_the_obfuscated2_stream(monkeypatch):
    proxy = FakeProxy()
    transport = await connected(proxy, monkeypatch)

    await transport.send(b"\x11" * 40)

    payload = unwrap_records(bytes(proxy.stream))
    header, body = payload[:64], payload[64:]

    # Exactly what a proxy does with the header: derive the key the client
    # encrypts under, read the tag and dc id out of its own keystream, then skip
    # the 64 bytes the header already spent and decrypt the stream.
    key = hashlib.sha256(header[8:40] + KEY).digest()
    keystream = aes.ctr256_encrypt(bytes(64), key, bytearray(header[40:56]), bytearray(1))
    tail = bytes(a ^ b for a, b in zip(header[56:64], keystream[56:64]))

    assert tail[:4] == b"\xdd\xdd\xdd\xdd"
    assert int.from_bytes(tail[4:6], "little", signed=True) == 2

    cipher = (key, bytearray(header[40:56]), bytearray(1))
    aes.ctr256_decrypt(bytes(64), *cipher)

    frame = aes.ctr256_decrypt(body, *cipher)
    length = struct.unpack("<i", frame[:4])[0]

    assert length == len(frame) - 4
    assert frame[4:44] == b"\x11" * 40
    assert len(frame) - 44 <= 15  # the rest is random padding


async def test_records_are_read_back_across_boundaries(monkeypatch):
    proxy = FakeProxy()
    transport = await connected(proxy, monkeypatch)

    # A record boundary has nothing to do with a read boundary: three records
    # carrying four bytes each must serve a single 12-byte read.
    for chunk in (b"\x01\x02\x03\x04", b"\x05\x06\x07\x08", b"\x09\x0a\x0b\x0c"):
        proxy._pending += (
            APPLICATION_DATA_PREFIX + len(chunk).to_bytes(RECORD_LENGTH_SIZE, "big") + chunk
        )

    transport.decrypt = None  # read the record layer without the cipher on top

    assert await TCP.recv(transport, 12) == bytes(range(1, 13))
