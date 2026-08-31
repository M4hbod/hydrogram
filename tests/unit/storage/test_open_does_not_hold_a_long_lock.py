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

"""Opening a session file must not take a long exclusive lock.

``open()`` used to ``VACUUM`` every existing session file, every time. VACUUM
rewrites the whole database under an exclusive lock for as long as that takes,
which on a network volume is exactly the kind of long write lock that makes
another connection's write fail with ``database is locked``. Once the schema is
current there is nothing for it to do, so it now runs only after a migration.

The other half is the timeout. ``sqlite3.connect`` already defaults to 5
seconds and sets ``busy_timeout`` from it, so a missing pragma was never the
reason a write failed: it does not fail immediately, it waits five seconds
first. What changed is the number, and that it can now be set.
"""

from __future__ import annotations

import aiosqlite
import pytest

from pyrogram.storage import SQLiteStorage
from pyrogram.storage.sqlite_storage import SCHEMA


@pytest.fixture
def session_path(tmp_path):
    return tmp_path


async def statements_run_by_open(storage: SQLiteStorage) -> list[str]:
    """Every SQL statement ``open()`` issues, in order."""
    executed: list[str] = []
    original = aiosqlite.Connection.execute

    async def record(self, sql, *args, **kwargs):
        executed.append(str(sql).strip())
        return await original(self, sql, *args, **kwargs)

    aiosqlite.Connection.execute = record
    try:
        await storage.open()
    finally:
        aiosqlite.Connection.execute = original
    return executed


@pytest.mark.asyncio
async def test_opening_a_current_session_file_does_not_vacuum(session_path):
    store = SQLiteStorage("s", workdir=session_path)
    await store.open()
    await store.close()

    reopened = SQLiteStorage("s", workdir=session_path)
    statements = await statements_run_by_open(reopened)
    await reopened.close()

    assert not any(s.upper().startswith("VACUUM") for s in statements), (
        "VACUUM rewrites the file under an exclusive lock; there was nothing to reclaim"
    )


@pytest.mark.asyncio
async def test_a_migration_still_vacuums(session_path):
    """The one case it was there for: reclaiming what a migration freed."""
    path = session_path / "old.session"

    conn = await aiosqlite.connect(path)
    await conn.executescript(SCHEMA)
    await conn.execute("INSERT INTO version VALUES (3)")
    await conn.execute(
        "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)", (2, None, None, None, 0, None, None)
    )
    await conn.commit()
    await conn.close()

    store = SQLiteStorage("old", workdir=session_path)
    statements = await statements_run_by_open(store)

    assert await store.version() == SQLiteStorage.VERSION
    assert any(s.upper().startswith("VACUUM") for s in statements), (
        "a migration ran, so the space it freed should be reclaimed"
    )
    await store.close()


@pytest.mark.asyncio
async def test_update_reports_whether_it_migrated(session_path):
    path = session_path / "old.session"

    conn = await aiosqlite.connect(path)
    await conn.executescript(SCHEMA)
    await conn.execute("INSERT INTO version VALUES (3)")
    await conn.execute(
        "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)", (2, None, None, None, 0, None, None)
    )
    await conn.commit()
    await conn.close()

    store = SQLiteStorage("old", workdir=session_path)
    await store.open()
    try:
        # Already brought up to date by open(), so there is nothing left to do.
        assert await store.update() is False
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_the_busy_timeout_is_the_one_configured(session_path):
    store = SQLiteStorage("s", workdir=session_path, busy_timeout=12.5)
    await store.open()
    try:
        async with store.conn.execute("PRAGMA busy_timeout") as cursor:
            assert (await cursor.fetchone())[0] == 12500
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_the_default_busy_timeout_is_longer_than_sqlites(session_path):
    """sqlite3 defaults to 5s. Raising it is the whole point of setting it."""
    store = SQLiteStorage("s", workdir=session_path)
    await store.open()
    try:
        async with store.conn.execute("PRAGMA busy_timeout") as cursor:
            timeout = (await cursor.fetchone())[0]
    finally:
        await store.close()

    assert timeout == int(SQLiteStorage.BUSY_TIMEOUT * 1000)
    assert timeout > 5000


@pytest.mark.asyncio
async def test_a_write_waits_for_another_connection_instead_of_failing(session_path):
    """What "database is locked" actually means: the wait ran out, not that there was none."""
    store = SQLiteStorage("s", workdir=session_path, busy_timeout=0.2)
    await store.open()

    holder = await aiosqlite.connect(store.database)
    await holder.execute("BEGIN IMMEDIATE")
    await holder.execute(
        "REPLACE INTO peers (id, access_hash, type, username, phone_number) VALUES (1,1,'user',NULL,NULL)"
    )

    try:
        with pytest.raises(aiosqlite.OperationalError, match="database is locked"):
            await store.update_peers([(2, 2, "user", None, None)])
    finally:
        await holder.rollback()
        await holder.close()
        await store.close()
