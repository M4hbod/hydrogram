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

"""Filter algebra.

``&``, ``|`` and ``~`` build a tree that the dispatcher walks for every update, so their
short-circuit behaviour is a hot path as well as a correctness question: a filter that runs when it
should have been skipped can make a network call per message.
"""

from __future__ import annotations

import asyncio

import pytest

from pyrogram import filters
from tests.unit.filters import Message


class Client:
    """Enough of a Client for the filter machinery.

    Sync filter callbacks are dispatched through ``client.loop.run_in_executor(client.executor,
    ...)`` so they cannot block the event loop, so a stub without a loop fails on every sync
    filter. ``executor=None`` means the default thread pool, which is what a real Client uses when
    none is configured.
    """

    executor = None

    @property
    def loop(self):
        return asyncio.get_running_loop()


client = Client()


def always(value: bool):
    return filters.create(lambda _flt, _client, _update: value)


async def evaluate(flt, update=None) -> bool:
    return await flt(client, update if update is not None else Message("x"))


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(True, True, True), (True, False, False), (False, True, False), (False, False, False)],
)
async def test_and_truth_table(left, right, expected):
    assert await evaluate(always(left) & always(right)) is expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(True, True, True), (True, False, True), (False, True, True), (False, False, False)],
)
async def test_or_truth_table(left, right, expected):
    assert await evaluate(always(left) | always(right)) is expected


@pytest.mark.parametrize("value", [True, False])
async def test_invert(value):
    assert await evaluate(~always(value)) is not value


async def test_double_invert_is_identity():
    assert await evaluate(~~always(True)) is True


async def test_and_short_circuits_on_a_false_left():
    """The right-hand side must not run: it is where the expensive filters live."""
    calls = []

    def record(_flt, _client, _update):
        calls.append(1)
        return True

    await evaluate(always(False) & filters.create(record))
    assert calls == []


async def test_or_short_circuits_on_a_true_left():
    calls = []

    def record(_flt, _client, _update):
        calls.append(1)
        return True

    await evaluate(always(True) | filters.create(record))
    assert calls == []


async def test_combinators_nest():
    combined = (always(True) & always(False)) | (~always(False) & always(True))
    assert await evaluate(combined) is True


async def test_async_and_sync_callbacks_both_work():
    async def async_filter(_flt, _client, _update):
        await asyncio.sleep(0)  # a coroutine that never awaits is not the case under test
        return True

    def sync_filter(_flt, _client, _update):
        return True

    assert await evaluate(filters.create(async_filter) & filters.create(sync_filter)) is True
