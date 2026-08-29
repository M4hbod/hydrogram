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
import logging
import struct
import time
from itertools import starmap
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiosqlite

from pyrogram import raw, utils

from .base import BaseStorage, InputPeer, UpdateState

if TYPE_CHECKING:
    from collections.abc import Iterable

SCHEMA = """
CREATE TABLE sessions
(
    dc_id     INTEGER PRIMARY KEY,
    api_id    INTEGER,
    test_mode INTEGER,
    auth_key  BLOB,
    date      INTEGER NOT NULL,
    user_id   INTEGER,
    is_bot    INTEGER
);

CREATE TABLE peers
(
    id             INTEGER PRIMARY KEY,
    access_hash    INTEGER,
    type           INTEGER NOT NULL,
    username       TEXT,
    phone_number   TEXT,
    last_update_on INTEGER NOT NULL DEFAULT (CAST(STRFTIME('%s', 'now') AS INTEGER))
);

CREATE TABLE version
(
    number INTEGER PRIMARY KEY
);

CREATE INDEX idx_peers_id ON peers (id);
CREATE INDEX idx_peers_username ON peers (username);
CREATE INDEX idx_peers_phone_number ON peers (phone_number);

CREATE TRIGGER trg_peers_last_update_on
    AFTER UPDATE
    ON peers
BEGIN
    UPDATE peers
    SET last_update_on = CAST(STRFTIME('%s', 'now') AS INTEGER)
    WHERE id = NEW.id;
END;
"""

# Kept apart from SCHEMA so a session file created before version 4 can be
# brought up to date with the same statement a fresh one is created with.
UPDATE_STATE_SCHEMA = """
CREATE TABLE update_state
(
    id   INTEGER PRIMARY KEY,
    pts  INTEGER,
    qts  INTEGER,
    date INTEGER,
    seq  INTEGER
);
"""


def get_input_peer(peer_id: int, access_hash: int, peer_type: str) -> InputPeer:
    if peer_type in {"user", "bot"}:
        return raw.types.InputPeerUser(user_id=peer_id, access_hash=access_hash)
    if peer_type == "group":
        return raw.types.InputPeerChat(chat_id=-peer_id)
    if peer_type in {"channel", "supergroup"}:
        return raw.types.InputPeerChannel(
            channel_id=utils.get_channel_id(peer_id), access_hash=access_hash
        )
    raise ValueError(f"Invalid peer type: {peer_type}")


class SQLiteStorage(BaseStorage):
    VERSION = 4
    USERNAME_TTL = 8 * 60 * 60
    FILE_EXTENSION = ".session"

    def __init__(
        self,
        name: str,
        workdir: Path | None = None,
        session_string: str | None = None,
        use_memory: bool = False,
    ):
        super().__init__(name)
        self.database: str | Path = (
            ":memory:"
            if use_memory
            else (workdir / (self.name + self.FILE_EXTENSION) if workdir else ":memory:")
        )
        self.session_string: str | None = session_string
        self.conn: aiosqlite.Connection | None = None

    async def update(self) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        version: int | None = await self.version()

        if version == 1:
            await self.conn.execute("DELETE FROM peers")
            version += 1

        if version == 2:
            await self.conn.execute("ALTER TABLE sessions ADD api_id INTEGER")
            version += 1

        if version == 3:
            await self.conn.executescript(UPDATE_STATE_SCHEMA)
            version += 1

        await self.version(version)
        await self.conn.commit()

    async def create(self) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        await self.conn.executescript(SCHEMA)
        await self.conn.executescript(UPDATE_STATE_SCHEMA)
        await self.conn.execute(
            "INSERT INTO version VALUES (?)",
            (self.VERSION,),
        )
        await self.conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
            (2, None, None, None, 0, None, None),
        )
        await self.conn.commit()

    async def open(self) -> None:
        path = self.database
        file_exists = isinstance(path, Path) and path.is_file()

        self.conn = await aiosqlite.connect(self.database)

        await self.conn.execute("PRAGMA journal_mode=WAL")

        if file_exists:
            await self.update()
            await self.conn.execute("VACUUM")
        else:
            await self.create()

        await self.conn.commit()

        if self.session_string:
            await self._load_session_string()

    async def _load_session_string(self) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        if self.session_string:
            dc_id, api_id, test_mode, auth_key, user_id, is_bot = struct.unpack(
                self.SESSION_STRING_FORMAT,
                base64.urlsafe_b64decode(
                    self.session_string + "=" * (-len(self.session_string) % 4)
                ),
            )

            await self.dc_id(dc_id)
            await self.api_id(api_id)
            await self.test_mode(test_mode)
            await self.auth_key(auth_key)
            await self.user_id(user_id)
            await self.is_bot(is_bot)
            await self.date(0)

    async def save(self) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        await self.date(int(time.time()))
        await self.conn.commit()

    async def close(self) -> None:
        if not self.conn:
            return

        # sqlite rolls an open transaction back on close, and update states are
        # written without committing each one -- so closing without this throws
        # away everything learned since the last save.
        try:
            await self.conn.commit()
        except Exception as e:
            logging.warning("Could not flush the session before closing: %s", e)

        await self.conn.close()

    async def delete(self) -> None:
        if self.database != ":memory:":
            Path(self.database).unlink()

    async def update_peers(
        self, peers: list[tuple[int, int, str, str | None, str | None]]
    ) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        await self.conn.executemany(
            "REPLACE INTO peers (id, access_hash, type, username, phone_number) "
            "VALUES (?, ?, ?, ?, ?)",
            peers,
        )
        await self.conn.commit()

    async def get_peer_by_id(self, peer_id: int) -> InputPeer | None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return None

        q = await self.conn.execute(
            "SELECT id, access_hash, type FROM peers WHERE id = ?", (peer_id,)
        )
        r = await q.fetchone()
        if not r:
            raise KeyError(f"ID not found: {peer_id}")

        return get_input_peer(*r)

    async def get_peer_by_username(self, username: str) -> InputPeer | None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return None

        q = await self.conn.execute(
            "SELECT id, access_hash, type, last_update_on "
            "FROM peers "
            "WHERE username = ? "
            "ORDER BY last_update_on DESC",
            (username,),
        )
        r = await q.fetchone()
        if not r:
            raise KeyError(f"Username not found: {username}")

        if abs(time.time() - r[3]) > self.USERNAME_TTL:
            raise KeyError(f"Username expired: {username}")

        return get_input_peer(*r[:3])

    async def get_peer_by_phone_number(self, phone_number: str) -> InputPeer | None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return None

        q = await self.conn.execute(
            "SELECT id, access_hash, type FROM peers WHERE phone_number = ?", (phone_number,)
        )
        r = await q.fetchone()
        if not r:
            raise KeyError(f"Phone number not found: {phone_number}")

        return get_input_peer(*r)

    async def get_update_states(self, ids: int | Iterable[int] | None = None) -> list[UpdateState]:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return []

        query = "SELECT id, pts, qts, date, seq FROM update_state"
        state_ids: tuple[int, ...] = ()

        if ids is not None:
            state_ids = (ids,) if isinstance(ids, int) else tuple(ids)

            if not state_ids:
                return []

            placeholders = ", ".join("?" for _ in state_ids)
            query += f" WHERE id IN ({placeholders})"

        q = await self.conn.execute(f"{query} ORDER BY date ASC", state_ids)

        return list(starmap(UpdateState, await q.fetchall()))

    async def set_update_state(self, update_state: UpdateState | Iterable[UpdateState]) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        states = [update_state] if isinstance(update_state, UpdateState) else list(update_state)

        if not states:
            return

        # COALESCE, not a plain assignment: an update carries only the counters
        # it advances, so writing its None fields over the stored ones would
        # throw away the parts of the state it says nothing about.
        await self.conn.executemany(
            "INSERT INTO update_state (id, pts, qts, date, seq) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "pts = COALESCE(excluded.pts, update_state.pts), "
            "qts = COALESCE(excluded.qts, update_state.qts), "
            "date = COALESCE(excluded.date, update_state.date), "
            "seq = COALESCE(excluded.seq, update_state.seq)",
            [(state.id, state.pts, state.qts, state.date, state.seq) for state in states],
        )

    async def delete_update_state(self, state_id: int | Iterable[int]) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        state_ids = (state_id,) if isinstance(state_id, int) else tuple(state_id)

        if not state_ids:
            return

        placeholders = ", ".join("?" for _ in state_ids)

        await self.conn.execute(
            f"DELETE FROM update_state WHERE id IN ({placeholders})", state_ids
        )

    async def _get(self, attr: str) -> Any:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return None

        q = await self.conn.execute(f"SELECT {attr} FROM sessions")
        row = await q.fetchone()
        return row[0] if row else None

    async def _set(self, attr: str, value: Any) -> None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return

        await self.conn.execute(f"UPDATE sessions SET {attr} = ?", (value,))
        await self.conn.commit()

    async def _accessor(self, attr: str, value: Any = object) -> Any | None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return None

        if value is object:
            return await self._get(attr)

        await self._set(attr, value)
        return None

    async def dc_id(self, value: int | object = object) -> int | None:
        return await self._accessor("dc_id", value)

    async def api_id(self, value: int | object = object) -> int | None:
        return await self._accessor("api_id", value)

    async def test_mode(self, value: bool | object = object) -> bool | None:
        return await self._accessor("test_mode", value)

    async def auth_key(self, value: bytes | object = object) -> bytes | None:
        return await self._accessor("auth_key", value)

    async def date(self, value: int | object = object) -> int | None:
        return await self._accessor("date", value)

    async def user_id(self, value: int | object = object) -> int | None:
        return await self._accessor("user_id", value)

    async def is_bot(self, value: bool | object = object) -> bool | None:
        return await self._accessor("is_bot", value)

    async def version(self, value: int | object = object) -> int | None:
        if not self.conn:
            logging.warning("Database connection is not available.")
            return None

        if value is object:
            q = await self.conn.execute("SELECT number FROM version")
            row = await q.fetchone()
            return row[0] if row else None

        await self.conn.execute("UPDATE version SET number = ?", (value,))
        await self.conn.commit()
        return None
