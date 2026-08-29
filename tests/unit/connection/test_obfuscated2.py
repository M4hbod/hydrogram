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

import hashlib

import pytest

from pyrogram.connection.transport.tcp.tcp import (
    ABRIDGED_OBFUSCATE_TAG,
    INTERMEDIATE_PADDED_OBFUSCATE_TAG,
    RESERVED_NONCE_PREFIXES,
    TCP,
    build_obfuscated2_header,
    generate_obfuscated2_nonce,
)
from pyrogram.connection.transport.tcp.tcp_intermediate_padded import TCPIntermediatePadded
from pyrogram.crypto import aes

SECRET = bytes(range(16))


def keystream(key: bytes, iv: bytes, length: int) -> bytes:
    # CTR encrypts by XOR, so encrypting zeros hands back the raw keystream --
    # which is how a test recovers the plaintext the header hid.
    return aes.ctr256_encrypt(bytes(length), key, bytearray(iv), bytearray(1))


def decoded_tail(header: bytes, *, secret: bytes | None) -> bytes:
    """The plaintext bytes 56:64 of a header, recovered from the wire form."""
    nonce = bytearray(header)

    key = bytes(nonce[8:40])
    if secret is not None:
        key = hashlib.sha256(key + secret).digest()

    stream = keystream(key, bytes(nonce[40:56]), 64)

    return bytes(a ^ b for a, b in zip(header[56:64], stream[56:64]))


def test_nonce_avoids_every_fingerprintable_prefix():
    for _ in range(200):
        nonce = generate_obfuscated2_nonce()

        assert len(nonce) == 64
        assert nonce[0] != 0xEF
        assert bytes(nonce[:4]) not in RESERVED_NONCE_PREFIXES
        assert nonce[4:8] != bytes(4)


def test_header_is_sixty_four_bytes():
    header = build_obfuscated2_header(None, dc_id=None, obfuscate_tag=ABRIDGED_OBFUSCATE_TAG)

    assert len(header.header) == 64


def test_a_plain_header_takes_its_keys_straight_out_of_the_nonce():
    # No secret means no hashing: this is the handshake a direct connection to a
    # DC speaks, and hashing an empty secret into it would break it.
    header = build_obfuscated2_header(None, dc_id=None, obfuscate_tag=ABRIDGED_OBFUSCATE_TAG)
    nonce = header.header
    reversed_tail = bytes(bytearray(nonce)[55:7:-1])

    assert header.encrypt[0] == nonce[8:40]
    assert header.decrypt[0] == reversed_tail[:32]


def test_a_secret_is_hashed_into_both_keys():
    header = build_obfuscated2_header(SECRET, dc_id=2, obfuscate_tag=ABRIDGED_OBFUSCATE_TAG)
    nonce = header.header
    reversed_tail = bytes(bytearray(nonce)[55:7:-1])

    assert header.encrypt[0] == hashlib.sha256(nonce[8:40] + SECRET).digest()
    assert header.decrypt[0] == hashlib.sha256(reversed_tail[:32] + SECRET).digest()


def test_the_tag_and_dc_id_ride_in_the_header_obfuscated():
    header = build_obfuscated2_header(
        SECRET, dc_id=-4, obfuscate_tag=INTERMEDIATE_PADDED_OBFUSCATE_TAG
    )
    tail = decoded_tail(header.header, secret=SECRET)

    assert tail[:4] == INTERMEDIATE_PADDED_OBFUSCATE_TAG
    assert int.from_bytes(tail[4:6], "little", signed=True) == -4


def test_a_plain_header_carries_the_tag_but_no_dc_id():
    # A DC we dialed by IP already knows which one it is; only a proxy needs it.
    header = build_obfuscated2_header(None, dc_id=3, obfuscate_tag=ABRIDGED_OBFUSCATE_TAG)
    tail = decoded_tail(header.header, secret=None)

    assert tail[:4] == ABRIDGED_OBFUSCATE_TAG
    assert tail[4:6] != (3).to_bytes(2, "little")


def test_the_cipher_state_is_already_past_the_header():
    # The header advances the keystream 64 bytes, so the first real send must
    # continue it rather than restart -- otherwise the proxy decrypts garbage.
    header = build_obfuscated2_header(SECRET, dc_id=1, obfuscate_tag=ABRIDGED_OBFUSCATE_TAG)
    key, iv, state = header.encrypt

    fresh = keystream(key, bytes(bytearray(header.header)[40:56]), 128)
    following = aes.ctr256_encrypt(bytes(64), key, iv, state)

    assert following == fresh[64:]


@pytest.mark.parametrize("secret", [bytes(15), bytes(17)])
def test_a_wrong_sized_secret_is_refused(secret):
    with pytest.raises(ValueError, match="exactly 16 bytes"):
        build_obfuscated2_header(secret, dc_id=1, obfuscate_tag=ABRIDGED_OBFUSCATE_TAG)


def test_a_wrong_sized_tag_is_refused():
    with pytest.raises(ValueError, match="exactly 4 bytes"):
        build_obfuscated2_header(SECRET, dc_id=1, obfuscate_tag=b"\xef")


async def test_a_transport_without_a_tag_cannot_speak_mtproxy():
    proxy = {"scheme": "MTPROXY", "hostname": "h", "port": 1, "secret": SECRET.hex()}
    transport = TCP(ipv6=False, proxy=proxy, dc_id=1)

    with pytest.raises(ValueError, match="no OBFUSCATE_TAG"):
        transport.mtproxy_secret()


async def test_a_padded_secret_is_refused_by_a_transport_that_sends_no_padding():
    proxy = {"scheme": "MTPROXY", "hostname": "h", "port": 1, "secret": "dd" + SECRET.hex()}

    class Unpadded(TCP):
        OBFUSCATE_TAG = ABRIDGED_OBFUSCATE_TAG

    transport = Unpadded(ipv6=False, proxy=proxy, dc_id=1)

    with pytest.raises(ValueError, match="random padding"):
        transport.mtproxy_secret()


async def test_mtproxy_needs_a_dc_id():
    proxy = {"scheme": "MTPROXY", "hostname": "h", "port": 1, "secret": SECRET.hex()}
    transport = TCPIntermediatePadded(ipv6=False, proxy=proxy, dc_id=None)

    with pytest.raises(ValueError, match="requires a dc_id"):
        transport.mtproxy_secret()


async def test_padded_send_pads_to_a_length_the_prefix_agrees_with(monkeypatch):
    sent: list[bytes] = []

    async def capture(self, data):
        sent.append(data)

    monkeypatch.setattr(TCP, "send", capture)

    transport = TCPIntermediatePadded(ipv6=False, proxy=None)

    for _ in range(64):
        await transport.send(b"payload!")

    for packet in sent:
        declared = int.from_bytes(packet[:4], "little")

        assert declared == len(packet) - 4
        assert packet[4:12] == b"payload!"
        assert 0 <= declared - 8 <= 15

    # Random padding that is always the same length would not be padding.
    assert len({len(packet) for packet in sent}) > 1


async def test_padded_recv_strips_the_padding_off_an_encrypted_message(monkeypatch):
    body = b"\x11" * 8 + b"\x22" * 16 + b"\x33" * 16  # auth_key_id + 32 bytes
    packet = body + b"pad" * 3  # 9 bytes of padding, 41 % 16 == 9
    queue = [len(packet).to_bytes(4, "little"), packet]

    async def replay(self, length=0):
        return queue.pop(0)

    monkeypatch.setattr(TCP, "recv", replay)

    transport = TCPIntermediatePadded(ipv6=False, proxy=None)

    assert await transport.recv() == body


async def test_padded_recv_keeps_a_short_transport_answer_whole(monkeypatch):
    # A 4-byte error code is not a padded message and has nothing to strip.
    error = (-404).to_bytes(4, "little", signed=True)
    queue = [len(error).to_bytes(4, "little"), error]

    async def replay(self, length=0):
        return queue.pop(0)

    monkeypatch.setattr(TCP, "recv", replay)

    transport = TCPIntermediatePadded(ipv6=False, proxy=None)

    assert await transport.recv() == error
