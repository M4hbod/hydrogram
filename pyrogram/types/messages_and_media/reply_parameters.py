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

from pyrogram.types.object import Object

if TYPE_CHECKING:
    from pyrogram import enums, types


class ReplyParameters(Object):
    """Describes the message to reply to.

    Replaces the flat ``reply_to_message_id`` parameter. Grouping the fields makes the mutually
    exclusive combinations expressible: a reply carries either a message, a story or an ephemeral
    message, and a quote only means something alongside a message.

    Parameters:
        message_id (``int``, *optional*):
            Identifier of the message to reply to in the current chat, or in *chat_id* if given.
            Required unless *ephemeral_message_id* or *story_id* is specified.

        story_id (``int``, *optional*):
            Unique identifier of the story to reply to.

        chat_id (``int`` | ``str``, *optional*):
            Unique identifier (int) or username (str) of the chat the replied-to message is in,
            when it is not the chat being sent to.
            Not supported for messages sent on behalf of a business account, or in channel direct
            messages chats.

        ephemeral_message_id (``int``, *optional*):
            Identifier of an incoming ephemeral message to reply to. The reply must itself be an
            ephemeral message, and must be sent within 15 seconds of the original.
            Required unless *message_id* is specified.

        quote (``str``, *optional*):
            The quoted part of the message being replied to, 0-1024 characters after entities
            parsing. Must be an exact substring of the replied-to message, including its bold,
            italic, underline, strikethrough, spoiler and custom_emoji entities; the send fails if
            the quote is not found.

        quote_parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
            By default, quotes are parsed using both Markdown and HTML styles.
            You can combine both syntaxes together.

        quote_entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            List of special entities that appear in the quote, which can be specified instead of
            *quote_parse_mode*.

        quote_position (``int``, *optional*):
            Position of the quote in the original message, in UTF-16 code units.

        checklist_task_id (``int``, *optional*):
            Identifier of the specific checklist task being replied to.

        poll_option_id (``str``, *optional*):
            Persistent identifier of the specific poll option being replied to.
    """

    def __init__(
        self,
        *,
        message_id: int | None = None,
        story_id: int | None = None,
        chat_id: int | str | None = None,
        ephemeral_message_id: int | None = None,
        quote: str | None = None,
        quote_parse_mode: enums.ParseMode | None = None,
        quote_entities: list[types.MessageEntity] | None = None,
        quote_position: int | None = None,
        checklist_task_id: int | None = None,
        poll_option_id: str | None = None,
    ):
        super().__init__()

        self.message_id = message_id
        self.story_id = story_id
        self.chat_id = chat_id
        self.ephemeral_message_id = ephemeral_message_id
        self.quote = quote
        self.quote_parse_mode = quote_parse_mode
        self.quote_entities = quote_entities
        self.quote_position = quote_position
        self.checklist_task_id = checklist_task_id
        self.poll_option_id = poll_option_id
