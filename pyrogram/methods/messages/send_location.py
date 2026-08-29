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
from pyrogram import raw, types, utils

if TYPE_CHECKING:
    from datetime import datetime


class SendLocation:
    async def send_location(
        self: pyrogram.Client,
        chat_id: int | str,
        latitude: float,
        longitude: float,
        *,
        message_thread_id: int | None = None,
        horizontal_accuracy: int | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        protect_content: bool | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        direct_messages_topic_id: int | None = None,
        effect_id: int | None = None,
        repeat_period: int | None = None,
        allow_paid_broadcast: bool | None = None,
        paid_message_star_count: int | None = None,
        suggested_post_parameters: types.SuggestedPostParameters | None = None,
        business_connection_id: str | None = None,
        receiver_user_id: int | str | None = None,
        callback_query_id: str | None = None,
    ) -> types.Message:
        """Send points on the map.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            latitude (``float``):
                Latitude of the location.

            longitude (``float``):
                Longitude of the location.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                for forum supergroups only.

            horizontal_accuracy (``int``, *optional*):
                The estimated horizontal accuracy of the location, in meters.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            direct_messages_topic_id (``int``, *optional*):
                Unique identifier of the direct messages topic to send the message to.

            effect_id (``int``, *optional*):
                Unique identifier of the message effect to be added to the message.

            repeat_period (``int``, *optional*):
                Period in seconds for which a scheduled message should be repeated.

            allow_paid_broadcast (``bool``, *optional*):
                Pass True to bypass the broadcast rate limit for a fee, charged to the bot's Telegram Star balance.

            paid_message_star_count (``int``, *optional*):
                Number of Telegram Stars the sender is willing to pay to send the message, when the chat charges for incoming messages.

            suggested_post_parameters (:obj:`~pyrogram.types.SuggestedPostParameters`, *optional*):
                Parameters of the suggested post this message proposes. Channel direct messages only.

            business_connection_id (``str``, *optional*):
                Unique identifier of the business connection to send the message on behalf of.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            receiver_user_id (``int`` | ``str``, *optional*):
                Send the message as an ephemeral message, visible only to this user.
                Bots only, and only in answer to a callback query.

            callback_query_id (``str``, *optional*):
                Identifier of the callback query the ephemeral message answers.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the sent location message is returned.

        Example:
            .. code-block:: python

                app.send_location("me", latitude, longitude)
        """

        reply_to = await utils.get_reply_to(
            self, reply_parameters, message_thread_id, direct_messages_topic_id
        )

        r = await self.invoke(
            await utils.ephemeral_or(
                self,
                raw.functions.messages.SendMedia(
                    peer=await self.resolve_peer(chat_id),
                    media=raw.types.InputMediaGeoPoint(
                        geo_point=raw.types.InputGeoPoint(
                            lat=latitude, long=longitude, accuracy_radius=horizontal_accuracy
                        )
                    ),
                    message="",
                    silent=disable_notification or None,
                    reply_to=reply_to,
                    random_id=self.rnd_id(),
                    suggested_post=suggested_post_parameters.write()
                    if suggested_post_parameters
                    else None,
                    allow_paid_stars=paid_message_star_count,
                    allow_paid_floodskip=allow_paid_broadcast,
                    schedule_repeat_period=repeat_period,
                    effect=effect_id,
                    schedule_date=utils.datetime_to_timestamp(schedule_date),
                    noforwards=protect_content,
                    reply_markup=await reply_markup.write(self) if reply_markup else None,
                ),
                receiver_user_id,
                callback_query_id,
            ),
            business_connection_id=business_connection_id,
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
