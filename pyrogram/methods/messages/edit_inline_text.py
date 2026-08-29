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

import pyrogram
from pyrogram import enums, raw, types, utils

from .inline_session import get_session


class EditInlineText:
    async def edit_inline_text(
        self: pyrogram.Client,
        inline_message_id: str,
        text: str,
        parse_mode: enums.ParseMode | None = None,
        link_preview_options: types.LinkPreviewOptions | None = None,
        reply_markup: types.InlineKeyboardMarkup = None,
        rich_message: types.InputRichMessage | None = None,
        entities: list[types.MessageEntity] | None = None,
    ) -> bool:
        """Edit the text of inline messages.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            inline_message_id (``str``):
                Identifier of the inline message.

            text (``str``):
                New text of the message.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            link_preview_options (:obj:`~pyrogram.types.LinkPreviewOptions`, *optional*):
                Options for how the link preview is generated. Only ``is_disabled`` and
                ``show_above_text`` apply when editing; the previewed URL cannot be changed.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.

            rich_message (:obj:`~pyrogram.types.InputRichMessage`, *optional*):
                New rich content for the message. Required when *text* is not given.

            entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
                List of special entities in the text, which can be specified instead of *parse_mode*.

        Returns:
            ``bool``: On success, True is returned.

        Example:
            .. code-block:: python

                # Bots only

                # Simple edit text
                await app.edit_inline_text(inline_message_id, "new text")

                # Take the same text message, remove the web page preview only
                await app.edit_inline_text(
                    inline_message_id,
                    message.text,
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
        """

        unpacked = utils.unpack_inline_message_id(inline_message_id)
        dc_id = unpacked.dc_id

        session = await get_session(self, dc_id)

        return await session.invoke(
            raw.functions.messages.EditInlineBotMessage(
                id=unpacked,
                no_webpage=(link_preview_options.is_disabled if link_preview_options else None)
                or None,
                invert_media=(
                    link_preview_options.show_above_text if link_preview_options else None
                ),
                reply_markup=await reply_markup.write(self) if reply_markup else None,
                rich_message=rich_message.write() if rich_message else None,
                **await utils.parse_text_entities(self, text, parse_mode, entities),
            ),
            sleep_threshold=self.sleep_threshold,
        )
