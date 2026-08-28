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

from pyrogram import utils


@pytest.mark.parametrize("value", [0, 1, 255, 256, 2**64, 2**256 - 1])
def test_itob_btoi_round_trip(value):
    assert utils.btoi(utils.itob(value)) == value


def test_xor_is_its_own_inverse():
    a, b = b"\x00\x0f\xf0\xff", b"\xaa\xbb\xcc\xdd"
    assert utils.xor(utils.xor(a, b), b) == a


def test_xor_of_a_value_with_itself_is_zero():
    a = bytes(range(32))
    assert utils.xor(a, a) == bytes(32)


def test_sha256_is_the_standard_digest():
    assert utils.sha256(b"pyrogram") == hashlib.sha256(b"pyrogram").digest()
