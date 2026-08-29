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
import hashlib
import logging
import os
import socket
import time
from typing import ClassVar, Final, NamedTuple

from python_socks import ProxyType
from python_socks.async_.asyncio import Proxy as SocksProxy

import pyrogram
from pyrogram.connection.proxy import (
    MTProxySecret,
    Proxy,
    decode_mtproxy_secret,
    is_mtproxy,
)
from pyrogram.crypto import aes, faketls

from .faketls_records import (
    GREETING_RESPONSE_PREFIXES,
    RECORD_LENGTH_SIZE,
    FakeTlsRecords,
)

log = logging.getLogger(__name__)

# The schemes python-socks dials for us, and its name for each. Anything else
# needs a transport of its own.
proxy_type_by_scheme: dict[str, ProxyType] = {
    "SOCKS4": ProxyType.SOCKS4,
    "SOCKS5": ProxyType.SOCKS5,
    "HTTP": ProxyType.HTTP,
}

# The 4-byte tag written at nonce[56:60], by which a peer recognizes the packet
# framing that follows. An MTProxy reads it off the obfuscated2 header; a direct
# connection sends it as the whole greeting instead.
ABRIDGED_OBFUSCATE_TAG: Final[bytes] = b"\xef\xef\xef\xef"
INTERMEDIATE_OBFUSCATE_TAG: Final[bytes] = b"\xee\xee\xee\xee"
INTERMEDIATE_PADDED_OBFUSCATE_TAG: Final[bytes] = b"\xdd\xdd\xdd\xdd"

_OBFUSCATE_TAG_SIZE: Final[int] = 4

# The first four bytes a nonce must not open with. The repeated bytes are
# framing tags and ``16 03 01 02`` is a TLS ClientHello record; the four verbs
# are the ones stock MTProxy hands to its HTTP fallback, so a nonce opening with
# one would be answered as a web request.
# https://github.com/tdlib/td/blob/d1085f9/td/mtproto/TcpTransport.cpp#L99-L101
RESERVED_NONCE_PREFIXES: Final[tuple[bytes, ...]] = (
    b"HEAD",
    b"POST",
    b"GET ",
    b"OPTI",
    ABRIDGED_OBFUSCATE_TAG,
    INTERMEDIATE_OBFUSCATE_TAG,
    INTERMEDIATE_PADDED_OBFUSCATE_TAG,
    b"\x16\x03\x01\x02",
)

# (key, iv, state) for aes.ctr256_{en,de}crypt. The iv and state are mutated in
# place by every call, so a tuple must be reused as-is for the connection's life.
CipherArgs = tuple[bytes, bytearray, bytearray]


def generate_obfuscated2_nonce(
    reserved_prefixes: tuple[bytes, ...] = RESERVED_NONCE_PREFIXES,
) -> bytearray:
    """A random 64-byte obfuscated2 nonce with no fingerprintable prefix.

    Avoids a literal ``0xef`` first byte, the cleartext protocol prefixes a
    middlebox looks for, and an all-zero field.
    """
    while True:
        nonce = bytearray(os.urandom(64))

        if (
            nonce[0] != 0xEF
            and bytes(nonce[:4]) not in reserved_prefixes
            and nonce[4:8] != b"\x00\x00\x00\x00"
        ):
            return nonce


class Obfuscated2Header(NamedTuple):
    header: bytes
    encrypt: CipherArgs
    decrypt: CipherArgs


def build_obfuscated2_header(
    secret: bytes | None, *, dc_id: int | None, obfuscate_tag: bytes
) -> Obfuscated2Header:
    """Build the 64-byte header that opens an obfuscated2 stream.

    ``secret`` is the bare 16-byte MTProxy key, or ``None`` for the plain
    obfuscated transports, which take the keys straight out of the nonce rather
    than hashing a secret into them. ``dc_id`` is written into the header only
    when a secret is present -- an MTProxy needs to know which DC to relay to,
    a DC we dialed ourselves already knows.
    """
    if secret is not None and len(secret) != 16:
        raise ValueError(f"obfuscated2: secret must be exactly 16 bytes, got {len(secret)}")

    if len(obfuscate_tag) != _OBFUSCATE_TAG_SIZE:
        raise ValueError(f"obfuscated2: obfuscate_tag must be exactly {_OBFUSCATE_TAG_SIZE} bytes")

    nonce = generate_obfuscated2_nonce()
    reversed_tail = bytearray(nonce[55:7:-1])

    if secret is None:
        encrypt_key = bytes(nonce[8:40])
        decrypt_key = bytes(reversed_tail[:32])
    else:
        encrypt_key = hashlib.sha256(bytes(nonce[8:40]) + secret).digest()
        decrypt_key = hashlib.sha256(bytes(reversed_tail[:32]) + secret).digest()

    encrypt: CipherArgs = (encrypt_key, bytearray(nonce[40:56]), bytearray(1))
    decrypt: CipherArgs = (decrypt_key, bytearray(reversed_tail[32:48]), bytearray(1))

    nonce[56:60] = obfuscate_tag

    if dc_id is not None and secret is not None:
        nonce[60:62] = dc_id.to_bytes(2, "little", signed=True)

    # Encrypting the whole 64-byte buffer both puts the tag and dc_id bytes onto
    # the wire in obfuscated form and advances the keystream exactly 64 bytes, so
    # the first real send() continues it rather than restarting.
    nonce[56:64] = aes.ctr256_encrypt(bytes(nonce), *encrypt)[56:64]

    return Obfuscated2Header(header=bytes(nonce), encrypt=encrypt, decrypt=decrypt)


class TCP:
    TIMEOUT = 10

    # Set by a framing subclass that can speak obfuscated2: the 4-byte tag an
    # MTProxy reads out of the header to know what framing follows. None means
    # "this transport has no obfuscated2 story" and cannot be used with MTProxy.
    OBFUSCATE_TAG: ClassVar[bytes | None] = None

    def __init__(self, ipv6: bool, proxy: Proxy, dc_id: int | None = None) -> None:
        self.ipv6 = ipv6
        self.proxy = proxy
        # Every obfuscated2 header carries the dc id, so an MTProxy knows which
        # DC to relay to. Connection passes the already-shifted protocol dc id
        # (media and test mode folded in), not the bare logical one.
        self.dc_id = dc_id

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        self.lock = asyncio.Lock()
        self.loop = asyncio.get_running_loop()
        self._closed = True

        self.encrypt: CipherArgs | None = None
        self.decrypt: CipherArgs | None = None
        self.records: FakeTlsRecords | None = None

    @property
    def closed(self) -> bool:
        return (
            self._closed or self.writer is None or self.writer.is_closing() or self.reader is None
        )

    @property
    def is_mtproxy(self) -> bool:
        return is_mtproxy(self.proxy)

    def mtproxy_secret(self) -> MTProxySecret:
        """The decoded secret, checked against what this transport can actually speak."""
        if self.dc_id is None:
            raise ValueError("MTProxy requires a dc_id, passed through by Connection")

        if not self.OBFUSCATE_TAG:
            raise ValueError(
                f"{type(self).__name__} has no OBFUSCATE_TAG and cannot speak obfuscated2; use "
                f"TCPAbridgedO for a plain secret, TCPIntermediatePadded for a dd one"
            )

        secret = decode_mtproxy_secret(self.proxy["secret"])

        # A dd secret asks for random padding, and the padded intermediate is the
        # only transport that sends any. Connection picks that class on its own,
        # so reaching this means the transport was built by hand.
        if secret.padded and self.OBFUSCATE_TAG != INTERMEDIATE_PADDED_OBFUSCATE_TAG:
            raise ValueError(
                f"this proxy's secret asks for random padding, which {type(self).__name__} "
                f"does not send; use TCPIntermediatePadded"
            )

        return secret

    async def _connect_via_proxy(self, destination: tuple[str, int]) -> None:
        scheme = self.proxy.get("scheme")
        if scheme is None:
            raise ValueError("No scheme specified")

        proxy_type = proxy_type_by_scheme.get(scheme.upper())
        if proxy_type is None:
            raise ValueError(f"Unknown proxy type {scheme}")

        # The fields go in one by one rather than as a URL: python-socks' URL
        # parser drops a username that comes without a password and unquotes
        # both, so a credential holding "@", ":" or "%" would not survive.
        proxy = SocksProxy(
            proxy_type=proxy_type,
            host=self.proxy.get("hostname"),
            port=self.proxy.get("port"),
            username=self.proxy.get("username"),
            password=self.proxy.get("password"),
        )

        dest_host, dest_port = destination
        sock = await proxy.connect(dest_host=dest_host, dest_port=dest_port, timeout=TCP.TIMEOUT)

        self.reader, self.writer = await asyncio.open_connection(sock=sock)
        self._closed = False

    async def _connect_via_direct(
        self, destination: tuple[str, int], *, family: int | None = None
    ) -> None:
        host, port = destination

        if family is None:
            family = socket.AF_INET6 if self.ipv6 else socket.AF_INET

        self.reader, self.writer = await asyncio.open_connection(
            host=host, port=port, family=family
        )

        # Cleared here rather than in connect(), because a handshake that runs
        # before connect() returns -- the fake-TLS greeting -- has to be able to
        # read from the socket it just opened.
        self._closed = False

    async def _open_obfuscated2(
        self, secret: bytes | None, *, sni_hostname: str | None = None
    ) -> None:
        """Write the obfuscated2 header and arm the stream ciphers.

        The header goes straight to the socket rather than through :meth:`send`,
        which would encrypt it under the very keys it is delivering. Everything
        sent after this point is obfuscated.

        With ``sni_hostname`` the stream is greeted as TLS first, and the header
        then rides inside the first record instead of going out on its own.
        """
        if not self.OBFUSCATE_TAG:
            raise ValueError(f"{type(self).__name__} has no OBFUSCATE_TAG")

        header = build_obfuscated2_header(
            secret, dc_id=self.dc_id, obfuscate_tag=self.OBFUSCATE_TAG
        )

        if sni_hostname is None:
            self.writer.write(header.header)
            await self.writer.drain()
        else:
            await self._greet_fake_tls(domain=sni_hostname, secret=secret)
            self.records = FakeTlsRecords(self._recv_from_socket, prologue=header.header)

        self.encrypt = header.encrypt
        self.decrypt = header.decrypt

    async def _greet_fake_tls(self, *, domain: str, secret: bytes) -> None:
        # The local clock, where TDLib uses one corrected against the server: the
        # correction lives in Session, which does not exist yet at connect time.
        # A proxy tolerates hours of skew, so this only matters on a broken clock.
        hello = faketls.build_client_hello(
            domain=domain, secret=secret, unix_time=int(time.time())
        )

        log.info("Greeting the fake-TLS MTProxy as %s", domain)

        self.writer.write(hello.record)
        await self.writer.drain()

        response = await self._read_greeting_response()

        if not faketls.server_hello_is_authentic(
            response, secret=secret, client_random=hello.random
        ):
            raise OSError(
                f"fake-TLS: {domain} answered the greeting without knowing the proxy secret"
            )

    async def _read_greeting_response(self) -> bytes:
        response = bytearray()

        for prefix in GREETING_RESPONSE_PREFIXES:
            head = await self._recv_from_socket(len(prefix) + RECORD_LENGTH_SIZE)

            if head is None or head[: len(prefix)] != prefix:
                raise OSError("fake-TLS: the greeting was not answered with a ServerHello")

            body = await self._recv_from_socket(int.from_bytes(head[-RECORD_LENGTH_SIZE:], "big"))

            if body is None:
                raise OSError("fake-TLS: the connection closed inside the ServerHello")

            response += head + body

        # Hashed exactly as it arrived, both segments together.
        return bytes(response)

    async def _connect_via_mtproxy(self) -> None:
        secret = self.mtproxy_secret()

        # The proxy sits at its own address, unrelated to the DC address ipv6 was
        # derived from, so let getaddrinfo pick the family it actually has.
        await self._connect_via_direct(
            (self.proxy["hostname"], self.proxy["port"]), family=socket.AF_UNSPEC
        )

        await self._open_obfuscated2(secret.key, sni_hostname=secret.sni_hostname)

    async def _connect(self, destination: tuple[str, int]) -> None:
        if self.is_mtproxy:
            await self._connect_via_mtproxy()
        elif self.proxy:
            await self._connect_via_proxy(destination)
        else:
            await self._connect_via_direct(destination)

    async def connect(self, address: tuple[str, int]) -> None:
        try:
            await asyncio.wait_for(self._connect(address), TCP.TIMEOUT)
            self._closed = False
        except (
            asyncio.TimeoutError
        ):  # Re-raise as TimeoutError. asyncio.TimeoutError is deprecated in 3.11
            self._closed = True
            raise TimeoutError("Connection timed out") from None

    async def close(self) -> None:
        if self.writer is None:
            self._closed = True
            return

        try:
            self.writer.close()
            await asyncio.wait_for(self.writer.wait_closed(), TCP.TIMEOUT)
        except Exception as e:
            log.info("Close exception: %s %s", type(e).__name__, e)
        finally:
            self._closed = True

    async def send(self, data: bytes) -> None:
        if self.writer is None or self._closed:
            raise OSError("Connection is closed")

        if self.encrypt is not None:
            data = await self.loop.run_in_executor(
                pyrogram.crypto_executor, aes.ctr256_encrypt, data, *self.encrypt
            )

        if self.records is not None:
            data = self.records.wrap(data)

        async with self.lock:
            try:
                self.writer.write(data)
                await self.writer.drain()
            except Exception as e:
                log.info("Send exception: %s %s", type(e).__name__, e)
                self._closed = True
                raise OSError(e) from e

    async def recv(self, length: int = 0) -> bytes | None:
        if self.records is not None:
            data = await self.records.recv(length)
        else:
            data = await self._recv_from_socket(length)

        if data is None or self.decrypt is None:
            return data

        return await self.loop.run_in_executor(
            pyrogram.crypto_executor, aes.ctr256_decrypt, data, *self.decrypt
        )

    async def _recv_from_socket(self, length: int) -> bytes | None:
        if self._closed or self.reader is None:
            return None

        data = b""

        while len(data) < length:
            try:
                chunk = await asyncio.wait_for(self.reader.read(length - len(data)), TCP.TIMEOUT)
            except (OSError, asyncio.TimeoutError):
                self._closed = True
                return None
            else:
                if chunk:
                    data += chunk
                else:
                    self._closed = True
                    return None

        return data
