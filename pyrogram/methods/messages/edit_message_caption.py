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

from pyrogram import types

if TYPE_CHECKING:
    from datetime import datetime

    import pyrogram
    from pyrogram import enums


class EditMessageCaption:
    async def edit_message_caption(
        self: pyrogram.Client,
        chat_id: int | str,
        message_id: int,
        caption: str,
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        reply_markup: types.InlineKeyboardMarkup = None,
        business_connection_id: str | None = None,
        schedule_date: datetime | None = None,
        show_caption_above_media: bool | None = None,
    ) -> types.Message:
        """Edit the caption of media messages.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            message_id (``int``):
                Message identifier in the chat specified in chat_id.

            caption (``str``):
                New caption of the media message.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.

            business_connection_id (``str``, *optional*):
                Unique identifier of the business connection to act on behalf of.

            schedule_date (``datetime``, *optional*):
                Date when the edit will be applied, for a scheduled message.

            show_caption_above_media (``bool``, *optional*):
                Pass True if the caption must be shown above the message media.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the edited message is returned.

        Example:
            .. code-block:: python

                await app.edit_message_caption(chat_id, message_id, "new media caption")
        """
        return await self.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=caption,
            parse_mode=parse_mode,
            entities=caption_entities,
            reply_markup=reply_markup,
            schedule_date=schedule_date,
            business_connection_id=business_connection_id,
            # Telegram has one wire flag for "put the text above the media",
            # and link previews are the other thing that sets it.
            link_preview_options=(
                types.LinkPreviewOptions(show_above_text=show_caption_above_media)
                if show_caption_above_media is not None
                else None
            ),
        )
