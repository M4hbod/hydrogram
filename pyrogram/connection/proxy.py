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
from typing import Final, NamedTuple, TypedDict
from urllib.parse import parse_qs, urlsplit

# The obfuscated2 key is always 16 bytes. A marker byte may prefix it: ``dd``
# asks for random padding on every packet, ``ee`` asks for the fake-TLS record
# layer and appends the SNI domain after the key. TDLib accepts exactly these
# three shapes -- 16 bare, 17 behind ``dd``, 18 or more behind ``ee``.
# https://github.com/tdlib/td/blob/d1085f9/td/mtproto/ProxySecret.cpp#L37-L39
SECRET_SIZE: Final[int] = 16
MARKED_SECRET_SIZE: Final[int] = SECRET_SIZE + 1

PADDED_MARKER: Final[int] = 0xDD
FAKE_TLS_MARKER: Final[int] = 0xEE

# TDLib's ``MAX_DOMAIN_LENGTH``, whose own comment reads "must be small enough
# to not overflow TLS-hello length".
MAX_SNI_DOMAIN_SIZE: Final[int] = 182

# An ``ee`` secret is shared base64url-encoded and the others as hex, but every
# client accepts any encoding, so the alphabet does not identify the flavour.
_BASE64URL_ALTCHARS: Final[bytes] = b"-_"

MTPROXY_SCHEME: Final[str] = "MTPROXY"

# The schemes ``socks`` dials for us. Anything else needs a transport of its own.
DIALED_SCHEMES: Final[frozenset[str]] = frozenset({"SOCKS4", "SOCKS5", "HTTP"})


class Proxy(TypedDict, total=False):
    """The dict accepted by ``Client(proxy=...)``.

    ``username``/``password`` apply to the dialed schemes; ``secret`` applies to
    ``mtproxy`` and is required there. No key is required at the type level
    because the four proxy kinds use different subsets -- :func:`normalize_proxy`
    is what rejects a dict that is missing something it needs.
    """

    scheme: str
    hostname: str
    port: int
    username: str | None
    password: str | None
    secret: str | bytes | None


class MTProxySecret(NamedTuple):
    """A decoded MTProxy secret, in the form the transport needs it."""

    key: bytes
    """The bare 16-byte obfuscated2 key, with any marker byte removed."""

    padded: bool
    """Whether every packet must carry random padding (a ``dd`` or ``ee`` secret)."""

    sni_hostname: str | None
    """The domain a fake-TLS (``ee``) secret greets with, else ``None``."""


def _b64_decoded(encoded: str, *, altchars: bytes) -> bytes | None:
    # Telegram's own links drop the "=" padding that base64 still requires.
    padded = encoded + "=" * (-len(encoded) % 4)

    try:
        return base64.b64decode(padded, altchars=altchars, validate=True)
    except ValueError:
        # binascii.Error is a ValueError, and both mean the same thing here.
        return None


def _decode_secret_bytes(secret: str | bytes) -> bytes:
    """Hex, then base64 in either alphabet -- the encodings TDLib accepts."""
    if isinstance(secret, (bytes, bytearray)):
        return bytes(secret)

    try:
        return bytes.fromhex(secret)
    except ValueError:
        pass

    # One call covers both alphabets: altchars only rewrites "-_" into "+/"
    # before validating, so a standard-base64 secret passes through untouched.
    decoded = _b64_decoded(secret, altchars=_BASE64URL_ALTCHARS)

    if decoded is None:
        raise ValueError(f"proxy secret must be hex, base64url or base64: {secret!r}")

    return decoded


def decode_mtproxy_secret(secret: str | bytes) -> MTProxySecret:
    """Decode an MTProxy secret into its key, padding flag and optional SNI domain.

    The length decides the flavour and is tested before the marker byte, the
    order TDLib tests it in: a bare 16-byte secret is plain even when it happens
    to start with ``0xdd``.
    """
    full = _decode_secret_bytes(secret)

    if len(full) == SECRET_SIZE:
        return MTProxySecret(key=full, padded=False, sni_hostname=None)

    if len(full) == MARKED_SECRET_SIZE and full[0] == PADDED_MARKER:
        return MTProxySecret(key=full[1:], padded=True, sni_hostname=None)

    # Strictly longer than a dd secret, because the domain may not be empty:
    # TDLib refuses to build a ClientHello without one.
    if len(full) > MARKED_SECRET_SIZE and full[0] == FAKE_TLS_MARKER:
        domain = full[MARKED_SECRET_SIZE:]

        if len(domain) > MAX_SNI_DOMAIN_SIZE:
            raise ValueError(
                f"ee-prefixed proxy secret carries a {len(domain)}-byte SNI domain, over "
                f"the {MAX_SNI_DOMAIN_SIZE}-byte maximum"
            )

        try:
            sni_hostname = domain.decode("ascii")
        except UnicodeDecodeError as e:
            raise ValueError(
                f"ee-prefixed proxy secret carries a non-ASCII SNI domain: {e}"
            ) from e

        return MTProxySecret(
            key=full[1:MARKED_SECRET_SIZE], padded=True, sni_hostname=sni_hostname
        )

    raise ValueError(
        "proxy secret must decode to 16 bytes (plain), 17 with a dd marker, or an ee marker "
        f"followed by a 16-byte key and a domain, got {len(full)} bytes"
    )


def is_mtproxy(proxy: Proxy | None) -> bool:
    return bool(proxy) and str(proxy.get("scheme", "")).upper() == MTPROXY_SCHEME


def normalize_proxy(proxy: Proxy | None) -> Proxy | None:
    """Validate a proxy dict once, at the boundary, and return it uppercase-schemed.

    Raising here rather than at connect time means a typo in the scheme or a
    malformed secret is reported when the ``Client`` is built, not on the first
    reconnect hours later.
    """
    if not proxy:
        return None

    scheme = proxy.get("scheme")

    if not scheme:
        raise ValueError("proxy dict must contain 'scheme'")

    scheme = str(scheme).upper()

    if not proxy.get("hostname"):
        raise ValueError("proxy dict must contain 'hostname'")

    if scheme == MTPROXY_SCHEME:
        secret = proxy.get("secret")

        if not secret:
            raise ValueError("an mtproxy proxy dict must contain 'secret'")

        # Decoded and thrown away: this is the validation, the transport decodes
        # it again from the stored string form.
        decode_mtproxy_secret(secret)

        if not proxy.get("port"):
            raise ValueError("an mtproxy proxy dict must contain 'port'")

    elif scheme in DIALED_SCHEMES:
        if not proxy.get("port"):
            raise ValueError(f"a {scheme.lower()} proxy dict must contain 'port'")

    else:
        known = ", ".join(sorted([*DIALED_SCHEMES, MTPROXY_SCHEME]))
        raise ValueError(f"unknown proxy scheme {scheme!r}, expected one of: {known}")

    return {**proxy, "scheme": scheme}


def parse_proxy_url(url: str) -> Proxy:
    """Build a proxy dict from a shared proxy link.

    Accepts the two forms Telegram clients hand out -- ``tg://proxy?...`` and
    ``https://t.me/proxy?...`` -- for MTProxy, and ``tg://socks?...`` /
    ``https://t.me/socks?...`` for SOCKS5.
    """
    parts = urlsplit(url)
    query = parse_qs(parts.query)

    def one(name: str) -> str | None:
        values = query.get(name)
        return values[0] if values else None

    kind = parts.netloc.lower() if parts.scheme == "tg" else parts.path.strip("/").lower()

    server = one("server")
    port = one("port")

    if not server or not port:
        raise ValueError(f"proxy link is missing 'server' or 'port': {url!r}")

    # A hostname copied out of a chat often keeps a trailing dot; it is a valid
    # fully-qualified name but not every resolver stack accepts it.
    server = server.rstrip(".")

    if kind == "proxy":
        secret = one("secret")

        if not secret:
            raise ValueError(f"an mtproxy link must carry a 'secret': {url!r}")

        return normalize_proxy({
            "scheme": "mtproxy",
            "hostname": server,
            "port": int(port),
            "secret": secret,
        })

    if kind == "socks":
        return normalize_proxy({
            "scheme": "socks5",
            "hostname": server,
            "port": int(port),
            "username": one("user"),
            "password": one("pass"),
        })

    raise ValueError(f"not a proxy link: {url!r}")
