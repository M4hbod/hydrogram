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

import base64

import pytest

from pyrogram.connection.connection import protocol_dc_id, transport_class_for
from pyrogram.connection.proxy import (
    decode_mtproxy_secret,
    is_mtproxy,
    normalize_proxy,
    parse_proxy_url,
)
from pyrogram.connection.transport import TCPAbridged, TCPAbridgedO, TCPIntermediatePadded

PLAIN_KEY = bytes(range(16))
PLAIN_HEX = PLAIN_KEY.hex()
PADDED_HEX = "dd" + PLAIN_HEX
FAKE_TLS_HEX = "ee" + PLAIN_HEX + b"example.com".hex()


def test_plain_secret_is_the_bare_key():
    secret = decode_mtproxy_secret(PLAIN_HEX)

    assert secret == (PLAIN_KEY, False, None)


def test_a_sixteen_byte_secret_stays_plain_even_when_it_opens_with_a_marker():
    # The length decides the flavour before the first byte does -- TDLib's order.
    key = b"\xdd" + bytes(15)

    assert decode_mtproxy_secret(key.hex()) == (key, False, None)


def test_dd_secret_asks_for_padding_and_loses_its_marker():
    assert decode_mtproxy_secret(PADDED_HEX) == (PLAIN_KEY, True, None)


def test_ee_secret_carries_the_sni_domain():
    assert decode_mtproxy_secret(FAKE_TLS_HEX) == (PLAIN_KEY, True, "example.com")


def test_secret_may_be_base64url_without_padding():
    encoded = base64.b64encode(bytes.fromhex(PADDED_HEX), altchars=b"-_").decode().rstrip("=")

    assert decode_mtproxy_secret(encoded) == (PLAIN_KEY, True, None)


@pytest.mark.parametrize(
    "secret",
    [
        "not hex and not base64!",
        bytes(15).hex(),  # too short
        bytes(17).hex(),  # 17 bytes without a dd marker
        "ee" + PLAIN_HEX,  # ee marker with no domain after the key
    ],
)
def test_malformed_secrets_are_rejected(secret):
    with pytest.raises(ValueError):
        decode_mtproxy_secret(secret)


def test_ee_secret_rejects_an_oversized_domain():
    with pytest.raises(ValueError, match="over the 182-byte maximum"):
        decode_mtproxy_secret("ee" + PLAIN_HEX + (b"a" * 183).hex())


def test_proxy_link_becomes_an_mtproxy_dict():
    # The trailing dot is a valid fully-qualified name that not every resolver
    # stack accepts, and links copied out of a chat carry one.
    proxy = parse_proxy_url(
        f"https://t.me/proxy?server=example.com.&port=4455&secret={PADDED_HEX}"
    )

    assert proxy == {
        "scheme": "MTPROXY",
        "hostname": "example.com",
        "port": 4455,
        "secret": PADDED_HEX,
    }


def test_tg_scheme_link_parses_the_same_way():
    tme = parse_proxy_url(f"https://t.me/proxy?server=example.com&port=443&secret={PLAIN_HEX}")
    tg = parse_proxy_url(f"tg://proxy?server=example.com&port=443&secret={PLAIN_HEX}")

    assert tme == tg


def test_socks_link_keeps_its_credentials():
    proxy = parse_proxy_url("tg://socks?server=example.com&port=1080&user=u&pass=p")

    assert proxy == {
        "scheme": "SOCKS5",
        "hostname": "example.com",
        "port": 1080,
        "username": "u",
        "password": "p",
    }


@pytest.mark.parametrize(
    "url",
    [
        "https://t.me/joinchat/whatever",
        "tg://proxy?server=example.com&port=443",  # no secret
        "tg://proxy?server=example.com&secret=" + PLAIN_HEX,  # no port
    ],
)
def test_bad_links_are_rejected(url):
    with pytest.raises(ValueError):
        parse_proxy_url(url)


def test_normalize_uppercases_the_scheme():
    proxy = normalize_proxy({"scheme": "socks5", "hostname": "h", "port": 1})

    assert proxy["scheme"] == "SOCKS5"


def test_normalize_leaves_none_alone():
    assert normalize_proxy(None) is None


@pytest.mark.parametrize(
    ("proxy", "match"),
    [
        ({"hostname": "h", "port": 1}, "must contain 'scheme'"),
        ({"scheme": "socks5", "port": 1}, "must contain 'hostname'"),
        ({"scheme": "socks5", "hostname": "h"}, "must contain 'port'"),
        ({"scheme": "mtproxy", "hostname": "h", "port": 1}, "must contain 'secret'"),
        ({"scheme": "wireguard", "hostname": "h", "port": 1}, "unknown proxy scheme"),
    ],
)
def test_normalize_rejects_an_incomplete_dict(proxy, match):
    with pytest.raises(ValueError, match=match):
        normalize_proxy(proxy)


def test_normalize_rejects_a_malformed_secret_at_the_boundary():
    # The point of validating here is that the failure lands when the Client is
    # built, not on the first reconnect hours later.
    with pytest.raises(ValueError):
        normalize_proxy({"scheme": "mtproxy", "hostname": "h", "port": 1, "secret": "zz"})


def test_is_mtproxy_only_for_the_mtproxy_scheme():
    assert is_mtproxy({"scheme": "MTPROXY", "hostname": "h", "port": 1, "secret": PLAIN_HEX})
    assert not is_mtproxy({"scheme": "SOCKS5", "hostname": "h", "port": 1})
    assert not is_mtproxy(None)


@pytest.mark.parametrize(
    ("secret", "expected"),
    [
        (PLAIN_HEX, TCPAbridgedO),
        (PADDED_HEX, TCPIntermediatePadded),
        (FAKE_TLS_HEX, TCPIntermediatePadded),
    ],
)
def test_the_secret_picks_the_transport(secret, expected):
    proxy = normalize_proxy({"scheme": "mtproxy", "hostname": "h", "port": 1, "secret": secret})

    assert transport_class_for(proxy) is expected


def test_a_non_mtproxy_keeps_the_default_transport():
    assert transport_class_for(None) is TCPAbridged
    assert transport_class_for({"scheme": "SOCKS5", "hostname": "h", "port": 1}) is TCPAbridged


@pytest.mark.parametrize(
    ("dc_id", "test_mode", "media", "expected"),
    [
        (2, False, False, 2),
        (2, True, False, 10002),
        (2, False, True, -2),
        (2, True, True, -10002),
    ],
)
def test_protocol_dc_id_folds_in_media_and_test_mode(dc_id, test_mode, media, expected):
    assert protocol_dc_id(dc_id, test_mode=test_mode, media=media) == expected
