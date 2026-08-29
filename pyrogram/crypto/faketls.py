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

"""The fake-TLS greeting an ``ee``-prefixed MTProxy secret asks for.

The whole point of the greeting is that an observer cannot tell it apart from
the ClientHello a current Chrome sends, so none of the byte strings, extension
bodies or random lengths below are choices of ours: they are TDLib's
``TlsInit.cpp``, which is normative here, and :func:`_client_hello_ops` mirrors
its op list one entry at a time so the two can be read side by side.

https://github.com/tdlib/td/blob/d1085f9/td/mtproto/TlsInit.cpp
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Final, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Sequence

# GREASE values are drawn once per greeting and then referenced by index,
# because the same value has to reappear in more than one extension.
_GREASE_SIZE: Final[int] = 7

# The curve the x25519 key share is drawn on: the field modulus, the ``A`` of
# its Montgomery form, and the size a public key occupies.
_CURVE25519_PRIME: Final[int] = 2**255 - 19
_CURVE25519_A: Final[int] = 486662
_CURVE25519_KEY_SIZE: Final[int] = 32

# One ML-KEM-768 key share: 384 coefficient pairs modulo 3329, then a 32-byte
# seed that TDLib appends to the same op as a plain random block.
_ML_KEM_768_MODULUS: Final[int] = 3329
_ML_KEM_768_COEFFICIENT_PAIRS: Final[int] = 384
_ML_KEM_768_SEED_SIZE: Final[int] = 32

# The hello is padded out to this offset, so its length says nothing about the
# length of the domain it names.
_PADDING_TARGET_OFFSET: Final[int] = 513

# The encrypted-client-hello payload length: one of four, drawn once for the
# process rather than once per greeting. TDLib draws it while initialising a
# function-local static, so every hello one TDLib process sends carries the
# same one -- and a client whose ECH length changed per connection would stand
# out for exactly that.
_ECH_PAYLOAD_SIZE: Final[int] = secrets.choice((144, 176, 208, 240))

# Where the 32-byte random field sits, which carries the HMAC rather than
# random bytes: 5 bytes of record header, 4 of handshake header, 2 of version.
_RANDOM_OFFSET: Final[int] = 11
_RANDOM_SIZE: Final[int] = 32

_TIMESTAMP_SIZE: Final[int] = 4

# A scope writes its own length into the two bytes it reserved up front.
_SCOPE_LENGTH_SIZE: Final[int] = 2


class _OpKind(Enum):
    STRING = auto()
    RANDOM = auto()
    ZERO = auto()
    DOMAIN = auto()
    GREASE = auto()
    BEGIN_SCOPE = auto()
    END_SCOPE = auto()
    KEY = auto()
    ML_KEM_768_KEY = auto()
    PERMUTATION = auto()
    PADDING = auto()


@dataclass(frozen=True)
class _Op:
    kind: _OpKind
    data: bytes = b""
    length: int = 0
    seed: int = 0
    parts: tuple[tuple[_Op, ...], ...] = ()


def _string(data: bytes) -> _Op:
    return _Op(kind=_OpKind.STRING, data=data)


def _random(length: int) -> _Op:
    return _Op(kind=_OpKind.RANDOM, length=length)


def _zero(length: int) -> _Op:
    return _Op(kind=_OpKind.ZERO, length=length)


def _domain() -> _Op:
    return _Op(kind=_OpKind.DOMAIN)


def _grease(seed: int) -> _Op:
    return _Op(kind=_OpKind.GREASE, seed=seed)


def _begin_scope() -> _Op:
    return _Op(kind=_OpKind.BEGIN_SCOPE)


def _end_scope() -> _Op:
    return _Op(kind=_OpKind.END_SCOPE)


def _key() -> _Op:
    return _Op(kind=_OpKind.KEY)


def _ml_kem_768_key() -> _Op:
    return _Op(kind=_OpKind.ML_KEM_768_KEY)


def _ech_payload() -> _Op:
    return _random(_ECH_PAYLOAD_SIZE)


def _permutation(parts: Sequence[Sequence[_Op]]) -> _Op:
    return _Op(kind=_OpKind.PERMUTATION, parts=tuple(tuple(part) for part in parts))


def _padding() -> _Op:
    return _Op(kind=_OpKind.PADDING)


def _client_hello_ops() -> tuple[_Op, ...]:
    """TDLib's non-Apple op list, entry for entry.

    The literal strings are the fixed fields of a Chrome ClientHello -- record
    and handshake headers, the cipher suite list, the extension bodies -- and
    the ops between them are the parts that vary per connection.

    https://github.com/tdlib/td/blob/d1085f9/td/mtproto/TlsInit.cpp#L194-L236
    """
    return (
        _string(b"\x16\x03\x01"),
        _begin_scope(),
        _string(b"\x01\x00"),
        _begin_scope(),
        _string(b"\x03\x03"),
        _zero(_RANDOM_SIZE),
        _string(b"\x20"),
        _random(32),
        _string(b"\x00\x20"),
        _grease(0),
        _string(
            b"\x13\x01\x13\x02\x13\x03\xc0\x2b\xc0\x2f\xc0\x2c\xc0\x30\xcc\xa9\xcc\xa8"
            b"\xc0\x13\xc0\x14\x00\x9c\x00\x9d\x00\x2f\x00\x35\x01\x00"
        ),
        _begin_scope(),
        _grease(2),
        _string(b"\x00\x00"),
        _permutation((
            (
                _string(b"\x00\x00"),
                _begin_scope(),
                _begin_scope(),
                _string(b"\x00"),
                _begin_scope(),
                _domain(),
                _end_scope(),
                _end_scope(),
                _end_scope(),
            ),
            (_string(b"\x00\x05\x00\x05\x01\x00\x00\x00\x00"),),
            (
                _string(b"\x00\x0a\x00\x0c\x00\x0a"),
                _grease(4),
                _string(b"\x11\xec\x00\x1d\x00\x17\x00\x18"),
            ),
            (_string(b"\x00\x0b\x00\x02\x01\x00"),),
            (
                _string(
                    b"\x00\x0d\x00\x18\x00\x16\x09\x04\x09\x05\x09\x06\x04\x03\x08\x04"
                    b"\x04\x01\x05\x03\x08\x05\x05\x01\x08\x06\x06\x01"
                ),
            ),
            (
                _string(
                    b"\x00\x10\x00\x0e\x00\x0c\x02\x68\x32\x08\x68\x74\x74\x70\x2f\x31\x2e\x31"
                ),
            ),
            (_string(b"\x00\x12\x00\x00"),),
            (_string(b"\x00\x17\x00\x00"),),
            (_string(b"\x00\x1b\x00\x03\x02\x00\x02"),),
            (_string(b"\x00\x23\x00\x00"),),
            (_string(b"\x00\x2b\x00\x07\x06"), _grease(6), _string(b"\x03\x04\x03\x03")),
            (_string(b"\x00\x2d\x00\x02\x01\x01"),),
            (
                _string(b"\x00\x33\x04\xef\x04\xed"),
                _grease(4),
                _string(b"\x00\x01\x00\x11\xec\x04\xc0"),
                _ml_kem_768_key(),
                _key(),
                _string(b"\x00\x1d\x00\x20"),
                _key(),
            ),
            (_string(b"\x44\xcd\x00\x05\x00\x03\x02\x68\x32"),),
            (
                _string(b"\xfe\x0d"),
                _begin_scope(),
                _string(b"\x00\x00\x01\x00\x01"),
                _random(1),
                _string(b"\x00\x20"),
                _key(),
                _begin_scope(),
                _ech_payload(),
                _end_scope(),
                _end_scope(),
            ),
            (_string(b"\xff\x01\x00\x01\x00"),),
        )),
        _grease(3),
        _string(b"\x00\x01\x00"),
        _padding(),
        _end_scope(),
        _end_scope(),
        _end_scope(),
    )


def _generate_grease() -> bytes:
    """One ``Grease::init``: keep the high nibble, force the low one to ``a``.

    https://github.com/tdlib/td/blob/d1085f9/td/mtproto/TlsInit.cpp#L28-L38
    """
    grease = bytearray(secrets.token_bytes(_GREASE_SIZE))

    for index in range(_GREASE_SIZE):
        grease[index] = (grease[index] & 0xF0) + 0x0A

    # Neighbouring values must differ: a repeated pair is not a shape the
    # browser being imitated ever produces.
    for index in range(1, _GREASE_SIZE, 2):
        if grease[index] == grease[index - 1]:
            grease[index] ^= 0x10

    return bytes(grease)


def _curve25519_y_squared(x: int) -> int:
    # y^2 = x^3 + 486662*x^2 + x, in the nesting TDLib's get_y2 evaluates it.
    return ((x + _CURVE25519_A) * x + 1) * x % _CURVE25519_PRIME


def _curve25519_double_x(x: int) -> int:
    # The u-coordinate of twice the point at x: (x^2 - 1)^2 / (4*y^2).
    denominator = _curve25519_y_squared(x) * 4 % _CURVE25519_PRIME
    numerator = pow(x * x - 1, 2, _CURVE25519_PRIME)

    return (
        numerator * pow(denominator, _CURVE25519_PRIME - 2, _CURVE25519_PRIME) % _CURVE25519_PRIME
    )


def _generate_curve25519_key() -> bytes:
    """One ``Type::Key`` op: a public key redrawn until it lands on the curve.

    https://github.com/tdlib/td/blob/d1085f9/td/mtproto/TlsInit.cpp#L420-L440
    """
    residue_exponent = (_CURVE25519_PRIME - 1) // 2

    while True:
        candidate = bytearray(secrets.token_bytes(_CURVE25519_KEY_SIZE))
        candidate[31] &= 0x7F
        x = int.from_bytes(bytes(candidate), "big")

        # Half of all x sit on the curve's twist rather than the curve, and a
        # point on the twist is precisely what a fingerprinter would notice.
        if pow(_curve25519_y_squared(x), residue_exponent, _CURVE25519_PRIME) == 1:
            break

    for _ in range(3):
        x = _curve25519_double_x(x)

    return x.to_bytes(_CURVE25519_KEY_SIZE, "little")


def _generate_ml_kem_768_key() -> bytes:
    """One ``Type::MlKem768Key`` op: 384 coefficient pairs, then a 32-byte seed.

    https://github.com/tdlib/td/blob/d1085f9/td/mtproto/TlsInit.cpp#L441-L451
    """
    key = bytearray()

    for _ in range(_ML_KEM_768_COEFFICIENT_PAIRS):
        first = secrets.randbits(32) % _ML_KEM_768_MODULUS
        second = secrets.randbits(32) % _ML_KEM_768_MODULUS

        # Two 12-bit coefficients packed little-endian into three bytes.
        key.append(first & 0xFF)
        key.append((first >> 8) | ((second & 0x0F) << 4))
        key.append(second >> 4)

    return bytes(key) + secrets.token_bytes(_ML_KEM_768_SEED_SIZE)


def _shuffled(parts: list[bytes]) -> list[bytes]:
    # A Fisher-Yates pass over a cryptographic source, matching TDLib's own.
    shuffled = list(parts)

    for index in range(len(shuffled) - 1):
        target = index + secrets.randbelow(len(shuffled) - index)
        shuffled[index], shuffled[target] = shuffled[target], shuffled[index]

    return shuffled


class _HelloWriter:
    def __init__(self, *, grease: bytes, domain: bytes) -> None:
        self._grease = grease
        self._domain = domain

        self._out = bytearray()
        self._scopes: list[int] = []

    def render(self, ops: Sequence[_Op]) -> bytearray:
        for op in ops:
            self._write(op)

        return self._out

    def _write(self, op: _Op) -> None:
        if op.kind is _OpKind.STRING:
            self._out += op.data
        elif op.kind is _OpKind.RANDOM:
            self._out += secrets.token_bytes(op.length)
        elif op.kind is _OpKind.ZERO:
            self._out += bytes(op.length)
        elif op.kind is _OpKind.DOMAIN:
            self._out += self._domain
        elif op.kind is _OpKind.GREASE:
            self._out += bytes((self._grease[op.seed],)) * 2
        elif op.kind is _OpKind.BEGIN_SCOPE:
            self._scopes.append(len(self._out))
            self._out += bytes(_SCOPE_LENGTH_SIZE)
        elif op.kind is _OpKind.END_SCOPE:
            self._close_scope()
        elif op.kind is _OpKind.KEY:
            self._out += _generate_curve25519_key()
        elif op.kind is _OpKind.ML_KEM_768_KEY:
            self._out += _generate_ml_kem_768_key()
        elif op.kind is _OpKind.PERMUTATION:
            self._write_permutation(op.parts)
        elif op.kind is _OpKind.PADDING:
            self._write_padding()
        else:
            raise ValueError(f"fake-TLS: unhandled op kind {op.kind}")

    def _close_scope(self) -> None:
        begin = self._scopes.pop()
        size = len(self._out) - begin - _SCOPE_LENGTH_SIZE

        self._out[begin : begin + _SCOPE_LENGTH_SIZE] = size.to_bytes(_SCOPE_LENGTH_SIZE, "big")

    def _write_permutation(self, parts: tuple[tuple[_Op, ...], ...]) -> None:
        # Each extension is rendered on its own and the finished blocks are then
        # shuffled, so no scope ever spans two of them.
        rendered = [
            bytes(_HelloWriter(grease=self._grease, domain=self._domain).render(part))
            for part in parts
        ]

        for part in _shuffled(rendered):
            self._out += part

    def _write_padding(self) -> None:
        size = _PADDING_TARGET_OFFSET - len(self._out)

        if size <= 0:
            return

        # Extension type 21, TLS's own padding extension.
        self._write(_string(b"\x00\x15"))
        self._write(_begin_scope())
        self._write(_zero(size))
        self._write(_end_scope())


class FakeTlsHello(NamedTuple):
    record: bytes
    """The ClientHello record, ready to go on the wire."""

    random: bytes
    """Its random field, which the proxy's reply is checked against."""


def build_client_hello(*, domain: str, secret: bytes, unix_time: int) -> FakeTlsHello:
    """The greeting for ``domain``, authenticated with the proxy's 16-byte secret."""
    hello = _HelloWriter(grease=_generate_grease(), domain=domain.encode("ascii")).render(
        _client_hello_ops()
    )

    # The digest covers the greeting with its random field still zeroed. The
    # last four bytes then carry the clock, so a proxy can tell a replayed
    # greeting from a fresh one.
    digest = bytearray(hmac.new(secret, bytes(hello), hashlib.sha256).digest())
    timestamp = (unix_time & 0xFFFFFFFF).to_bytes(_TIMESTAMP_SIZE, "little")

    for index in range(_TIMESTAMP_SIZE):
        digest[_RANDOM_SIZE - _TIMESTAMP_SIZE + index] ^= timestamp[index]

    hello[_RANDOM_OFFSET : _RANDOM_OFFSET + _RANDOM_SIZE] = digest

    return FakeTlsHello(record=bytes(hello), random=bytes(digest))


def server_hello_is_authentic(response: bytes, *, secret: bytes, client_random: bytes) -> bool:
    """Whether ``response`` came from a proxy that knows the secret.

    Without this check a censor could answer the greeting with a plausible
    ServerHello of its own and watch what the client does next.
    """
    end = _RANDOM_OFFSET + _RANDOM_SIZE

    if len(response) < end:
        return False

    server_random = response[_RANDOM_OFFSET:end]
    zeroed = response[:_RANDOM_OFFSET] + bytes(_RANDOM_SIZE) + response[end:]
    digest = hmac.new(secret, client_random + zeroed, hashlib.sha256).digest()

    return hmac.compare_digest(digest, server_random)
