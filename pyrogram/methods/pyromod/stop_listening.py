#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2020-present Cezar H. <https://github.com/usernein>
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

from pyrogram.types import Identifier, ListenerTypes

if TYPE_CHECKING:
    import pyrogram


class StopListening:
    async def stop_listening(
        self: pyrogram.Client,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        chat_id: int | str | list[int | str] | None = None,
        user_id: int | str | list[int | str] | None = None,
        message_id: int | list[int] | None = None,
        inline_message_id: str | list[str] | None = None,
    ):
        """
        Stops all listeners that match the given identifier pattern.
        Uses :meth:`pyrogram.Client.get_many_listeners_matching_with_identifier_pattern`.

        Parameters:
            listener_type (:obj:`~pyrogram.types.ListenerTypes`):
                The type of listener to stop. Must be a value from :class:`pyrogram.types.ListenerTypes`.

            chat_id (``Union[int, str], List[Union[int, str]]``):
                The chat_id to match against.

            user_id (``Union[int, str], List[Union[int, str]]``):
                The user_id to match against.

            message_id (``Union[int, List[int]]``):
                The message_id to match against.

            inline_message_id (``Union[str, List[str]]``):
                The inline_message_id to match against.
        """
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        listeners = self.get_many_listeners_matching_with_identifier_pattern(
            pattern, listener_type
        )

        for listener in listeners:
            await self.stop_listener(listener)
