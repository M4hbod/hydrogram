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

from datetime import datetime, timezone

import pytest

from pyrogram import utils


def test_zero_datetime_is_the_epoch_in_utc():
    assert utils.zero_datetime() == datetime.fromtimestamp(0, timezone.utc)


@pytest.mark.parametrize("timestamp", [1, 1000000, 2**31 - 1])
def test_timestamp_round_trip(timestamp):
    assert utils.datetime_to_timestamp(utils.timestamp_to_datetime(timestamp)) == timestamp


@pytest.mark.parametrize("falsy", [None, 0])
def test_falsy_timestamps_become_none(falsy):
    """Telegram uses 0 for "never", which must not become 1970-01-01."""
    assert utils.timestamp_to_datetime(falsy) is None


def test_none_datetime_becomes_none():
    assert utils.datetime_to_timestamp(None) is None
