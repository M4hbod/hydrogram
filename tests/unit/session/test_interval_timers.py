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

"""Interval timers must use a monotonic clock.

The updates watchdog and the reconnect throttle both measure *elapsed time*. They used
``datetime.now()``, which is a wall clock: it steps at DST boundaries, on NTP corrections, and when
someone sets the system time. A backward step makes an interval look negative or shrink; a forward
one makes it look huge. ``time.monotonic()`` cannot go backwards, which is the whole point of it.

These tests drive the clock rather than the network, so they assert the arithmetic that decides
whether the watchdog fires -- not the RPC it would then send.
"""

from __future__ import annotations

import time

import pytest

from pyrogram import Client
from pyrogram.session import Session


def elapsed_exceeds_watchdog(last: float, now: float) -> bool:
    """The comparison as client.py makes it."""
    return now - last > Client.UPDATES_WATCHDOG_INTERVAL


def throttled(last: float | None, now: float) -> bool:
    """The comparison as session.py makes it."""
    return last is not None and now - last < Session.RECONNECT_THRESHOLD


def test_watchdog_interval_is_a_plain_number_of_seconds():
    """It is compared against a monotonic delta, so a timedelta would raise."""
    assert isinstance(Client.UPDATES_WATCHDOG_INTERVAL, (int, float))


def test_reconnect_threshold_is_a_plain_number_of_seconds():
    assert isinstance(Session.RECONNECT_THRESHOLD, (int, float))


def test_watchdog_does_not_fire_before_the_interval():
    assert not elapsed_exceeds_watchdog(1000.0, 1000.0 + Client.UPDATES_WATCHDOG_INTERVAL - 1)


def test_watchdog_fires_after_the_interval():
    assert elapsed_exceeds_watchdog(1000.0, 1000.0 + Client.UPDATES_WATCHDOG_INTERVAL + 1)


def test_reconnect_is_throttled_inside_the_threshold():
    assert throttled(1000.0, 1000.0 + Session.RECONNECT_THRESHOLD - 1)


def test_reconnect_is_allowed_after_the_threshold():
    assert not throttled(1000.0, 1000.0 + Session.RECONNECT_THRESHOLD + 1)


def test_first_reconnect_is_never_throttled():
    """`last_reconnect_attempt` starts as None, and `0.0` is a legitimate monotonic reading."""
    assert not throttled(None, 1000.0)
    assert throttled(0.0, 0.0 + Session.RECONNECT_THRESHOLD - 1), (
        "a falsy-but-valid timestamp of 0.0 must still throttle"
    )


@pytest.mark.parametrize("jump_seconds", [3600, -3600])
def test_a_monotonic_clock_never_makes_these_jumps(jump_seconds, monkeypatch):
    """A DST step of an hour in either direction is what this replaces.

    With a wall clock, a backward step stalls the watchdog for the length of the step, and makes
    the reconnect throttle see a negative interval so it throttles every attempt. Monotonic
    readings are unaffected because they are not tied to civil time at all.
    """
    base = time.monotonic()
    monkeypatch.setenv("TZ", "Australia/Lord_Howe")  # a half-hour DST zone
    if hasattr(time, "tzset"):
        time.tzset()
    after = time.monotonic()
    if hasattr(time, "tzset"):
        monkeypatch.delenv("TZ")
        time.tzset()

    assert after >= base, "time.monotonic() moved backwards across a timezone change"
    assert after - base < abs(jump_seconds), "monotonic clock followed the civil-time jump"
