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

"""Datetime conversion.

Telegram dates are Unix timestamps -- instants, not wall-clock readings -- so
``timestamp_to_datetime`` returns timezone-aware UTC. That makes the three helpers agree with each
other: before, ``zero_datetime()`` was aware UTC while ``timestamp_to_datetime()`` was naive local,
and comparing a message date against the library's own default raised ``TypeError``.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from pyrogram import utils

# A timestamp with no special properties, well clear of any boundary.
SOME_TIMESTAMP = 1_700_000_000


@pytest.fixture
def timezone_east_of_utc(monkeypatch):
    """Run the body with the process timezone set east of UTC.

    Only matters on platforms where ``time.tzset`` exists (not Windows). A naive-local
    implementation gives different answers under different zones; an aware one does not, which is
    the property these tests are checking.
    """
    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset is unavailable on this platform")
    monkeypatch.setitem(os.environ, "TZ", "Asia/Tehran")
    time.tzset()
    yield
    time.tzset()


def test_zero_datetime_is_the_epoch_in_utc():
    assert utils.zero_datetime() == datetime.fromtimestamp(0, timezone.utc)


def test_timestamp_to_datetime_is_timezone_aware():
    assert utils.timestamp_to_datetime(SOME_TIMESTAMP).tzinfo is not None


def test_timestamp_to_datetime_is_utc():
    converted = utils.timestamp_to_datetime(SOME_TIMESTAMP)
    assert converted.utcoffset() == timedelta(0)
    assert converted == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)


def test_message_dates_are_comparable_with_the_library_default():
    """The regression: these two used to be naive and aware, and comparing them raised."""
    assert utils.timestamp_to_datetime(SOME_TIMESTAMP) > utils.zero_datetime()


def test_message_dates_can_be_subtracted_from_each_other():
    later = utils.timestamp_to_datetime(SOME_TIMESTAMP + 3600)
    earlier = utils.timestamp_to_datetime(SOME_TIMESTAMP)
    assert later - earlier == timedelta(hours=1)


def test_conversion_does_not_depend_on_the_local_timezone(timezone_east_of_utc):
    assert utils.timestamp_to_datetime(SOME_TIMESTAMP) == datetime(
        2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc
    )


@pytest.mark.parametrize("timestamp", [1, 60, 86_400, SOME_TIMESTAMP, 2**31 - 1])
def test_timestamp_round_trip(timestamp):
    """Small timestamps included deliberately.

    ``datetime.fromtimestamp(1)`` with no timezone raises ``OSError: [Errno 22]`` on Windows,
    because the local reading lands before the epoch. Passing ``tz`` skips the platform's
    ``localtime()`` altogether, so the whole range works everywhere.
    """
    assert utils.datetime_to_timestamp(utils.timestamp_to_datetime(timestamp)) == timestamp


@pytest.mark.parametrize("falsy", [None, 0])
def test_falsy_timestamps_become_none(falsy):
    """Telegram uses 0 for "never", which must not become 1970-01-01."""
    assert utils.timestamp_to_datetime(falsy) is None


def test_none_datetime_becomes_none():
    assert utils.datetime_to_timestamp(None) is None


def test_aware_datetimes_convert_exactly():
    aware = datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)
    assert utils.datetime_to_timestamp(aware) == SOME_TIMESTAMP


def test_an_aware_datetime_converts_the_same_from_any_offset():
    utc = datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)
    elsewhere = utc.astimezone(timezone(timedelta(hours=9)))
    assert utils.datetime_to_timestamp(elsewhere) == utils.datetime_to_timestamp(utc)


def test_naive_datetimes_are_still_read_as_local_time(timezone_east_of_utc):
    """Deliberate: naive input keeps Python's own meaning.

    ``datetime.now()`` is naive local, and it is the naive datetime callers actually build. Reading
    naive input as UTC instead would silently shift every such call by the caller's offset.
    """
    naive = datetime(2023, 11, 15, 1, 43, 20)  # Asia/Tehran is UTC+3:30
    assert utils.datetime_to_timestamp(naive) == SOME_TIMESTAMP
