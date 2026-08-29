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

from typing import TYPE_CHECKING

from pyrogram import raw, types, utils
from pyrogram.types.object import Object

if TYPE_CHECKING:
    from datetime import datetime


class BusinessConnection(Object):
    """Business information of a user.

    Parameters:
        id (``str``):
            Unique identifier of the business connection that belongs to the user.

        user (:obj:`~pyrogram.types.User`):
            Business account user that created the business connection.

        dc_id (``int``):
            Datacenter identifier of the user.

        date (:py:obj:`~datetime.datetime`):
            Date the connection was established in Unix time.

        is_enabled (``bool``, *optional*):
            True, if the connection is active.

        permissions (:obj:`~pyrogram.types.BusinessBotRights`, *optional*):
            Permissions for the business bot.
    """

    def __init__(
        self,
        *,
        id: str,
        user: types.User,
        dc_id: int,
        date: datetime,
        is_enabled: bool | None = None,
        rights: types.BusinessBotRights | None = None,
    ):
        self.id = id
        self.user = user
        self.dc_id = dc_id
        self.date = date
        self.is_enabled = is_enabled
        self.rights = rights

    @staticmethod
    def _parse(
        client,
        connection: raw.types.BotBusinessConnection
        | raw.types.UpdateBotBusinessConnect
        | None = None,
        users: dict[int, raw.types.User] | None = None,
    ) -> BusinessConnection | None:
        if not connection:
            return None

        if isinstance(connection, raw.types.UpdateBotBusinessConnect):
            connection = connection.connection

        return BusinessConnection(
            id=connection.connection_id,
            user=types.User._parse(client, (users or {}).get(connection.user_id)),
            dc_id=connection.dc_id,
            date=utils.timestamp_to_datetime(connection.date),
            is_enabled=not connection.disabled,
            rights=types.BusinessBotRights._parse(connection.rights),
        )
