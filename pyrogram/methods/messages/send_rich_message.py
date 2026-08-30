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

import logging

import pyrogram
from pyrogram import enums, raw, types, utils

log = logging.getLogger(__name__)


class SendRichMessage:
    async def send_rich_message(
        self: pyrogram.Client,
        chat_id: int | str,
        rich_message: types.InputRichMessage,
        disable_notification: bool | None = None,
        message_thread_id: int | None = None,
        direct_messages_topic_id: int | None = None,
        receiver_user_id: int | str | None = None,
        callback_query_id: str | None = None,
        effect_id: int | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        protect_content: bool | None = None,
        allow_paid_broadcast: bool | None = None,
        suggested_post_parameters: types.SuggestedPostParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply
        | None = None,
    ) -> types.Message | None:
        """Send text messages.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            rich_message (:obj:`~pyrogram.types.InputRichMessage`):
                The message to be sent.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                For forums only.

            direct_messages_topic_id (``int``, *optional*):
                Unique identifier of the topic in a channel direct messages chat administered by the current user.
                For direct chats only.only.

            receiver_user_id (``int`` | ``str``, *optional*):
                For outgoing ephemeral messages, unique identifier (int) or username (str) of the user who will receive the message.
                For group and supergroup chats only.
                It is not guaranteed that the user will receive the message, especially if they are offline.
                See `ephemeral message sending <https://core.telegram.org/bots/api#ephemeral-messages-and-commands>`__ for more details.

            callback_query_id (``str``, *optional*):
                For outgoing ephemeral messages, identifier of the callback query which triggered the message if any.

            effect_id (``int``, *optional*):
                Unique identifier of the message effect.
                For private chats only.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Describes reply parameters for the message that is being sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            allow_paid_broadcast (``bool``, *optional*):
                If True, you will be allowed to send up to 1000 messages per second.
                Ignoring broadcasting limits for a fee of 0.1 Telegram Stars per message.
                The relevant Stars will be withdrawn from the bot's balance.
                For bots only.

            suggested_post_parameters (:obj:`~pyrogram.types.SuggestedPostParameters`, *optional*):
                Information about the suggested post.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            :obj:`~pyrogram.types.Message` | ``None``: On success, the sent text message is returned,
            otherwise, in case the server answered with no message, None is returned.

        Example:
            .. code-block:: python

                from pyrogram import types

                await app.send_rich_message(
                    chat_id=chat_id,
                    rich_message=types.InputRichMessage(html="Hello <b>World</b>"),
                    reply_markup=types.InlineKeyboardMarkup([
                        [types.InlineKeyboardButton("Data", callback_data="callback_data")],
                        [types.InlineKeyboardButton("Docs", url="https://docs.pyrogram.org")],
                    ]),
                )

            Structured blocks, which is what HTML and Markdown cannot express --
            tables, checkboxes, collapsible sections, anchors and headings. The
            classes are the same ones reading a rich message gives back, so a
            message can be parsed, edited and sent again:

            .. code-block:: python

                from pyrogram import types

                await app.send_rich_message(
                    chat_id=chat_id,
                    rich_message=types.InputRichMessage(
                        blocks=[
                            types.RichBlockSectionHeading(text="Now Playing", size=2),
                            types.RichBlockParagraph(
                                text=[
                                    "by ",
                                    types.RichTextBold(text="Artemis"),
                                ]
                            ),
                            types.RichBlockTable(
                                cells=[
                                    [
                                        types.RichBlockTableCell(text="Track", is_header=True),
                                        types.RichBlockTableCell(
                                            text="Length", is_header=True, align="right"
                                        ),
                                    ],
                                    [
                                        types.RichBlockTableCell(text="Intro"),
                                        types.RichBlockTableCell(text="1:02", align="right"),
                                    ],
                                ],
                                is_bordered=True,
                            ),
                            # A list whose items carry checkboxes is a checklist.
                            types.RichBlockList(
                                items=[
                                    types.RichBlockListItem(
                                        label="•",
                                        blocks=[types.RichBlockParagraph(text="Downloaded")],
                                        has_checkbox=True,
                                        is_checked=True,
                                    ),
                                    types.RichBlockListItem(
                                        label="•",
                                        blocks=[types.RichBlockParagraph(text="Tagged")],
                                        has_checkbox=True,
                                    ),
                                ]
                            ),
                            types.RichBlockDetails(
                                summary="Metadata",
                                blocks=[types.RichBlockParagraph(text="320kbps, FLAC source")],
                            ),
                        ]
                    ),
                )
        """
        if receiver_user_id:
            rpc = raw.functions.ephemeral.SendMessage(
                peer=await self.resolve_peer(chat_id),
                receiver_id=await self.resolve_peer(receiver_user_id),
                query_id=int(callback_query_id) if callback_query_id is not None else None,
                reply_to=await utils.get_reply_to(
                    self, reply_parameters, message_thread_id, direct_messages_topic_id
                ),
                random_id=self.rnd_id(),
                reply_markup=await reply_markup.write(self) if reply_markup else None,
                message="",
                rich_message=rich_message.write(),
            )
        else:
            rpc = raw.functions.messages.SendMessage(
                peer=await self.resolve_peer(chat_id),
                silent=disable_notification or None,
                reply_to=await utils.get_reply_to(
                    self, reply_parameters, message_thread_id, direct_messages_topic_id
                ),
                random_id=self.rnd_id(),
                allow_paid_floodskip=allow_paid_broadcast,
                suggested_post=suggested_post_parameters.write()
                if suggested_post_parameters
                else None,
                reply_markup=await reply_markup.write(self) if reply_markup else None,
                message="",
                noforwards=protect_content,
                rich_message=rich_message.write(),
                effect=effect_id,
            )

        r = await self.invoke(rpc)

        if isinstance(r, raw.types.UpdateShortSentMessage):
            peer = await self.resolve_peer(chat_id)

            peer_id = peer.user_id if isinstance(peer, raw.types.InputPeerUser) else -peer.chat_id

            return types.Message(
                id=r.id,
                chat=types.Chat(id=peer_id, type=enums.ChatType.PRIVATE, client=self),
                date=utils.timestamp_to_datetime(r.date),
                outgoing=r.out,
                reply_markup=reply_markup,
                client=self,
            )

        # Both messages.sendMessage and ephemeral.sendMessage return Updates, which
        # has no `messages` attribute for parse_messages to read. A user sending to
        # their own private chat gets the UpdateShortSentMessage shortcut above; a
        # bot gets the full Updates, so this is the branch bots always take.
        return next(iter(await utils.parse_messages_from_updates(client=self, updates=r)), None)
