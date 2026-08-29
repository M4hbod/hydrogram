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

import re
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

import pyrogram
from pyrogram import StopTransmission, enums, raw, types, utils
from pyrogram.errors import FilePartMissing
from pyrogram.file_id import FileType

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime


class SendVoice:
    async def send_voice(
        self: pyrogram.Client,
        chat_id: int | str,
        voice: str | BinaryIO,
        caption: str = "",
        *,
        message_thread_id: int | None = None,
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        duration: int = 0,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        protect_content: bool | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
        direct_messages_topic_id: int | None = None,
        effect_id: int | None = None,
        repeat_period: int | None = None,
        allow_paid_broadcast: bool | None = None,
        paid_message_star_count: int | None = None,
        suggested_post_parameters: types.SuggestedPostParameters | None = None,
        business_connection_id: str | None = None,
        receiver_user_id: int | str | None = None,
        callback_query_id: str | None = None,
    ) -> types.Message | None:
        """Send audio files.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            voice (``str`` | ``BinaryIO``):
                Audio file to send.
                Pass a file_id as string to send an audio that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get an audio from the Internet,
                pass a file path as string to upload a new audio that exists on your local machine, or
                pass a binary file-like object with its attribute ".name" set for in-memory uploads.

            caption (``str``, *optional*):
                Voice message caption, 0-1024 characters.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                for forum supergroups only.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            duration (``int``, *optional*):
                Duration of the voice message in seconds.

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

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

            receiver_user_id (``int`` | ``str``, *optional*):
                Send the message as an ephemeral message, visible only to this user.
                Bots only, and only in answer to a callback query.

            callback_query_id (``str``, *optional*):
                Identifier of the callback query the ephemeral message answers.

        Returns:
            :obj:`~pyrogram.types.Message` | ``None``: On success, the sent voice message is returned, otherwise, in
            case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned.

        Example:
            .. code-block:: python

                # Send voice note by uploading from local file
                await app.send_voice("me", "voice.ogg")

                # Add caption to the voice note
                await app.send_voice("me", "voice.ogg", caption="voice caption")

                # Set voice note duration
                await app.send_voice("me", "voice.ogg", duration=20)
        """
        file = None

        try:
            if isinstance(voice, str):
                if Path(voice).is_file():
                    file = await self.save_file(
                        voice, progress=progress, progress_args=progress_args
                    )
                    media = raw.types.InputMediaUploadedDocument(
                        mime_type=self.guess_mime_type(voice) or "audio/mpeg",
                        file=file,
                        attributes=[
                            raw.types.DocumentAttributeAudio(voice=True, duration=duration)
                        ],
                    )
                elif re.match(r"^https?://", voice):
                    media = raw.types.InputMediaDocumentExternal(url=voice)
                else:
                    media = utils.get_input_media_from_file_id(voice, FileType.VOICE)
            else:
                file = await self.save_file(voice, progress=progress, progress_args=progress_args)
                media = raw.types.InputMediaUploadedDocument(
                    mime_type=self.guess_mime_type(voice.name) or "audio/mpeg",
                    file=file,
                    attributes=[raw.types.DocumentAttributeAudio(voice=True, duration=duration)],
                )

            reply_to = await utils.get_reply_to(
                self, reply_parameters, message_thread_id, direct_messages_topic_id
            )

            while True:
                try:
                    r = await self.invoke(
                        await utils.ephemeral_or(
                            self,
                            raw.functions.messages.SendMedia(
                                peer=await self.resolve_peer(chat_id),
                                media=media,
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
                                reply_markup=await reply_markup.write(self)
                                if reply_markup
                                else None,
                                **await utils.parse_text_entities(
                                    self, caption, parse_mode, caption_entities
                                ),
                            ),
                            receiver_user_id,
                            callback_query_id,
                        ),
                        business_connection_id=business_connection_id,
                    )
                except FilePartMissing as e:
                    await self.save_file(voice, file_id=file.id, file_part=e.value)
                else:
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
        except StopTransmission:
            return None
