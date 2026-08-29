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

"""Per-chat update counters -- what ``Client.recover_gaps`` catches up from.

A wrong counter here does not fail loudly: it silently re-delivers updates the
handlers already saw, or silently loses the ones they did not.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import aiosqlite
import pytest

from pyrogram.storage import SQLiteStorage, UpdateState
from pyrogram.storage.sqlite_storage import SCHEMA

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
async def storage():
    store = SQLiteStorage("test", use_memory=True)
    await store.open()
    yield store
    await store.close()


async def test_a_fresh_session_has_no_states(storage):
    assert await storage.get_update_states() == []


async def test_a_state_round_trips(storage):
    await storage.set_update_state(UpdateState(0, pts=10, qts=20, date=1700000000, seq=3))

    assert await storage.get_update_states() == [UpdateState(0, 10, 20, 1700000000, 3)]


async def test_many_states_are_written_in_one_go(storage):
    await storage.set_update_state([
        UpdateState(0, pts=1, date=100),
        UpdateState(-1001234567890, pts=2, date=200),
    ])

    assert {state.id for state in await storage.get_update_states()} == {0, -1001234567890}


async def test_states_come_back_oldest_first(storage):
    await storage.set_update_state([
        UpdateState(1, date=300),
        UpdateState(2, date=100),
        UpdateState(3, date=200),
    ])

    assert [state.id for state in await storage.get_update_states()] == [2, 3, 1]


async def test_a_none_field_leaves_the_stored_value_alone(storage):
    # This is the whole point of the COALESCE: an update carries only the
    # counters it advances, and writing its None fields over the stored ones
    # would throw away the parts of the state it says nothing about.
    await storage.set_update_state(UpdateState(0, pts=10, qts=20, date=100, seq=1))
    await storage.set_update_state(UpdateState(0, pts=11))

    assert await storage.get_update_states() == [UpdateState(0, 11, 20, 100, 1)]


async def test_ids_filter_the_result(storage):
    await storage.set_update_state([UpdateState(1, pts=1), UpdateState(2, pts=2)])

    assert [state.id for state in await storage.get_update_states(2)] == [2]
    assert [state.id for state in await storage.get_update_states([1, 2])] == [1, 2]


async def test_an_empty_id_list_asks_for_nothing_rather_than_everything(storage):
    await storage.set_update_state(UpdateState(1, pts=1))

    assert await storage.get_update_states([]) == []


async def test_a_state_can_be_forgotten(storage):
    await storage.set_update_state([UpdateState(1, pts=1), UpdateState(2, pts=2)])
    await storage.delete_update_state(1)

    assert [state.id for state in await storage.get_update_states()] == [2]


async def test_several_states_can_be_forgotten_at_once(storage):
    await storage.set_update_state([UpdateState(i, pts=i) for i in (1, 2, 3)])
    await storage.delete_update_state([1, 3])

    assert [state.id for state in await storage.get_update_states()] == [2]


async def test_setting_nothing_is_not_an_error(storage):
    await storage.set_update_state([])
    await storage.delete_update_state([])

    assert await storage.get_update_states() == []


async def test_a_pre_version_4_session_file_gains_the_table(tmp_path: Path):
    # Session files outlive releases: people keep one for years. A migration
    # that forgets a table turns the next start into an OperationalError.
    path = tmp_path / "old.session"

    with sqlite3.connect(path) as legacy:
        legacy.executescript(SCHEMA)
        legacy.execute("INSERT INTO version VALUES (3)")
        legacy.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)", (2, 1, 0, b"", 0, 7, 0)
        )

    store = SQLiteStorage("old", workdir=tmp_path)
    await store.open()
    try:
        assert await store.version() == 4

        await store.set_update_state(UpdateState(0, pts=5))
        assert await store.get_update_states() == [UpdateState(0, 5, None, None, None)]
    finally:
        await store.close()


async def test_a_fresh_session_file_is_created_at_the_current_version(tmp_path: Path):
    store = SQLiteStorage("new", workdir=tmp_path)
    await store.open()
    try:
        assert await store.version() == SQLiteStorage.VERSION

        async with aiosqlite.connect(tmp_path / "new.session") as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'update_state'"
            )

            assert await cursor.fetchone() is not None
    finally:
        await store.close()


async def test_states_survive_a_close_and_reopen(tmp_path: Path):
    # They are written without committing each one, and sqlite rolls an open
    # transaction back on close: without a flush, every counter learned during a
    # run is thrown away exactly when it is needed.
    store = SQLiteStorage("kept", workdir=tmp_path)
    await store.open()
    await store.set_update_state(UpdateState(0, pts=99, date=1700000000))
    await store.close()

    reopened = SQLiteStorage("kept", workdir=tmp_path)
    await reopened.open()
    try:
        assert await reopened.get_update_states() == [UpdateState(0, 99, None, 1700000000, None)]
    finally:
        await reopened.close()
