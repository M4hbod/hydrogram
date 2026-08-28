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

import pyrogram
from pyrogram import enums, raw, types, utils

if TYPE_CHECKING:
    from datetime import datetime


class SendMessage:
    async def send_message(
        self: pyrogram.Client,
        chat_id: int | str,
        text: str,
        *,
        message_thread_id: int | None = None,
        parse_mode: enums.ParseMode | None = None,
        entities: list[types.MessageEntity] | None = None,
        link_preview_options: types.LinkPreviewOptions | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        protect_content: bool | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> types.Message:
        """Send text messages.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            text (``str``):
                Text of the message to be sent.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                for forum supergroups only.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

            link_preview_options (:obj:`~pyrogram.types.LinkPreviewOptions`, *optional*):
                Options for how the link preview is generated. Can disable the preview, choose
                which URL it previews, prefer a larger or smaller image, and put the preview above
                the text instead of below it.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the sent text message is returned.

        Example:
            .. code-block:: python

                # Simple example
                await app.send_message("me", "Message sent with **Pyrogram**!")

                # Disable web page previews
                await app.send_message(
                    "me",
                    "https://docs.pyrogram.org",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )

                # Reply to a message using its id
                await app.send_message(
                    "me",
                    "this is a reply",
                    reply_parameters=ReplyParameters(message_id=123),
                )

            .. code-block:: python

                # For bots only, send messages with keyboards attached

                from pyrogram.types import (
                    ReplyKeyboardMarkup,
                    InlineKeyboardMarkup,
                    InlineKeyboardButton,
                )

                # Send a normal keyboard
                await app.send_message(
                    chat_id, "Look at that button!", reply_markup=ReplyKeyboardMarkup([["Nice!"]])
                )

                # Send an inline keyboard
                await app.send_message(
                    chat_id,
                    "These are inline buttons",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Data", callback_data="callback_data")],
                        [InlineKeyboardButton("Docs", url="https://docs.pyrogram.org")],
                    ]),
                )
        """

        message, entities = (
            await utils.parse_text_entities(self, text, parse_mode, entities)
        ).values()

        reply_to = await utils.get_reply_to(self, reply_parameters, message_thread_id)

        # A preview whose URL or size is specified cannot be expressed by sendMessage's
        # no_webpage flag: it needs an explicit InputMediaWebPage, which means sendMedia.
        wants_explicit_preview = link_preview_options is not None and (
            link_preview_options.url is not None
            or link_preview_options.prefer_large_media is not None
            or link_preview_options.prefer_small_media is not None
        )

        common = {
            "peer": await self.resolve_peer(chat_id),
            "silent": disable_notification or None,
            "reply_to": reply_to,
            "random_id": self.rnd_id(),
            "schedule_date": utils.datetime_to_timestamp(schedule_date),
            "reply_markup": await reply_markup.write(self) if reply_markup else None,
            "message": message,
            "entities": entities,
            "noforwards": protect_content,
            "invert_media": (
                link_preview_options.show_above_text if link_preview_options else None
            ),
        }

        if wants_explicit_preview:
            rpc = raw.functions.messages.SendMedia(
                media=raw.types.InputMediaWebPage(
                    url=link_preview_options.url,
                    force_large_media=link_preview_options.prefer_large_media,
                    force_small_media=link_preview_options.prefer_small_media,
                    # The preview is a bonus, not the point of the message: without this the
                    # send fails outright when Telegram cannot build one.
                    optional=True,
                ),
                **common,
            )
        else:
            rpc = raw.functions.messages.SendMessage(
                no_webpage=(link_preview_options.is_disabled if link_preview_options else None)
                or None,
                **common,
            )

        r = await self.invoke(rpc)

        if isinstance(r, raw.types.UpdateShortSentMessage):
            peer = await self.resolve_peer(chat_id)

            peer_id = peer.user_id if isinstance(peer, raw.types.InputPeerUser) else -peer.chat_id

            return types.Message(
                id=r.id,
                chat=types.Chat(id=peer_id, type=enums.ChatType.PRIVATE, client=self),
                text=message,
                date=utils.timestamp_to_datetime(r.date),
                outgoing=r.out,
                reply_markup=reply_markup,
                entities=[types.MessageEntity._parse(None, entity, {}) for entity in entities]
                if entities
                else None,
                client=self,
            )

        for i in r.updates:
            if isinstance(
                i,
                (
                    raw.types.UpdateNewMessage,
                    raw.types.UpdateNewChannelMessage,
                    raw.types.UpdateNewScheduledMessage,
                ),
            ):
                return await types.Message._parse(
                    client=self,
                    message=i.message,
                    users={i.id: i for i in r.users},
                    chats={i.id: i for i in r.chats},
                    is_scheduled=isinstance(i, raw.types.UpdateNewScheduledMessage),
                )
        return None
