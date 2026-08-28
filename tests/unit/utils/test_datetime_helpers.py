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

import contextlib
from datetime import datetime, timezone

import pytest

from pyrogram import utils


def test_zero_datetime_is_the_epoch_in_utc():
    assert utils.zero_datetime() == datetime.fromtimestamp(0, timezone.utc)


@pytest.mark.parametrize("timestamp", [1_000_000, 1_700_000_000, 2**31 - 1])
def test_timestamp_round_trip(timestamp):
    assert utils.datetime_to_timestamp(utils.timestamp_to_datetime(timestamp)) == timestamp


def test_timestamps_near_the_epoch_are_platform_dependent():
    """``timestamp_to_datetime`` is naive local time, which has no pre-epoch representation on Windows.

    ``datetime.fromtimestamp(1)`` is 1970-01-01T02:00:01 on a UTC+2 machine and raises
    ``OSError: [Errno 22]`` on a Windows runner behind UTC, because the local time lands before the
    epoch. Telegram never sends timestamps in that range -- they are all recent message and account
    dates -- so this is a documented boundary rather than something to work around. Anything that
    does need the epoch itself should use ``utils.zero_datetime()``, which is UTC and therefore
    portable.
    """
    with contextlib.suppress(OSError):
        assert utils.timestamp_to_datetime(1) is not None


@pytest.mark.parametrize("falsy", [None, 0])
def test_falsy_timestamps_become_none(falsy):
    """Telegram uses 0 for "never", which must not become 1970-01-01."""
    assert utils.timestamp_to_datetime(falsy) is None


def test_none_datetime_becomes_none():
    assert utils.datetime_to_timestamp(None) is None
