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
from pyrogram import raw, types, utils


class SendGame:
    async def send_game(
        self: pyrogram.Client,
        chat_id: int | str,
        game_short_name: str,
        *,
        message_thread_id: int | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        protect_content: bool | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        effect_id: int | None = None,
        allow_paid_broadcast: bool | None = None,
        business_connection_id: str | None = None,
        direct_messages_topic_id: int | None = None,
    ) -> types.Message:
        """Send a game.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            game_short_name (``str``):
                Short name of the game, serves as the unique identifier for the game. Set up your games via Botfather.

            message_thread_id (``int``, *optional*):
                Unique identifier of a message thread to which the message belongs.
                for supergroups only

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            effect_id (``int``, *optional*):
                Unique identifier of the message effect to be added to the message.

            allow_paid_broadcast (``bool``, *optional*):
                Pass True to bypass the broadcast rate limit for a fee, charged to the bot's Telegram Star balance.

            business_connection_id (``str``, *optional*):
                Unique identifier of the business connection to send the message on behalf of.

            direct_messages_topic_id (``int``, *optional*):
                Unique identifier of the direct messages topic to send the message to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An object for an inline keyboard. If empty, one ‘Play game_title’ button will be shown automatically.
                If not empty, the first button must launch the game.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the sent game message is returned.

        Example:
            .. code-block:: python

                await app.send_game(chat_id, "gamename")
        """
        reply_to = await utils.get_reply_to(
            self, reply_parameters, message_thread_id, direct_messages_topic_id
        )

        r = await self.invoke(
            raw.functions.messages.SendMedia(
                peer=await self.resolve_peer(chat_id),
                media=raw.types.InputMediaGame(
                    id=raw.types.InputGameShortName(
                        bot_id=raw.types.InputUserSelf(), short_name=game_short_name
                    ),
                ),
                message="",
                silent=disable_notification or None,
                reply_to=reply_to,
                random_id=self.rnd_id(),
                allow_paid_floodskip=allow_paid_broadcast,
                effect=effect_id,
                noforwards=protect_content,
                reply_markup=await reply_markup.write(self) if reply_markup else None,
            ),
            business_connection_id=business_connection_id,
        )

        for i in r.updates:
            if isinstance(i, (raw.types.UpdateNewMessage, raw.types.UpdateNewChannelMessage)):
                return await types.Message._parse(
                    client=self,
                    message=i.message,
                    users={i.id: i for i in r.users},
                    chats={i.id: i for i in r.chats},
                )
        return None
